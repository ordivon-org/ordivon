from governance.audit.auditor import RiskAuditor
from governance.audit.models import AuditEvent
from governance.audit.orm import AuditEventORM
from governance.audit.repository import AuditEventRepository
from governance.audit.service import AuditService
from governance.audit.auditor import RiskAuditor as LegacyRiskAuditor
from governance.audit.models import AuditEvent as LegacyAuditEvent
from governance.audit.orm import AuditEventORM as LegacyAuditEventORM
from governance.audit.repository import AuditEventRepository as LegacyAuditEventRepository
from governance.audit.service import AuditService as LegacyAuditService


def test_root_governance_audit_imports_are_available():
    assert RiskAuditor is not None
    assert AuditEvent is not None
    assert AuditEventORM is not None
    assert AuditEventRepository is not None
    assert AuditService is not None


def test_legacy_audit_imports_still_resolve():
    assert LegacyRiskAuditor.__name__ == RiskAuditor.__name__
    assert LegacyAuditEvent.__name__ == AuditEvent.__name__
    assert LegacyAuditEventORM.__name__ == AuditEventORM.__name__
    assert LegacyAuditEventRepository.__name__ == AuditEventRepository.__name__
    assert LegacyAuditService.__name__ == AuditService.__name__
