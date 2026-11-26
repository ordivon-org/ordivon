//! Bounded ordered verification of retained bytes, not an execution/domain verdict.
use crate::{
    artifact_chunk::{self, Window},
    artifact_descriptor::{self, Descriptor},
    logic::parse_execution_ref,
};
use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};

const MAX_BYTES: u64 = 64 * 1024 * 1024;
const MAX_WINDOWS: u64 = 4096;

#[derive(Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "standing", rename_all = "snake_case")]
pub(crate) enum Standing {
    Incomplete { received_bytes: u64, windows: u64 },
    Verified { received_bytes: u64, windows: u64 },
    Rejected { reason: &'static str },
}

enum State {
    Receiving(Sha256),
    Verified,
    Rejected(&'static str),
}

pub(crate) struct Stream<'a> {
    reference: &'a str,
    descriptor: Descriptor,
    state: State,
    next: u64,
    windows: u64,
    max_windows: u64,
}

impl<'a> Stream<'a> {
    pub(crate) fn new(
        reference: &'a str,
        descriptor: &Value,
        max_bytes: u64,
        max_windows: u64,
    ) -> Result<Self, &'static str> {
        parse_execution_ref(reference).ok_or("invalid_operation_ref")?;
        let d = artifact_descriptor::decode(descriptor).ok_or("unqualified_descriptor")?;
        if max_bytes > MAX_BYTES
            || !(1..=MAX_WINDOWS).contains(&max_windows)
            || d.retained_bytes() > max_bytes
        {
            return Err("stream_budget");
        }
        Ok(Self {
            reference,
            descriptor: d,
            state: State::Receiving(Sha256::new()),
            next: 0,
            windows: 0,
            max_windows,
        })
    }
    pub(crate) fn next(&self) -> u64 {
        self.next
    }
    pub(crate) fn artifact_id(&self) -> &str {
        self.descriptor.artifact_id()
    }
    pub(crate) fn remaining(&self) -> u64 {
        self.descriptor.retained_bytes() - self.next
    }
    pub(crate) fn can_read(&self) -> bool {
        matches!(self.state, State::Receiving(_)) && self.windows < self.max_windows
    }
    fn reject(&mut self, reason: &'static str) {
        self.state = State::Rejected(reason);
    }
    pub(crate) fn accept(&mut self, request: &Value, response: &Value) {
        if matches!(self.state, State::Rejected(_)) {
            return;
        }
        if matches!(self.state, State::Verified) {
            self.reject("window_after_eof");
            return;
        }
        if self.windows >= self.max_windows {
            self.reject("window_budget");
            return;
        }
        match artifact_chunk::qualify_bound(self.reference, &self.descriptor, request, response) {
            Window::Unobserved { reason } => self.reject(reason),
            Window::Qualified {
                offset,
                next_offset,
                eof,
                content,
                ..
            } => {
                if offset != self.next {
                    self.reject("noncontiguous_window");
                    return;
                }
                let State::Receiving(hash) = &mut self.state else {
                    unreachable!()
                };
                hash.update(content.as_bytes());
                self.next = next_offset;
                self.windows += 1;
                if eof {
                    let actual = hash.clone().finalize();
                    let hex: String = actual.iter().map(|b| format!("{b:02x}")).collect();
                    if self.descriptor.digest().strip_prefix("sha256:") == Some(hex.as_str()) {
                        self.state = State::Verified;
                    } else {
                        self.reject("stream_digest_mismatch");
                    }
                }
            }
        }
    }
    pub(crate) fn standing(&self) -> Standing {
        match self.state {
            State::Receiving(_) => Standing::Incomplete {
                received_bytes: self.next,
                windows: self.windows,
            },
            State::Verified => Standing::Verified {
                received_bytes: self.next,
                windows: self.windows,
            },
            State::Rejected(reason) => Standing::Rejected { reason },
        }
    }
}

pub(crate) fn project(input: &Value) -> Standing {
    let Some(max_bytes) = input["maxTotalBytes"].as_u64() else {
        return Standing::Rejected {
            reason: "stream_budget",
        };
    };
    let Some(max_windows) = input["maxWindows"].as_u64() else {
        return Standing::Rejected {
            reason: "stream_budget",
        };
    };
    let mut stream = match Stream::new(
        input["operationRef"].as_str().unwrap_or_default(),
        &input["descriptor"],
        max_bytes,
        max_windows,
    ) {
        Ok(s) => s,
        Err(reason) => return Standing::Rejected { reason },
    };
    let Some(windows) = input["windows"].as_array() else {
        return Standing::Rejected {
            reason: "invalid_windows",
        };
    };
    for w in windows {
        stream.accept(&w["request"], &w["response"]);
        if matches!(stream.standing(), Standing::Rejected { .. }) {
            break;
        }
    }
    stream.standing()
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use serde_json::json;
    fn fixture(parts: &[String]) -> Value {
        let all = parts.concat();
        let digest = format!(
            "sha256:{}",
            Sha256::digest(all.as_bytes())
                .iter()
                .map(|b| format!("{b:02x}"))
                .collect::<String>()
        );
        let mut offset = 0;
        let windows:Vec<_>=parts.iter().map(|part|{
            let end=offset+part.len();
            let w=json!({"request":{"artifactId":"opaque","offset":offset,"maxBytes":part.len().max(1)},
                "response":{"jobId":"job-a","artifactId":"opaque","offset":offset,"nextOffset":end,"eof":end==all.len(),"digest":digest,"content":part}});
            offset=end;w
        }).collect();
        json!({"operationRef":"ordivon-exec:v1:runtime.linux:job-a","descriptor":{"artifactId":"opaque","attemptId":"another","kind":"stdout","digest":digest,"retainedBytes":all.len(),"truncated":false},"maxTotalBytes":all.len(),"maxWindows":4096,"windows":windows})
    }
    #[test]
    fn complete_requires_eof_and_sticky_rejection() {
        let v = fixture(&["中".into(), "🙂".into()]);
        assert_eq!(
            project(&v),
            Standing::Verified {
                received_bytes: 7,
                windows: 2
            }
        );
        let mut incomplete = v.clone();
        incomplete["windows"].as_array_mut().unwrap().pop();
        assert_eq!(
            project(&incomplete),
            Standing::Incomplete {
                received_bytes: 3,
                windows: 1
            }
        );
        let mut replay = v.clone();
        replay["windows"]
            .as_array_mut()
            .unwrap()
            .push(v["windows"][0].clone());
        assert_eq!(
            project(&replay),
            Standing::Rejected {
                reason: "window_after_eof"
            }
        );
        let mut corruption = v;
        corruption["windows"][0]["response"]["content"] = json!("abc");
        assert_eq!(
            project(&corruption),
            Standing::Rejected {
                reason: "stream_digest_mismatch"
            }
        );
    }
    proptest! {
        #![proptest_config(ProptestConfig::with_cases(512))]
        #[test]
        fn partition_invariance_and_mutations(parts in prop::collection::vec(".{1,24}",2..12), which in 0usize..11){
            let v=fixture(&parts);
            let n=parts.iter().map(String::len).sum::<usize>() as u64;
            prop_assert_eq!(project(&v),Standing::Verified{received_bytes:n,windows:parts.len() as u64});
            let mut bad=v.clone();
            let pos=which%parts.len();
            bad["windows"][pos]["response"]["content"]=json!(if parts[pos].bytes().all(|b|b==b'x'){"y".repeat(parts[pos].len())}else{"x".repeat(parts[pos].len())});
            let rejected=matches!(project(&bad),Standing::Rejected{..});
            prop_assert!(rejected,"same-length mutation must fail");
            let mut prefix=v;prefix["windows"].as_array_mut().unwrap().truncate(pos);
            let expected=parts[..pos].iter().map(String::len).sum::<usize>() as u64;
            prop_assert_eq!(project(&prefix),Standing::Incomplete{received_bytes:expected,windows:pos as u64});
        }
    }
}
