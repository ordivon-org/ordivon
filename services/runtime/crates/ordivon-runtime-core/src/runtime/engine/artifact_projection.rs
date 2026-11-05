// Artifact byte projection is a separately replaceable in-process seam.
// Preserve one open handle across digest verification and returned bytes.
impl Runtime {
    #[cfg(unix)]
    fn open_artifact_beneath_bundle(bundle: &Path, relative: &Path) -> RuntimeResult<File> {
        // The pinned directory FD plus openat2's RESOLVE_BENEATH and
        // RESOLVE_NO_SYMLINKS exclude a mutable parent symlink between
        // pathname qualification and Artifact byte projection.
        let root = open_directory_nofollow(bundle).map_err(|_| {
            RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Attempt bundle is unavailable as a no-follow directory",
                Some("artifactId"),
                false,
            )
        })?;
        open_regular_file_beneath(&root, relative, true).map_err(|_| {
            RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Artifact is unavailable as a regular file beneath Attempt bundle",
                Some("artifactId"),
                false,
            )
        })
    }

    fn verified_artifact_file(
        &self,
        job_id: &str,
        artifact_id: &str,
    ) -> RuntimeResult<(RuntimeArtifactRecord, File)> {
        let artifact = self.registry.get_artifact(job_id, artifact_id)?;
        let attempt = self.registry.get_attempt(&artifact.attempt_id)?;
        let bundle = canonical_directory(Path::new(&attempt.bundle_path), "bundlePath")
            .map_err(map_universal_error)?;

        #[cfg(unix)]
        let file = Self::open_artifact_beneath_bundle(
            &bundle, Path::new(&artifact.relative_path),
        )?;

        // Windows has no admitted openat2 equivalent. Preserve the existing
        // checked-beneath-path behavior but pin one file handle for identity
        // qualification and projection; Windows parent-path race proof remains
        // UNKNOWN and must not be promoted from this Linux-specific gate.
        #[cfg(not(unix))]
        let file = {
            let path = bundle.join(&artifact.relative_path);
            let metadata = fs::symlink_metadata(&path)
                .map_err(|error| io_error("inspect Artifact", error))?;
            if metadata.file_type().is_symlink() || !metadata.is_file() {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ArtifactIdentityConflict,
                    "Artifact path is not a regular non-symlink file",
                    Some("artifactId"),
                    false,
                ));
            }
            let canonical = fs::canonicalize(&path)
                .map_err(|error| io_error("canonicalize Artifact", error))?;
            if !canonical.starts_with(&bundle) {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ArtifactIdentityConflict,
                    "Artifact escaped Attempt bundle",
                    Some("artifactId"),
                    false,
                ));
            }
            OpenOptions::new().read(true).open(canonical)
                .map_err(|error| io_error("open Artifact", error))?
        };
        let metadata = file.metadata().map_err(|error| io_error("inspect Artifact", error))?;
        if !metadata.is_file() || metadata.len() != artifact.byte_length {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Artifact file type or byte length changed",
                Some("artifactId"),
                false,
            ));
        }
        Ok((artifact, file))
    }

    // Verify the entire stored Artifact through one open handle, retaining
    // only the requested window. Two opens (hash, then read) cannot establish
    // that the returned bytes belong to the same recorded digest.
    fn read_verified_artifact_window(
        artifact: &RuntimeArtifactRecord,
        mut file: File,
        offset: u64,
        max_bytes: u64,
    ) -> RuntimeResult<Vec<u8>> {
        if !file
            .metadata()
            .map_err(|error| io_error("inspect Artifact", error))?
            .is_file()
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Artifact is not a regular file",
                Some("artifactId"),
                false,
            ));
        }
        let end = offset.saturating_add(max_bytes).min(artifact.byte_length);
        let mut captured = Vec::new();
        let mut hasher = sha2::Sha256::new();
        let mut position = 0u64;
        let mut buffer = [0u8; 65_536];
        loop {
            let count = file
                .read(&mut buffer)
                .map_err(|error| io_error("read Artifact", error))?;
            if count == 0 {
                break;
            }
            let next = position.saturating_add(count as u64);
            if next > artifact.byte_length {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ArtifactIdentityConflict,
                    "Artifact grew beyond recorded byte length",
                    Some("artifactId"),
                    false,
                ));
            }
            hasher.update(&buffer[..count]);
            let left = offset.max(position).min(next);
            let right = end.max(position).min(next);
            if right > left {
                captured.extend_from_slice(&buffer[
                    usize::try_from(left - position).unwrap()
                        ..usize::try_from(right - position).unwrap()
                ]);
            }
            position = next;
        }
        if position != artifact.byte_length
            || format!("sha256:{}", hex::encode(hasher.finalize())) != artifact.digest
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Artifact bytes changed while projecting content",
                Some("artifactId"),
                false,
            ));
        }
        Ok(captured)
    }

    pub fn read_artifact(
        &self,
        request: &ArtifactReadRequest,
    ) -> RuntimeResult<ArtifactReadResult> {
        ArtifactStateContract::validate_read_request(request)?;
        let (artifact, file) =
            self.verified_artifact_file(&request.job_id, &request.artifact_id)?;
        if request.offset > artifact.byte_length {
            return Err(RuntimeError::invalid(
                format!("offset exceeds retained byte length {}", artifact.byte_length),
                "offset",
            ));
        }
        let verified_bytes = Self::read_verified_artifact_window(
            &artifact, file, request.offset, request.max_bytes,
        )?;
        let range = decode_utf8_range_bytes(
            verified_bytes,
            request.offset,
            artifact.byte_length,
            true,
            RangeFields {
                offset: "offset",
                max_bytes: "maxBytes",
            },
        )?;
        Ok(ArtifactReadResult {
            job_id: request.job_id.clone(),
            artifact_id: request.artifact_id.clone(),
            content: range.content,
            offset: request.offset,
            next_offset: range.next_offset,
            eof: range.next_offset >= artifact.byte_length,
            digest: artifact.digest,
        })
    }

    pub fn read_artifact_content(
        &self,
        request: &ArtifactContentRequest,
    ) -> RuntimeResult<ArtifactContentReadResult> {
        ArtifactStateContract::validate_content_request(request)?;
        let (artifact, file) =
            self.verified_artifact_file(&request.job_id, &request.artifact_id)?;
        if artifact.byte_length > request.max_bytes {
            return Err(RuntimeError::new(
                RuntimeErrorCode::InvalidRequest,
                format!(
                    "Artifact requires {} bytes but maxBytes is {}",
                    artifact.byte_length, request.max_bytes
                ),
                Some("maxBytes"),
                false,
            ));
        }
        let bytes = Self::read_verified_artifact_window(
            &artifact, file, 0, artifact.byte_length,
        )?;
        Ok(ArtifactContentReadResult {
            metadata: ArtifactContentMetadata {
                job_id: request.job_id.clone(),
                artifact_id: request.artifact_id.clone(),
                digest: artifact.digest,
                media_type: artifact.media_type,
                byte_length: artifact.byte_length,
                truncated: artifact.truncated,
            },
            bytes,
        })
    }
}

fn artifact_descriptor(
    artifact: RuntimeArtifactRecord,
    result: Option<&RunnerResult>,
) -> ArtifactDescriptor {
    let dropped_bytes = match artifact.kind.as_str() {
        "stdout" => result.map(|result| result.stdout.dropped_bytes),
        "stderr" => result.map(|result| result.stderr.dropped_bytes),
        _ => None,
    };
    ArtifactDescriptor {
        artifact_id: artifact.artifact_id,
        attempt_id: artifact.attempt_id,
        kind: artifact.kind,
        digest: artifact.digest,
        retained_bytes: artifact.byte_length,
        dropped_bytes,
        truncated: artifact.truncated,
    }
}

#[cfg(test)]
mod stage_b0_artifact_descriptor_tests {
    use super::*;

    #[test]
    fn artifact_descriptor_projects_stored_attempt_id_without_parsing_artifact_id() {
        let descriptor = artifact_descriptor(
            RuntimeArtifactRecord {
                artifact_id: "opaque-artifact".to_string(),
                job_id: "job-owner-lineage".to_string(),
                attempt_id: "attempt-owner-lineage".to_string(),
                kind: "result".to_string(),
                relative_path: "result.json".to_string(),
                digest: format!("sha256:{}", "a".repeat(64)),
                media_type: "application/json".to_string(),
                byte_length: 7,
                truncated: false,
                created_at_ms: 1,
            },
            None,
        );

        assert_eq!(descriptor.artifact_id, "opaque-artifact");
        assert_eq!(descriptor.attempt_id, "attempt-owner-lineage");
    }

    #[test]
    fn artifact_snapshot_binds_returned_bytes_to_registered_digest() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-artifact-snapshot-{}-{}",
            std::process::id(),
            SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos()
        ));
        fs::create_dir(&root).unwrap();
        let path = root.join("stdout.log");
        let original = "🙂OK".as_bytes();
        fs::write(&path, original).unwrap();
        let record = RuntimeArtifactRecord {
            artifact_id: "stdout".to_string(),
            job_id: "job-test".to_string(),
            attempt_id: "attempt-test".to_string(),
            kind: "stdout".to_string(),
            relative_path: "stdout.log".to_string(),
            digest: sha256_bytes(original),
            media_type: "text/plain".to_string(),
            byte_length: original.len() as u64,
            truncated: false,
            created_at_ms: 1,
        };

        let verified = Runtime::read_verified_artifact_window(&record, File::open(&path).unwrap(), 0, record.byte_length).unwrap();
        assert_eq!(
            Runtime::read_verified_artifact_window(&record, File::open(&path).unwrap(), 4, 2).unwrap(),
            b"OK"
        );
        // This is the exact historical two-open counterexample: a fresh path
        // read after the digest check admits different same-length bytes.
        fs::write(&path, "123456").unwrap();
        let raw_path_range = read_utf8_range(
            &path,
            0,
            6,
            6,
            true,
            RangeFields { offset: "offset", max_bytes: "maxBytes" },
            "Artifact",
        ).unwrap();
        assert_eq!(raw_path_range.content, "123456");
        assert_ne!(sha256_bytes(raw_path_range.content.as_bytes()), record.digest);

        // A byte snapshot already qualified for this Artifact stays stable
        // even after the mutable pathname is replaced.
        let first = decode_utf8_range_bytes(
            verified[..4].to_vec(), 0, record.byte_length, true,
            RangeFields { offset: "offset", max_bytes: "maxBytes" },
        ).unwrap();
        assert_eq!(first.content, "🙂");
        assert_eq!(first.next_offset, 4);
        let second = decode_utf8_range_bytes(
            verified[4..].to_vec(), 4, record.byte_length, true,
            RangeFields { offset: "offset", max_bytes: "maxBytes" },
        ).unwrap();
        assert_eq!(second.content, "OK");
        assert_eq!(second.next_offset, 6);

        let stale = Runtime::read_verified_artifact_window(&record, File::open(&path).unwrap(), 0, record.byte_length).unwrap_err();
        assert_eq!(stale.code, RuntimeErrorCode::ArtifactIdentityConflict);
        fs::remove_dir_all(&root).unwrap();
    }

    #[test]
    fn artifact_stream_window_crosses_chunk_boundaries_without_full_capture() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-artifact-window-{}-{}",
            std::process::id(),
            SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos()
        ));
        fs::create_dir(&root).unwrap();
        let path = root.join("stdout.log");
        let mut original = vec![b'A'; 65_534];
        original.extend_from_slice("🙂".as_bytes());
        original.extend(std::iter::repeat_n(b'Z', 80_000));
        fs::write(&path, &original).unwrap();
        let record = RuntimeArtifactRecord {
            artifact_id: "stdout".to_string(),
            job_id: "job-window".to_string(),
            attempt_id: "attempt-window".to_string(),
            kind: "stdout".to_string(),
            relative_path: "stdout.log".to_string(),
            digest: sha256_bytes(&original),
            media_type: "text/plain".to_string(),
            byte_length: original.len() as u64,
            truncated: false,
            created_at_ms: 1,
        };
        let emoji = Runtime::read_verified_artifact_window(&record, File::open(&path).unwrap(), 65_534, 4).unwrap();
        assert_eq!(emoji, "🙂".as_bytes());
        let decoded = decode_utf8_range_bytes(
            emoji, 65_534, record.byte_length, true,
            RangeFields { offset: "offset", max_bytes: "maxBytes" },
        ).unwrap();
        assert_eq!(decoded.next_offset, 65_538);
        let continuation = Runtime::read_verified_artifact_window(&record, File::open(&path).unwrap(), 65_535, 4).unwrap();
        assert_eq!(
            decode_utf8_range_bytes(
                continuation, 65_535, record.byte_length, true,
                RangeFields { offset: "offset", max_bytes: "maxBytes" },
            ).unwrap_err().field.as_deref(),
            Some("offset")
        );
        let eof = Runtime::read_verified_artifact_window(
            &record, File::open(&path).unwrap(), record.byte_length, 1,
        ).unwrap();
        assert!(eof.is_empty());

        original[0] = b'X';
        fs::write(&path, &original).unwrap();
        assert_eq!(
            Runtime::read_verified_artifact_window(&record, File::open(&path).unwrap(), 65_534, 4)
                .unwrap_err().code,
            RuntimeErrorCode::ArtifactIdentityConflict
        );
        original.push(b'Q');
        fs::write(&path, &original).unwrap();
        assert_eq!(
            Runtime::read_verified_artifact_window(&record, File::open(&path).unwrap(), 65_534, 4)
                .unwrap_err().code,
            RuntimeErrorCode::ArtifactIdentityConflict
        );
        fs::remove_dir_all(&root).unwrap();
    }

    #[cfg(unix)]
    #[test]
    fn artifact_canonical_parent_swap_never_reads_outside_attempt_bundle() {
        use std::os::unix::fs::symlink;

        let root = std::env::temp_dir().join(format!(
            "ordivon-artifact-parent-swap-{}-{}",
            std::process::id(),
            SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos()
        ));
        let bundle = root.join("attempt-bundle");
        let inner = bundle.join("parent");
        let foreign = root.join("foreign");
        fs::create_dir_all(&inner).unwrap();
        fs::create_dir_all(&foreign).unwrap();
        let data = b"SAFE";
        let path = inner.join("artifact.txt");
        fs::write(&path, data).unwrap();
        fs::write(foreign.join("artifact.txt"), data).unwrap();
        let already_qualified = fs::canonicalize(&path).unwrap();
        assert!(already_qualified.starts_with(fs::canonicalize(&bundle).unwrap()));
        let record = RuntimeArtifactRecord {
            artifact_id: "parent-swap".to_string(),
            job_id: "job-bound".to_string(),
            attempt_id: "attempt-bound".to_string(),
            kind: "stdout".to_string(),
            relative_path: "parent/artifact.txt".to_string(),
            digest: sha256_bytes(data),
            media_type: "text/plain".to_string(),
            byte_length: data.len() as u64,
            truncated: false,
            created_at_ms: 1,
        };
        let qualified_bundle = fs::canonicalize(&bundle).unwrap();
        let original_handle = Runtime::open_artifact_beneath_bundle(
            &qualified_bundle, Path::new(&record.relative_path),
        ).unwrap();
        assert_eq!(
            Runtime::read_verified_artifact_window(&record, original_handle, 0, 4).unwrap(),
            data
        );
        fs::rename(&inner, bundle.join("archived-parent")).unwrap();
        symlink(&foreign, &inner).unwrap();
        let result = Runtime::open_artifact_beneath_bundle(
            &fs::canonicalize(&bundle).unwrap(), Path::new(&record.relative_path),
        ).and_then(|file| Runtime::read_verified_artifact_window(&record, file, 0, 4));
        assert_eq!(
            result.unwrap_err().code,
            RuntimeErrorCode::ArtifactIdentityConflict,
            "prequalified canonical path must not follow a swapped parent symlink"
        );
        fs::remove_dir_all(&root).unwrap();
    }
}
