#[cfg(unix)]
fn configured_execution_path() -> RuntimeResult<String> {
    let value =
        std::env::var("ORDIVON_EXEC_PATH").unwrap_or_else(|_| DEFAULT_EXECUTION_PATH.to_string());
    if value.is_empty()
        || value.as_bytes().contains(&0)
        || crate::universal::validate_env(&BTreeMap::from([("PATH".to_string(), value.clone())]))
            .is_err()
        || value
            .split(':')
            .any(|entry| entry.is_empty() || !Path::new(entry).is_absolute())
    {
        return Err(RuntimeError::invalid(
            "ORDIVON_EXEC_PATH must fit the Linux execve per-string boundary and contain only absolute paths",
            "ORDIVON_EXEC_PATH",
        ));
    }
    Ok(value)
}

#[cfg(windows)]
fn configured_execution_path() -> RuntimeResult<String> {
    let value = std::env::var("ORDIVON_EXEC_PATH")
        .or_else(|_| std::env::var("PATH"))
        .map_err(|_| {
            RuntimeError::invalid(
                "ORDIVON_EXEC_PATH or PATH is required on native Windows Runtime",
                "ORDIVON_EXEC_PATH",
            )
        })?;
    let paths = std::env::split_paths(&value).collect::<Vec<_>>();
    if value.is_empty()
        || value.as_bytes().contains(&0)
        || crate::universal::validate_env(&BTreeMap::from([("PATH".to_string(), value.clone())]))
            .is_err()
        || paths.is_empty()
        || paths.iter().any(|entry| !entry.is_absolute())
    {
        return Err(RuntimeError::invalid(
            "native Windows execution PATH must contain only absolute Windows paths",
            "ORDIVON_EXEC_PATH",
        ));
    }
    Ok(value)
}

#[cfg(unix)]
fn configured_execution_home() -> RuntimeResult<String> {
    let value = std::env::var("ORDIVON_EXEC_HOME")
        .or_else(|_| std::env::var("HOME"))
        .unwrap_or_else(|_| DEFAULT_EXECUTION_HOME.to_string());
    if value.is_empty()
        || value.as_bytes().contains(&0)
        || crate::universal::validate_env(&BTreeMap::from([("HOME".to_string(), value.clone())]))
            .is_err()
        || !Path::new(&value).is_absolute()
    {
        return Err(RuntimeError::invalid(
            "ORDIVON_EXEC_HOME must fit the Linux execve per-string boundary and be an absolute path",
            "ORDIVON_EXEC_HOME",
        ));
    }
    Ok(value)
}

#[cfg(windows)]
fn configured_execution_home() -> RuntimeResult<String> {
    let value = std::env::var("ORDIVON_EXEC_HOME")
        .or_else(|_| std::env::var("USERPROFILE"))
        .map_err(|_| {
            RuntimeError::invalid(
                "ORDIVON_EXEC_HOME or USERPROFILE is required on native Windows Runtime",
                "ORDIVON_EXEC_HOME",
            )
        })?;
    if value.is_empty()
        || value.as_bytes().contains(&0)
        || crate::universal::validate_env(&BTreeMap::from([("HOME".to_string(), value.clone())]))
            .is_err()
        || !Path::new(&value).is_absolute()
    {
        return Err(RuntimeError::invalid(
            "native Windows execution home must be an absolute Windows path",
            "ORDIVON_EXEC_HOME",
        ));
    }
    Ok(value)
}

fn merge_environment(
    base: &BTreeMap<String, String>,
    explicit: &BTreeMap<String, String>,
) -> BTreeMap<String, String> {
    let mut merged = base.clone();
    merged.extend(
        explicit
            .iter()
            .map(|(name, value)| (name.clone(), value.clone())),
    );
    merged
}
