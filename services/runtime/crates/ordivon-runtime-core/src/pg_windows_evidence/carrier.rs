//! Native, bounded evidence carrier reads. The exact same opened file
//! handle supplies size and bytes; paths are not reopened after validation.
//! Content identity and physical authority remain separate higher layers.
use crate::universal::{open_directory_nofollow, open_regular_file_beneath};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{
    fs::File,
    io::{self, Read},
    path::Path,
};

const MAX_EVIDENCE_BYTES: u64 = 2 * 1024 * 1024;
const MAX_REQUEST_BYTES: u64 = 4 * 1024 * 1024;

fn bounded_bytes(reader: impl Read, expected: u64, ceiling: u64) -> io::Result<Vec<u8>> {
    if expected > ceiling {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "carrier exceeds byte ceiling",
        ));
    }
    let mut bytes = Vec::new();
    reader.take(ceiling + 1).read_to_end(&mut bytes)?;
    if bytes.len() as u64 != expected {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "carrier length changed or exceeds byte ceiling",
        ));
    }
    Ok(bytes)
}

fn open_file(path: &Path) -> io::Result<Option<File>> {
    let dir = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "carrier has no directory"))?;
    let name = path
        .file_name()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "carrier has no file name"))?;
    // Open the native directory without following its final link. Missing
    // root is not a missing receipt inside an already qualified bundle.
    let root = open_directory_nofollow(dir)?;
    let file = match open_regular_file_beneath(&root, Path::new(name), true) {
        Ok(file) => file,
        Err(e) if e.kind() == io::ErrorKind::NotFound => return Ok(None),
        Err(e) => return Err(e),
    };
    Ok(Some(file))
}

fn read_file(path: &Path, ceiling: u64) -> io::Result<Option<Vec<u8>>> {
    let Some(file) = open_file(path)? else {
        return Ok(None);
    };
    let expected = file.metadata()?.len();
    let bytes = bounded_bytes(&file, expected, ceiling)?;
    if file.metadata()?.len() != expected {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "carrier length changed during read",
        ));
    }
    Ok(Some(bytes))
}

pub(super) fn read_value(path: &Path) -> Result<Option<(Value, Vec<u8>)>, String> {
    let Some(bytes) =
        read_file(path, MAX_EVIDENCE_BYTES).map_err(|e| format!("evidence read: {e}"))?
    else {
        return Ok(None);
    };
    let value =
        serde_json::from_slice::<Value>(&bytes).map_err(|e| format!("evidence JSON: {e}"))?;
    if !value.is_object() {
        return Err("evidence must be a JSON object".into());
    }
    Ok(Some((value, bytes)))
}

pub(super) fn read_request_bytes(path: &Path) -> Result<Vec<u8>, String> {
    read_file(path, MAX_REQUEST_BYTES)
        .map_err(|e| format!("request read: {e}"))?
        .ok_or_else(|| "request file missing".into())
}

/// Verify the same native opened handle against the admitted per-stream
/// ceiling and exact receipt length/digest. Stream bytes, never allocate a
/// vector sized by mutable file metadata or the requested output budget.
pub(super) fn verify_output(
    path: &Path,
    declared_length: u64,
    declared_digest: &str,
    admitted_limit: u64,
) -> Result<(), String> {
    if admitted_limit == 0 || admitted_limit > i64::MAX as u64 || declared_length > admitted_limit {
        return Err("output exceeds frozen PG stream limit".into());
    }
    let file = open_file(path)
        .map_err(|e| format!("output open: {e}"))?
        .ok_or("output file missing")?;
    let metadata_length = || file.metadata().map(|m| m.len()).map_err(|e| e.to_string());
    if metadata_length()? != declared_length {
        return Err("output length disagrees with native receipt".into());
    }
    let mut reader = (&file).take(declared_length + 1);
    let mut hash = Sha256::new();
    let mut count = 0_u64;
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let n = match reader.read(&mut buffer) {
            Err(e) if e.kind() == io::ErrorKind::Interrupted => continue,
            result => result.map_err(|e| format!("output read: {e}"))?,
        };
        if n == 0 {
            break;
        }
        count += n as u64;
        if count > declared_length {
            return Err("output grew beyond native receipt".into());
        }
        hash.update(&buffer[..n]);
    }
    if count != declared_length
        || metadata_length()? != declared_length
        || format!("sha256:{}", hex::encode(hash.finalize())) != declared_digest
    {
        return Err("output bytes disagree with native receipt".into());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn growth_is_bounded_even_when_initial_metadata_is_small() {
        // Infinite reader is the adversarial growth case, not a giant allocation.
        let mut source = io::repeat(7);
        let mut consumed = 0;
        struct Count<'a, R>(&'a mut R, &'a mut usize);
        impl<R: Read> Read for Count<'_, R> {
            fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
                let n = self.0.read(buf)?;
                *self.1 += n;
                Ok(n)
            }
        }
        assert!(bounded_bytes(Count(&mut source, &mut consumed), 1, 16).is_err());
        assert_eq!(consumed, 17);
        assert_eq!(bounded_bytes(&b"abcd"[..], 4, 4).unwrap(), b"abcd");
        assert!(bounded_bytes(&b"abcd"[..], 5, 5).is_err());
        assert!(bounded_bytes(&b"abcd"[..], 4, 3).is_err());
    }

    #[test]
    fn actual_file_missing_directory_and_size_are_distinct() {
        let dir = tempfile::TempDir::new().unwrap();
        let path = dir.path().join("receipt.json");
        assert_eq!(read_file(&path, 4).unwrap(), None);
        assert!(read_file(&dir.path().join("missing").join("receipt.json"), 4).is_err());
        std::fs::write(&path, b"1234").unwrap();
        assert_eq!(read_file(&path, 4).unwrap().unwrap(), b"1234");
        assert!(read_file(&path, 3).is_err());
        std::fs::remove_file(&path).unwrap();
        std::fs::create_dir(&path).unwrap();
        assert!(read_file(&path, 4).is_err());
    }
}
