fn validate_ingress_sha256(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value[7..].bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn validate_ingress_relative_object(value: &str) -> bool {
    if value.is_empty() || value.starts_with('/') || value.contains('\\') || value.contains('\0') {
        return false;
    }
    value
        .split('/')
        .all(|part| !part.is_empty() && part != "." && part != "..")
}

fn ingress_ipv4_is_public(value: Ipv4Addr) -> bool {
    let octets = value.octets();
    if value.is_unspecified()
        || value.is_loopback()
        || value.is_private()
        || value.is_link_local()
        || value.is_broadcast()
        || value.is_documentation()
        || value.is_multicast()
    {
        return false;
    }
    if octets[0] == 0
        || (octets[0] == 100 && (64..=127).contains(&octets[1]))
        || (octets[0] == 192 && octets[1] == 0 && octets[2] == 0)
        || (octets[0] == 198 && (octets[1] == 18 || octets[1] == 19))
        || octets[0] >= 240
    {
        return false;
    }
    true
}

fn ingress_ipv6_is_public(value: Ipv6Addr) -> bool {
    if let Some(mapped) = value.to_ipv4_mapped() {
        return ingress_ipv4_is_public(mapped);
    }
    if value.is_unspecified()
        || value.is_loopback()
        || value.is_multicast()
        || value.is_unique_local()
        || value.is_unicast_link_local()
    {
        return false;
    }
    let segments = value.segments();
    !(segments[0] == 0x2001 && segments[1] == 0x0db8)
}

fn ingress_ip_is_public(value: IpAddr) -> bool {
    match value {
        IpAddr::V4(value) => ingress_ipv4_is_public(value),
        IpAddr::V6(value) => ingress_ipv6_is_public(value),
    }
}

fn validate_ingress_download_host_config(host: &str) -> bool {
    if host == "*" {
        return true;
    }
    if host.is_empty()
        || host != host.to_ascii_lowercase()
        || host.contains('/')
        || host.contains(':')
        || host.contains('@')
        || host == "localhost"
        || host.ends_with(".localhost")
        || host.ends_with(".local")
    {
        return false;
    }
    match host.parse::<IpAddr>() {
        Ok(ip) => ingress_ip_is_public(ip),
        Err(_) => true,
    }
}

fn ingress_download_host_allowed(allowed_hosts: &[String], host: &str) -> bool {
    allowed_hosts
        .iter()
        .any(|allowed| allowed == "*" || allowed == host)
}

fn ingress_stage_size_digest(
    path: &std::path::Path,
    max_bytes: u64,
) -> Result<(u64, String), ToolError> {
    let metadata = std::fs::symlink_metadata(path)
        .map_err(|_| ToolError::internal("cannot inspect retained verified input stage"))?;
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err(ToolError::internal(
            "retained verified input stage is not a regular non-symlink file",
        ));
    }
    if metadata.len() > max_bytes {
        return Err(ToolError::invalid(
            "retained input stage exceeds configured maxBytes",
            "file",
        ));
    }
    let mut file = std::fs::File::open(path)
        .map_err(|_| ToolError::internal("cannot open retained verified input stage"))?;
    let mut digest = Sha256::new();
    let mut observed = 0_u64;
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let read = std::io::Read::read(&mut file, &mut buffer)
            .map_err(|_| ToolError::internal("cannot read retained verified input stage"))?;
        if read == 0 {
            break;
        }
        observed = observed.saturating_add(read as u64);
        if observed > max_bytes {
            return Err(ToolError::invalid(
                "retained input stage exceeds configured maxBytes",
                "file",
            ));
        }
        digest.update(&buffer[..read]);
    }
    Ok((observed, format!("sha256:{:x}", digest.finalize())))
}

async fn ingress_pinned_https_get(
    initial: reqwest::Url,
    allowed_hosts: &[String],
) -> Result<reqwest::Response, ToolError> {
    let mut url = initial;
    for redirect_index in 0..=5 {
        if url.scheme() != "https" || !url.username().is_empty() || url.password().is_some() {
            return Err(ToolError::invalid(
                "file.download_url must remain HTTPS without URL userinfo",
                "file.download_url",
            ));
        }
        if url.port_or_known_default() != Some(443) {
            return Err(ToolError::invalid(
                "file.download_url must use the standard HTTPS port",
                "file.download_url",
            ));
        }
        let host = url.host_str().unwrap_or_default().to_ascii_lowercase();
        if !ingress_download_host_allowed(allowed_hosts, &host) {
            return Err(ToolError::invalid(
                "file.download_url host is not operator-authorized for input ingress",
                "file.download_url",
            ));
        }
        let resolved = tokio::net::lookup_host((host.as_str(), 443))
            .await
            .map_err(|_| ToolError::internal("input file download host resolution failed"))?
            .collect::<Vec<SocketAddr>>();
        if resolved.is_empty()
            || resolved
                .iter()
                .any(|address| !ingress_ip_is_public(address.ip()))
        {
            return Err(ToolError::invalid(
                "file.download_url resolved to a non-public network address",
                "file.download_url",
            ));
        }
        let client = reqwest::Client::builder()
            .no_proxy()
            .redirect(reqwest::redirect::Policy::none())
            .resolve_to_addrs(host.as_str(), &resolved)
            .timeout(std::time::Duration::from_secs(180))
            .build()
            .map_err(|_| ToolError::internal("cannot initialize pinned input download client"))?;
        let response = client.get(url.clone()).send().await.map_err(|_| {
            ToolError::internal("input file download failed before a verified local stage existed")
        })?;
        if !response.status().is_redirection() {
            return Ok(response);
        }
        if redirect_index == 5 {
            return Err(ToolError::invalid(
                "input file download exceeded the redirect limit",
                "file.download_url",
            ));
        }
        let location = response
            .headers()
            .get(reqwest::header::LOCATION)
            .and_then(|value| value.to_str().ok())
            .ok_or_else(|| {
                ToolError::invalid(
                    "input file redirect omitted a valid Location",
                    "file.download_url",
                )
            })?;
        url = url.join(location).map_err(|_| {
            ToolError::invalid(
                "input file redirect Location is invalid",
                "file.download_url",
            )
        })?;
    }
    Err(ToolError::internal(
        "input file redirect loop did not terminate",
    ))
}
