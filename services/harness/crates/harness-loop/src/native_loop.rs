//! Bounded Rust Agent decision loop with explicit durable-admission boundaries.
//! A trait is an owner port, not an old Python adapter or a substitute for PG.
use crate::{
    pg_domain_read::ObservedNoToolRun,
    tool_arguments::validate_granted_tool_arguments,
    tool_call::{
        inspect_model_tool_call, preflight_domain_model_call, ModelToolCall, ModelToolCallStanding,
    },
    tool_surface::DomainToolSurface,
};
use ordivon_harness_core::{digest_bytes, CanonicalDocument};
use std::collections::HashSet;

#[derive(Debug, Clone)]
pub enum ModelDecision {
    ProposeCompletion(String),
    RequestInput,
    CallTools(Vec<CanonicalDocument>),
}
#[derive(Debug, Clone)]
pub enum ProviderResult {
    Delivered(ModelDecision),
    Unknown,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ToolObservation {
    pub call_id: String,
    pub name: String,
    pub owner_receipt_digest: String,
    /// Provider-visible projection released by the authoritative Journal.
    /// This is model data, not a Tool/Provider instruction or completion proof.
    pub model_visible_content: Option<String>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EffectResult {
    Observed { owner_receipt_digest: String },
    Unknown,
}

/// A successful physical owner receipt never implies permission to send raw
/// Tool output to a model. Only the journal's privacy/evidence release port
/// can select a bounded, digest-bound Provider-visible projection.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ModelVisibleContent {
    Redacted,
    Released {
        text: String,
        content_digest: String,
    },
}

const MAX_MODEL_VISIBLE_BYTES: usize = 65_536;
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RunResult {
    CompletionProposal(String),
    NeedsInput,
    PausedUnknown,
    ExhaustedTurns,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RunFault {
    InvalidBudget,
    InactiveRun,
    InvalidProviderAction,
    InvalidModelTool,
    InvalidToolArguments,
    DuplicateCallId,
    ToolNotGranted,
    TooManyToolCalls,
    Journal(String),
}

/// Only a durable, authoritative Journal can construct a positive tool grant.
/// The engine itself never guesses whether a physical effect was committed.
#[derive(Debug)]
pub struct AdmittedTool {
    call_id: String,
    name: String,
    digest: String,
}
impl AdmittedTool {
    /// Journal-authoritative code constructs this only after an exact Tool
    /// Intent/Fence is committed. Construction alone cannot authorize effects.
    pub fn after_committed_intent(call: &ModelToolCall) -> Self {
        Self {
            call_id: call.tool_call_id().to_owned(),
            name: call.name().to_owned(),
            digest: call.digest().to_owned(),
        }
    }
    pub fn call_id(&self) -> &str {
        &self.call_id
    }
    pub fn name(&self) -> &str {
        &self.name
    }
    pub fn digest(&self) -> &str {
        &self.digest
    }
}
pub trait Provider {
    fn turn(&mut self, number: u32, observations: &[ToolObservation]) -> ProviderResult;
}
pub trait DurableJournal {
    fn prepare_provider(&mut self, turn: u32) -> Result<(), String>;
    fn complete_provider(&mut self, turn: u32, decision: &ModelDecision) -> Result<(), String>;
    fn admit_tool(&mut self, turn: u32, call: &ModelToolCall) -> Result<AdmittedTool, String>;
    fn record_effect(
        &mut self,
        turn: u32,
        grant: &AdmittedTool,
        result: &EffectResult,
    ) -> Result<ModelVisibleContent, String>;
    fn record_completion(&mut self, turn: u32, proposal: &str) -> Result<(), String>;
    fn record_pause(&mut self, turn: u32) -> Result<(), String>;
}
pub trait EffectReceiver {
    /// The owner verifies real effect authority and returns its own receipt.
    /// A transport failure MUST be returned as Unknown, not as fake absence.
    fn execute(&mut self, grant: &AdmittedTool, arguments: &CanonicalDocument) -> EffectResult;
}

pub struct NativeAgentLoop<'a, P: Provider, J: DurableJournal, E: EffectReceiver> {
    provider: &'a mut P,
    journal: &'a mut J,
    receiver: &'a mut E,
    catalog: Option<&'a CanonicalDocument>,
    surface: Option<&'a DomainToolSurface>,
    max_turns: u32,
    max_tool_calls: u32,
}
impl<'a, P: Provider, J: DurableJournal, E: EffectReceiver> NativeAgentLoop<'a, P, J, E> {
    pub fn new(
        provider: &'a mut P,
        journal: &'a mut J,
        receiver: &'a mut E,
        catalog: &'a CanonicalDocument,
        surface: &'a DomainToolSurface,
        max_turns: u32,
        max_tool_calls: u32,
    ) -> Result<Self, RunFault> {
        if max_turns == 0 {
            return Err(RunFault::InvalidBudget);
        }
        surface
            .model_definitions(catalog)
            .map_err(|_| RunFault::ToolNotGranted)?;
        Ok(Self {
            provider,
            journal,
            receiver,
            catalog: Some(catalog),
            surface: Some(surface),
            max_turns,
            max_tool_calls,
        })
    }

    /// Ordinary Provider-only Run: caller must supply an A-verified PG
    /// no-Tool Contract projection. The result is a source identity check,
    /// not a live lease or dispatch grant. DurableJournal must recheck live
    /// Run authority before permitting any Provider request.
    pub fn new_provider_only(
        provider: &'a mut P,
        journal: &'a mut J,
        receiver: &'a mut E,
        verified: &ObservedNoToolRun,
        max_turns: u32,
    ) -> Result<Self, RunFault> {
        if max_turns == 0 {
            return Err(RunFault::InvalidBudget);
        }
        if !matches!(verified.status(), "created" | "active")
            || verified.model_visible_tool_count() != 0
        {
            return Err(RunFault::InactiveRun);
        }
        Ok(Self {
            provider,
            journal,
            receiver,
            catalog: None,
            surface: None,
            max_turns,
            max_tool_calls: 0,
        })
    }

    pub fn run(&mut self) -> Result<RunResult, RunFault> {
        let mut observations = Vec::new();
        let mut seen = HashSet::new();
        let mut total_calls = 0u32;
        for turn in 1..=self.max_turns {
            self.journal
                .prepare_provider(turn)
                .map_err(RunFault::Journal)?;
            let delivered = self.provider.turn(turn, &observations);
            let decision = match delivered {
                ProviderResult::Unknown => {
                    self.journal.record_pause(turn).map_err(RunFault::Journal)?;
                    return Ok(RunResult::PausedUnknown);
                }
                ProviderResult::Delivered(decision) => decision,
            };
            self.journal
                .complete_provider(turn, &decision)
                .map_err(RunFault::Journal)?;
            match decision {
                ModelDecision::ProposeCompletion(text) => {
                    if text.is_empty() {
                        return Err(RunFault::InvalidProviderAction);
                    }
                    self.journal
                        .record_completion(turn, &text)
                        .map_err(RunFault::Journal)?;
                    return Ok(RunResult::CompletionProposal(text));
                }
                ModelDecision::RequestInput => {
                    self.journal.record_pause(turn).map_err(RunFault::Journal)?;
                    return Ok(RunResult::NeedsInput);
                }
                ModelDecision::CallTools(docs) => {
                    if docs.is_empty() {
                        return Err(RunFault::InvalidProviderAction);
                    }
                    let (Some(surface), Some(catalog)) = (self.surface, self.catalog) else {
                        // A source-authenticated no-Tool Run must reject even
                        // a model-hallucinated Tool call with zero physical effect.
                        return Err(RunFault::ToolNotGranted);
                    };
                    let n = u32::try_from(docs.len()).map_err(|_| RunFault::TooManyToolCalls)?;
                    if n > self.max_tool_calls.saturating_sub(total_calls) {
                        return Err(RunFault::TooManyToolCalls);
                    }
                    // Preflight the *entire* model batch before first physical effect.
                    let mut batch_seen = seen.clone();
                    let mut accepted = Vec::with_capacity(docs.len());
                    for doc in &docs {
                        let call =
                            inspect_model_tool_call(doc).map_err(|_| RunFault::InvalidModelTool)?;
                        match preflight_domain_model_call(
                            surface,catalog,
                            surface.catalog_digest(),surface.grant_digest(),
                            &call,&batch_seen
                        ).map_err(|_|RunFault::ToolNotGranted)?{
                            ModelToolCallStanding::DuplicateCallIdentity=>return Err(RunFault::DuplicateCallId),
                            ModelToolCallStanding::LocallyRejectedProviderArguments=>return Err(RunFault::InvalidModelTool),
                            ModelToolCallStanding::NotOnVisibleGrantedToolSurface=>return Err(RunFault::ToolNotGranted),
                            ModelToolCallStanding::NeedsAuthenticatedContractAndDurableAdmission=>{}
                        }
                        // Enforce frozen granted Tool parameter schema before any
                        // batch effect; a model-proposed name is not authority.
                        validate_granted_tool_arguments(surface, catalog, &call, doc)
                            .map_err(|_| RunFault::InvalidToolArguments)?;
                        batch_seen.insert(call.tool_call_id().to_owned());
                        accepted.push(call);
                    }
                    for (doc, call) in docs.iter().zip(&accepted) {
                        // Durable admit -> effect receiver -> durable owner observation.
                        let grant = self
                            .journal
                            .admit_tool(turn, call)
                            .map_err(RunFault::Journal)?;
                        if grant.call_id() != call.tool_call_id()
                            || grant.name() != call.name()
                            || grant.digest() != call.digest()
                        {
                            return Err(RunFault::Journal(
                                "returned grant mismatches current Tool Call".into(),
                            ));
                        }
                        let effect = self.receiver.execute(&grant, doc);
                        if let EffectResult::Observed {
                            owner_receipt_digest,
                        } = &effect
                        {
                            if !valid_digest(owner_receipt_digest) {
                                return Err(RunFault::Journal(
                                    "unqualified owner receipt digest".into(),
                                ));
                            }
                        }
                        let released = self
                            .journal
                            .record_effect(turn, &grant, &effect)
                            .map_err(RunFault::Journal)?;
                        match effect {
                            EffectResult::Unknown => {
                                if released != ModelVisibleContent::Redacted {
                                    return Err(RunFault::Journal(
                                        "UNKNOWN effect must never release model content".into(),
                                    ));
                                }
                                self.journal.record_pause(turn).map_err(RunFault::Journal)?;
                                return Ok(RunResult::PausedUnknown);
                            }
                            EffectResult::Observed {
                                owner_receipt_digest,
                            } => {
                                let model_visible_content = match released {
                                    ModelVisibleContent::Redacted => None,
                                    ModelVisibleContent::Released {
                                        text,
                                        content_digest,
                                    } => {
                                        // Owner-approved content is still untrusted model data.
                                        // Verify its exact bytes before the NEXT Provider turn.
                                        if text.is_empty()
                                            || text.len() > MAX_MODEL_VISIBLE_BYTES
                                            || digest_bytes(text.as_bytes()) != content_digest
                                        {
                                            return Err(RunFault::Journal(
                                                "unqualified model-visible Tool projection".into(),
                                            ));
                                        }
                                        Some(text)
                                    }
                                };
                                observations.push(ToolObservation {
                                    call_id: call.tool_call_id().to_owned(),
                                    name: call.name().to_owned(),
                                    owner_receipt_digest,
                                    model_visible_content,
                                });
                            }
                        }
                    }
                    seen = batch_seen;
                    total_calls = total_calls
                        .checked_add(n)
                        .ok_or(RunFault::TooManyToolCalls)?;
                }
            }
        }
        Ok(RunResult::ExhaustedTurns)
    }
}
fn valid_digest(d: &str) -> bool {
    d.len() == 71
        && d.starts_with("sha256:")
        && d.as_bytes()[7..]
            .iter()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(b))
}
#[cfg(test)]
mod tests {
    use super::*;
    use crate::tool_surface::project_domain_tool_surface;
    use ordivon_harness_core::{digest_bytes, loads_strict};
    use std::collections::VecDeque;
    struct Script(VecDeque<ProviderResult>);
    impl Provider for Script {
        fn turn(&mut self, _: u32, _: &[ToolObservation]) -> ProviderResult {
            self.0.pop_front().expect("bounded scripted turns")
        }
    }
    #[derive(Default)]
    struct Journal {
        steps: Vec<&'static str>,
        deny: &'static str,
        release: Option<ModelVisibleContent>,
    }
    impl DurableJournal for Journal {
        fn prepare_provider(&mut self, _: u32) -> Result<(), String> {
            self.steps.push("provider-prepared");
            Ok(())
        }
        fn complete_provider(&mut self, _: u32, _: &ModelDecision) -> Result<(), String> {
            self.steps.push("provider-recorded");
            Ok(())
        }
        fn admit_tool(&mut self, _: u32, c: &ModelToolCall) -> Result<AdmittedTool, String> {
            self.steps.push("tool-admitted");
            if self.deny == "admit" {
                return Err("PG admission refused".into());
            }
            Ok(AdmittedTool {
                call_id: c.tool_call_id().into(),
                name: c.name().into(),
                digest: c.digest().into(),
            })
        }
        fn record_effect(
            &mut self,
            _: u32,
            _: &AdmittedTool,
            _: &EffectResult,
        ) -> Result<ModelVisibleContent, String> {
            self.steps.push("owner-recorded");
            Ok(self
                .release
                .clone()
                .unwrap_or(ModelVisibleContent::Redacted))
        }
        fn record_completion(&mut self, _: u32, _: &str) -> Result<(), String> {
            self.steps.push("proposal-recorded");
            Ok(())
        }
        fn record_pause(&mut self, _: u32) -> Result<(), String> {
            self.steps.push("paused");
            Ok(())
        }
    }
    #[derive(Default)]
    struct Receiver {
        calls: usize,
        unknown: bool,
    }
    impl EffectReceiver for Receiver {
        fn execute(&mut self, _: &AdmittedTool, _: &CanonicalDocument) -> EffectResult {
            self.calls += 1;
            if self.unknown {
                EffectResult::Unknown
            } else {
                EffectResult::Observed {
                    owner_receipt_digest: digest_bytes(b"owner-receipt"),
                }
            }
        }
    }
    fn fixtures() -> (CanonicalDocument, DomainToolSurface) {
        let catalog=loads_strict(r#"{"schemaVersion":1,"kind":"ordivon.domain-tool-catalog","domainId":"domain:test","revision":"v1","tools":[{"name":"read","description":"read","inputSchema":{}},{"name":"write","description":"write","inputSchema":{}}]}"#).unwrap();
        let grant = project_domain_tool_surface(&catalog, &["read"]).unwrap();
        (catalog, grant)
    }
    fn call(id: &str, name: &str) -> CanonicalDocument {
        loads_strict(&format!(
            r#"{{"toolCallId":"{id}","name":"{name}","arguments":{{}}}}"#
        ))
        .unwrap()
    }
    #[test]
    fn bounded_native_run_proposes_result_after_owner_effect() {
        let (catalog, grant) = fixtures();
        let mut provider = Script(VecDeque::from([
            ProviderResult::Delivered(ModelDecision::CallTools(vec![call("call:1", "read")])),
            ProviderResult::Delivered(ModelDecision::ProposeCompletion("candidate".into())),
        ]));
        let mut journal = Journal::default();
        let mut receiver = Receiver::default();
        let result = NativeAgentLoop::new(
            &mut provider,
            &mut journal,
            &mut receiver,
            &catalog,
            &grant,
            3,
            1,
        )
        .unwrap()
        .run()
        .unwrap();
        assert_eq!(result, RunResult::CompletionProposal("candidate".into()));
        assert_eq!(receiver.calls, 1);
        assert_eq!(
            journal.steps,
            vec![
                "provider-prepared",
                "provider-recorded",
                "tool-admitted",
                "owner-recorded",
                "provider-prepared",
                "provider-recorded",
                "proposal-recorded"
            ]
        );
    }
    #[test]
    fn unknown_provider_is_not_resubmitted() {
        let (catalog, grant) = fixtures();
        let mut provider = Script(VecDeque::from([ProviderResult::Unknown]));
        let mut journal = Journal::default();
        let mut receiver = Receiver::default();
        assert_eq!(
            NativeAgentLoop::new(
                &mut provider,
                &mut journal,
                &mut receiver,
                &catalog,
                &grant,
                4,
                4
            )
            .unwrap()
            .run()
            .unwrap(),
            RunResult::PausedUnknown
        );
        assert_eq!(journal.steps, vec!["provider-prepared", "paused"]);
    }
    #[test]
    fn unknown_effect_stops_before_later_effect() {
        let (catalog, grant) = fixtures();
        let mut provider = Script(VecDeque::from([ProviderResult::Delivered(
            ModelDecision::CallTools(vec![call("call:1", "read"), call("call:2", "read")]),
        )]));
        let mut journal = Journal::default();
        let mut receiver = Receiver {
            unknown: true,
            ..Default::default()
        };
        assert_eq!(
            NativeAgentLoop::new(
                &mut provider,
                &mut journal,
                &mut receiver,
                &catalog,
                &grant,
                3,
                2
            )
            .unwrap()
            .run()
            .unwrap(),
            RunResult::PausedUnknown
        );
        assert_eq!(receiver.calls, 1);
    }
    #[test]
    fn duplicate_batch_is_preflight_rejected_with_zero_effect() {
        let (catalog, grant) = fixtures();
        let mut provider = Script(VecDeque::from([ProviderResult::Delivered(
            ModelDecision::CallTools(vec![call("call:1", "read"), call("call:1", "read")]),
        )]));
        let mut journal = Journal::default();
        let mut receiver = Receiver::default();
        assert_eq!(
            NativeAgentLoop::new(
                &mut provider,
                &mut journal,
                &mut receiver,
                &catalog,
                &grant,
                3,
                2
            )
            .unwrap()
            .run(),
            Err(RunFault::DuplicateCallId)
        );
        assert_eq!(receiver.calls, 0);
    }
    #[test]
    fn unknown_tool_denied_even_with_signed_catalog() {
        let (catalog, grant) = fixtures();
        let mut provider = Script(VecDeque::from([ProviderResult::Delivered(
            ModelDecision::CallTools(vec![call("call:1", "write")]),
        )]));
        let mut journal = Journal::default();
        let mut receiver = Receiver::default();
        assert_eq!(
            NativeAgentLoop::new(
                &mut provider,
                &mut journal,
                &mut receiver,
                &catalog,
                &grant,
                3,
                2
            )
            .unwrap()
            .run(),
            Err(RunFault::ToolNotGranted)
        );
        assert_eq!(receiver.calls, 0);
    }
    #[test]
    fn failed_durable_admission_prevents_dispatch() {
        let (catalog, grant) = fixtures();
        let mut provider = Script(VecDeque::from([ProviderResult::Delivered(
            ModelDecision::CallTools(vec![call("call:1", "read")]),
        )]));
        let mut journal = Journal {
            deny: "admit",
            ..Default::default()
        };
        let mut receiver = Receiver::default();
        assert_eq!(
            NativeAgentLoop::new(
                &mut provider,
                &mut journal,
                &mut receiver,
                &catalog,
                &grant,
                3,
                2
            )
            .unwrap()
            .run(),
            Err(RunFault::Journal("PG admission refused".into()))
        );
        assert_eq!(receiver.calls, 0);
    }
    #[test]
    fn no_tool_budget_disallows_call() {
        let (catalog, grant) = fixtures();
        let mut provider = Script(VecDeque::from([ProviderResult::Delivered(
            ModelDecision::CallTools(vec![call("call:1", "read")]),
        )]));
        let mut journal = Journal::default();
        let mut receiver = Receiver::default();
        assert_eq!(
            NativeAgentLoop::new(
                &mut provider,
                &mut journal,
                &mut receiver,
                &catalog,
                &grant,
                3,
                0
            )
            .unwrap()
            .run(),
            Err(RunFault::TooManyToolCalls)
        );
    }
    #[test]
    fn valid_tool_batch_without_conclusion_is_bounded() {
        let (catalog, grant) = fixtures();
        let mut provider = Script(VecDeque::from([ProviderResult::Delivered(
            ModelDecision::CallTools(vec![call("call:1", "read")]),
        )]));
        let mut journal = Journal::default();
        let mut receiver = Receiver::default();
        assert_eq!(
            NativeAgentLoop::new(
                &mut provider,
                &mut journal,
                &mut receiver,
                &catalog,
                &grant,
                1,
                1
            )
            .unwrap()
            .run()
            .unwrap(),
            RunResult::ExhaustedTurns
        );
    }
    #[test]
    fn input_request_does_not_infer_domain_completion() {
        let (catalog, grant) = fixtures();
        let mut provider = Script(VecDeque::from([ProviderResult::Delivered(
            ModelDecision::RequestInput,
        )]));
        let mut journal = Journal::default();
        let mut receiver = Receiver::default();
        assert_eq!(
            NativeAgentLoop::new(
                &mut provider,
                &mut journal,
                &mut receiver,
                &catalog,
                &grant,
                1,
                0
            )
            .unwrap()
            .run()
            .unwrap(),
            RunResult::NeedsInput
        );
    }
    #[test]
    fn entire_batch_schema_preflight_blocks_all_effects_even_if_first_call_valid() {
        let catalog = loads_strict(
            r#"{
            "schemaVersion":1,"kind":"ordivon.domain-tool-catalog",
            "domainId":"domain:validation","revision":"r1","tools":[
            {"name":"read","description":"Read","inputSchema":{
                "type":"object","properties":{"count":{"type":"integer","minimum":1}},
                "required":["count"],"additionalProperties":false
            }}]}"#,
        )
        .unwrap();
        let surface =
            crate::tool_surface::project_domain_tool_surface(&catalog, &["read"]).unwrap();
        let mut provider = Script(VecDeque::from([ProviderResult::Delivered(
            ModelDecision::CallTools(vec![
                loads_strict(
                    r#"{"toolCallId":"call:first","name":"read","arguments":{"count":1}}"#,
                )
                .unwrap(),
                loads_strict(
                    r#"{"toolCallId":"call:second","name":"read","arguments":{"count":"bad"}}"#,
                )
                .unwrap(),
            ]),
        )]));
        let mut journal = Journal::default();
        let mut receiver = Receiver::default();
        assert_eq!(
            NativeAgentLoop::new(
                &mut provider,
                &mut journal,
                &mut receiver,
                &catalog,
                &surface,
                2,
                2
            )
            .unwrap()
            .run(),
            Err(RunFault::InvalidToolArguments)
        );
        assert_eq!(receiver.calls, 0);
        assert!(!journal.steps.contains(&"tool-admitted"));
    }
    #[test]
    fn forged_or_oversized_provider_visible_tool_content_is_never_sent_to_model() {
        let (catalog, grant) = fixtures();
        for release in [
            ModelVisibleContent::Released {
                text: "Private content".into(),
                content_digest: digest_bytes(b"unrelated"),
            },
            ModelVisibleContent::Released {
                text: "z".repeat(MAX_MODEL_VISIBLE_BYTES + 1),
                content_digest: digest_bytes("z".repeat(MAX_MODEL_VISIBLE_BYTES + 1).as_bytes()),
            },
        ] {
            let mut provider = Script(VecDeque::from([
                ProviderResult::Delivered(ModelDecision::CallTools(vec![call("call:1", "read")])),
                ProviderResult::Delivered(ModelDecision::ProposeCompletion(
                    "never observed".into(),
                )),
            ]));
            let mut journal = Journal {
                release: Some(release),
                ..Default::default()
            };
            let mut receiver = Receiver::default();
            assert_eq!(
                NativeAgentLoop::new(
                    &mut provider,
                    &mut journal,
                    &mut receiver,
                    &catalog,
                    &grant,
                    3,
                    1
                )
                .unwrap()
                .run(),
                Err(RunFault::Journal(
                    "unqualified model-visible Tool projection".into()
                ))
            );
            assert_eq!(receiver.calls, 1);
            assert!(!journal.steps.contains(&"proposal-recorded"));
        }
    }

    #[test]
    fn unknown_effect_never_releases_any_provider_visible_content() {
        let (catalog, grant) = fixtures();
        let mut provider = Script(VecDeque::from([ProviderResult::Delivered(
            ModelDecision::CallTools(vec![call("call:1", "read")]),
        )]));
        let mut journal = Journal {
            release: Some(ModelVisibleContent::Released {
                text: "fake knowledge".into(),
                content_digest: digest_bytes(b"fake knowledge"),
            }),
            ..Default::default()
        };
        let mut receiver = Receiver {
            unknown: true,
            ..Default::default()
        };
        assert_eq!(
            NativeAgentLoop::new(
                &mut provider,
                &mut journal,
                &mut receiver,
                &catalog,
                &grant,
                2,
                1
            )
            .unwrap()
            .run(),
            Err(RunFault::Journal(
                "UNKNOWN effect must never release model content".into()
            ))
        );
        assert_eq!(receiver.calls, 1);
    }
}
