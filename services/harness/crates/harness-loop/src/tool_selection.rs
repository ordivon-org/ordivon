use std::collections::HashSet;
use std::fmt;

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ToolSelectionError {
    DuplicateSelectedNames,
    OutsideAdmittedSurface(Vec<String>),
}

impl fmt::Display for ToolSelectionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::DuplicateSelectedNames => write!(f, "Turn Tool Working Set names must be unique"),
            Self::OutsideAdmittedSurface(names) => write!(
                f,
                "Turn Tool Working Set references Tools outside the admitted surface: {:?}",
                names
            ),
        }
    }
}
impl std::error::Error for ToolSelectionError {}

/// Mirror select_turn_tool_working_set from turn_projection.py.
/// Preserve admitted catalog order; never discover or authorize new Tools.
pub fn select_tool_indices(
    admitted_names: &[&str],
    selected_names: Option<&[&str]>,
) -> Result<Vec<usize>, ToolSelectionError> {
    let Some(names) = selected_names else {
        return Ok((0..admitted_names.len()).collect());
    };
    let selected: HashSet<&str> = names.iter().copied().collect();
    if selected.len() != names.len() {
        return Err(ToolSelectionError::DuplicateSelectedNames);
    }
    let available: HashSet<&str> = admitted_names.iter().copied().collect();
    let mut missing: Vec<String> = selected
        .difference(&available)
        .map(|name| (*name).to_string())
        .collect();
    if !missing.is_empty() {
        missing.sort();
        return Err(ToolSelectionError::OutsideAdmittedSurface(missing));
    }
    Ok(admitted_names
        .iter()
        .enumerate()
        .filter_map(|(i, name)| selected.contains(name).then_some(i))
        .collect())
}
