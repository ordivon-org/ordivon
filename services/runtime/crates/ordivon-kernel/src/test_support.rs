use base64::{engine::general_purpose::STANDARD as BASE64, Engine as _};
use ed25519_dalek::{Signer, SigningKey};
use std::collections::HashMap;

use crate::{
    AuthorityToken, AuthorityTokenDraft, AuthorityVerifier, Ed25519SealSigner, InMemoryKeyResolver,
    KernelError, KeyMetadata, KeyStatus,
};

pub const TEST_AUTHORITY_KID: &str = "ordivon-test-authority-v1";
pub const TEST_SEAL_KID: &str = "ordivon-test-seal-v1";
const TEST_AUTHORITY_SIGNING_KEY_BYTES: [u8; 32] = [7; 32];
const TEST_SEAL_SIGNING_KEY_BYTES: [u8; 32] = [9; 32];

pub fn test_authority_signing_key() -> SigningKey {
    SigningKey::from_bytes(&TEST_AUTHORITY_SIGNING_KEY_BYTES)
}

pub fn test_seal_signing_key() -> SigningKey {
    SigningKey::from_bytes(&TEST_SEAL_SIGNING_KEY_BYTES)
}

pub fn test_authority_verifier() -> AuthorityVerifier {
    let mut trusted_keys = HashMap::new();
    trusted_keys.insert(
        TEST_AUTHORITY_KID.to_string(),
        test_authority_signing_key().verifying_key(),
    );
    AuthorityVerifier::new(
        trusted_keys,
        "ordivon-authority-service",
        "adapter:mock-action",
    )
}

pub fn sign_test_token(mut token: AuthorityToken) -> Result<AuthorityToken, KernelError> {
    let payload = token.unsigned_payload()?;
    let signature = test_authority_signing_key().sign(payload.as_bytes());
    token.signature = BASE64.encode(signature.to_bytes());
    Ok(token)
}

pub fn signed_test_token(draft: AuthorityTokenDraft) -> Result<AuthorityToken, KernelError> {
    sign_test_token(AuthorityToken::from_unsigned_draft(draft)?)
}

pub fn test_seal_signer() -> Ed25519SealSigner {
    Ed25519SealSigner::new(TEST_SEAL_KID, test_seal_signing_key())
}

pub fn test_seal_key_resolver(status: KeyStatus) -> InMemoryKeyResolver {
    InMemoryKeyResolver::new(vec![KeyMetadata {
        kid: TEST_SEAL_KID.to_string(),
        public_key: test_seal_signing_key().verifying_key(),
        not_before: "2026-05-16T00:00:00Z".to_string(),
        not_after: "2026-06-16T00:00:00Z".to_string(),
        status,
    }])
}
