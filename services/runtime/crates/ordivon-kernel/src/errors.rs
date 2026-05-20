#[derive(Clone, Debug, Eq, PartialEq)]
pub enum KernelError {
    ForgedObservedEvent { origin: String },
    CanonicalizationFailed(String),
    InvalidTime(String),
    InvalidDeclaration(String),
    MissingTrustedSourceIdentity,
    MissingTargetRef,
    MissingAuthorityReference,
    MissingIdempotencyKey,
}

impl std::fmt::Display for KernelError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::ForgedObservedEvent { origin } => {
                write!(f, "origin {origin} cannot emit observed events")
            }
            Self::CanonicalizationFailed(err) => write!(f, "canonicalization failed: {err}"),
            Self::InvalidTime(err) => write!(f, "invalid RFC3339 time: {err}"),
            Self::InvalidDeclaration(err) => write!(f, "invalid declaration: {err}"),
            Self::MissingTrustedSourceIdentity => {
                write!(f, "observed event missing source identity")
            }
            Self::MissingTargetRef => write!(f, "observed event missing targetRef"),
            Self::MissingAuthorityReference => write!(f, "effectful event missing authorityRef"),
            Self::MissingIdempotencyKey => write!(f, "effectful event missing idempotencyKey"),
        }
    }
}

impl std::error::Error for KernelError {}
