use ordivon_host_rust::{mcp::HostMcp, pg::HostPg};
use rmcp::{transport::stdio, ServiceExt};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let transport = std::env::var("ORDIVON_HOST_V2_TRANSPORT").unwrap_or_else(|_| "stdio".into());
    if transport != "stdio" {
        return Err(
            "Rust Host staging binary supports only stdio; HTTP parity is not yet implemented"
                .into(),
        );
    }
    let dsn = std::env::var("ORDIVON_HOST_V2_DSN")?;
    let pg = HostPg::new(dsn);
    pg.check_schema().await?;
    let server = HostMcp::new(pg).serve(stdio()).await?;
    server.waiting().await?;
    Ok(())
}
