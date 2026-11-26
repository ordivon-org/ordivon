//! Native, bounded evidence carrier reads. The exact same opened file
//! handle supplies size and bytes; paths are not reopened after validation.
//! Content identity and physical authority remain separate higher layers.
use crate::universal::{open_directory_nofollow, open_regular_file_beneath};
use serde_json::Value;
use std::{
    io::{self, Read},
    path::Path,
};

const MAX_EVIDENCE_BYTES: u64 = 2 * 1024 * 1024;
const MAX_OUTPUT_BYTES: u64 = 4 * 1024 * 1024;

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

fn read_file(path: &Path, ceiling: u64) -> io::Result<Option<Vec<u8>>> {
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

pub(super) fn read_raw_bounded(path: &Path) -> Result<Vec<u8>, String> {
    read_file(path, MAX_OUTPUT_BYTES)
        .map_err(|e| format!("output read: {e}"))?
        .ok_or_else(|| "output file missing".into())
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
