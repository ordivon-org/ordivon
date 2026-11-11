use axum::Router;
use ordivon_host_rust::{mcp::HostMcp, pg::HostPg};
use rmcp::transport::streamable_http_server::{
    session::local::LocalSessionManager, StreamableHttpServerConfig, StreamableHttpService,
};
use rmcp::{transport::stdio, ServiceExt};
use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr};

fn loopback_bind(host: &str, port: u16) -> Result<SocketAddr, &'static str> {
    let ip = match host {
        "127.0.0.1" | "localhost" => IpAddr::V4(Ipv4Addr::LOCALHOST),
        "::1" => IpAddr::V6(Ipv6Addr::LOCALHOST),
        _ => return Err("ORDIVON_HOST_V2_HOST must be loopback-only"),
    };
    Ok(SocketAddr::new(ip, port))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let dsn = std::env::var("ORDIVON_HOST_V2_DSN")?;
    let pg = HostPg::try_new(dsn)?;
    pg.check_schema().await?;
    let server = HostMcp::new(pg);
    let transport = std::env::var("ORDIVON_HOST_V2_TRANSPORT").unwrap_or_else(|_| "stdio".into());
    match transport.as_str() {
        "stdio" => {
            let process = server.serve(stdio()).await?;
            process.waiting().await?;
        }
        "streamable-http" => {
            let host = std::env::var("ORDIVON_HOST_V2_HOST").unwrap_or_else(|_| "127.0.0.1".into());
            let port = std::env::var("ORDIVON_HOST_V2_PORT")
                .unwrap_or_else(|_| "8898".into())
                .parse::<u16>()?;
            let bind = loopback_bind(&host, port)?;
            let path = std::env::var("ORDIVON_HOST_V2_PATH").unwrap_or_else(|_| "/mcp".into());
            if !path.starts_with('/') || path.contains("//") || path.contains("..") {
                return Err("ORDIVON_HOST_V2_PATH must be an absolute simple HTTP path".into());
            }
            let service_server = server.clone();
            let service: StreamableHttpService<HostMcp, LocalSessionManager> =
                StreamableHttpService::new(
                    move || Ok(service_server.clone()),
                    Default::default(),
                    StreamableHttpServerConfig::default()
                        .with_json_response(true)
                        .with_sse_keep_alive(None)
                        .with_allowed_origins([
                            "http://127.0.0.1:*",
                            "http://localhost:*",
                            "http://[::1]:*",
                        ]),
                );
            let listener = tokio::net::TcpListener::bind(bind).await?;
            let app = Router::new().nest_service(&path, service);
            axum::serve(listener, app)
                .with_graceful_shutdown(async {
                    let _ = tokio::signal::ctrl_c().await;
                })
                .await?;
        }
        _ => return Err("ORDIVON_HOST_V2_TRANSPORT must be stdio or streamable-http".into()),
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn http_never_binds_wildcard_or_public_address() {
        assert_eq!(
            loopback_bind("localhost", 8898).expect("loopback").ip(),
            IpAddr::V4(Ipv4Addr::LOCALHOST)
        );
        assert!(loopback_bind("0.0.0.0", 8898).is_err());
        assert!(loopback_bind("192.168.1.1", 8898).is_err());
    }
}
