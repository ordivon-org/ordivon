from orchestrator.runtime.wake_resume import ResumeDirective, ResumeReason, WakeReason


def test_wake_resume_contracts_keep_runtime_semantics_explicit():
    wake = WakeReason("runtime_recovered_later")
    resume = ResumeReason("fallback_path_completed")
    directive = ResumeDirective(resume_reason=resume.reason, resume_from_ref="handoff_1", resume_count=1)

    assert wake.reason == "runtime_recovered_later"
    assert directive.resume_from_ref == "handoff_1"
    assert directive.resume_reason == "fallback_path_completed"
