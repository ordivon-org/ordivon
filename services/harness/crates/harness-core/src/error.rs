use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CanonicalError {
    InvalidJson,
    DuplicateKey(String),
    NonIntegerNumber,
    IntegerDigitLimit,
    ExcessiveNesting,
}

impl fmt::Display for CanonicalError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidJson => write!(f, "invalid JSON"),
            Self::DuplicateKey(key) => write!(f, "duplicate JSON object key: {key}"),
            Self::NonIntegerNumber => write!(f, "non-integer JSON number is forbidden"),
            Self::IntegerDigitLimit => write!(f, "integer exceeds native bounded JSON digit limit"),
            Self::ExcessiveNesting => write!(f, "JSON nesting exceeds bounded parser limit"),
        }
    }
}
impl std::error::Error for CanonicalError {}
