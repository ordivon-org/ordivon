//! Namespace derivation and reattachment qualification, not authentication.
//! No public caller can construct a trusted ingress identity through this fixture.
use crate::logic::parse_execution_ref;
use crate::owner_resolution::{Resolution, resolve_protected_fixture};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::path::Path;

const DOMAIN: &str = "ordivon.gateway-principal-scoped-execution-request.v1";

/// Exact existing Python namespace encoding, not a general canonical JSON API.
/// Neither normalization nor delimiter concatenation preserves this identity.
pub fn namespace(issuer: &str, principal: &str, capability: &str, request: &str) -> String {
    let canonical = serde_json::to_vec(&[DOMAIN, issuer, principal, capability, request])
        .expect("strings are serializable");
    let digest: String = Sha256::digest(canonical)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect();
    format!("request:gw-principal:{digest}")
}

// Synthetic operator fixture. This struct must NOT become a public MCP input
// schema; production provenance belongs to a verified ingress adapter.
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BindingFixture {
    issuer: String,
    principal: String,
    capability: String,
    request_id: String,
    operation_ref: String,
}

#[derive(Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "standing", rename_all = "snake_case")]
pub enum Binding {
    Matched,
    Unqualified,
}

fn nonblank(s: &str) -> bool {
    // Python str.strip includes U+001C..U+001F in addition to Unicode whitespace.
    !s.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
        .is_empty()
}

impl BindingFixture {
    fn scoped_key(&self) -> Option<String> {
        if !nonblank(&self.issuer)
            || !nonblank(&self.principal)
            || self.capability != "execution.linux"
            || self.request_id.is_empty()
            || !matches!(
                parse_execution_ref(&self.operation_ref),
                Some(("runtime.linux", _))
            )
        {
            return None;
        }
        Some(namespace(
            &self.issuer,
            &self.principal,
            &self.capability,
            &self.request_id,
        ))
    }

    fn qualify(&self, resolution: Resolution) -> Binding {
        match resolution {
            Resolution::Found { operation_ref, .. } if operation_ref == self.operation_ref => {
                Binding::Matched
            }
            _ => Binding::Unqualified,
        }
    }
}

pub async fn qualify_fixture(
    input: BindingFixture,
    endpoint: &str,
    credential: &Path,
    legacy: bool,
) -> Binding {
    let Some(key) = input.scoped_key() else {
        return Binding::Unqualified;
    };
    let resolution = resolve_protected_fixture(endpoint, credential, &key, legacy).await;
    input.qualify(resolution)
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    fn fixture() -> BindingFixture {
        BindingFixture {
            issuer: "issuer".into(),
            principal: "principal".into(),
            capability: "execution.linux".into(),
            request_id: "original".into(),
            operation_ref: "ordivon-exec:v1:runtime.linux:job-a".into(),
        }
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(256))]
        #[test]
        fn namespace_separates_each_coordinate(
            s in prop::collection::vec(any::<char>(),0..32),
            field in 0usize..4,
        ){
            let s:String=s.into_iter().collect();
            let mut tuple=[s.as_str(),s.as_str(),s.as_str(),s.as_str()];
            let baseline=namespace(tuple[0],tuple[1],tuple[2],tuple[3]);
            let changed=format!("{s}!");
            tuple[field]=&changed;
            prop_assert_ne!(baseline,namespace(tuple[0],tuple[1],tuple[2],tuple[3]));
        }

        #[test]
        fn only_exact_found_ref_qualifies(
            id in "[a-z0-9]{1,24}", kind in 0u8..5,
        ){
            let input=fixture();
            let (resolution,expected)=match kind {
                0=>(Resolution::Found{operation_ref:input.operation_ref.clone(),native_id:"job-a".into(),workspace_id:"ws".into()},Binding::Matched),
                1=>(Resolution::Found{operation_ref:format!("ordivon-exec:v1:runtime.linux:foreign-{id}"),native_id:format!("foreign-{id}"),workspace_id:"ws".into()},Binding::Unqualified),
                2=>(Resolution::Absent,Binding::Unqualified),
                3=>(Resolution::Ambiguous,Binding::Unqualified),
                _=>(Resolution::Unobserved{reason:"transport"},Binding::Unqualified),
            };
            prop_assert_eq!(input.qualify(resolution),expected);
        }

        #[test]
        fn blank_ingress_never_creates_key(
            chars in prop::collection::vec(prop::sample::select(vec![' ','\n','\t','\u{1c}','\u{1d}','\u{1e}','\u{1f}','\u{a0}','\u{3000}']),0..20),
            issuer in any::<bool>(),
        ){
            let mut input=fixture();
            let blank=chars.into_iter().collect();
            if issuer {input.issuer=blank;} else {input.principal=blank;}
            prop_assert_eq!(input.scoped_key(),None);
        }
    }
}
