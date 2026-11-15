//! Non-production Rust Host migration slice.
//! Host's existing PostgreSQL schema remains the sole persistence authority.
pub mod attention;
pub mod mcp;
pub mod pg;
pub mod social;
pub mod work;
