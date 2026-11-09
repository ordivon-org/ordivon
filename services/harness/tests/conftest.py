"""Harness portable tests gain isolated PostgreSQL fixtures only when supplied."""

from __future__ import annotations

import pytest

from tests.pg_test_support import isolated_harness_schema


@pytest.fixture
def pg_schema():
    with isolated_harness_schema() as binding:
        yield binding
