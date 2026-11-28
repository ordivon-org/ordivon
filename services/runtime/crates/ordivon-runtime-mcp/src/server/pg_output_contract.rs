// Original PG Scheduling facet for exact SDK Job success schema only.
// Consumer behavior, not source-file position, remains authoritative.
#[path = "pg_output_contract/wire.rs"]
mod pg_job_scheduling_wire;
#[path = "pg_output_contract/schema.rs"]
mod pg_scheduling_schema;
use pg_scheduling_schema::{
    pg_scheduling_success_definition, qualify_pg_scheduling_output_schema,
};

#[cfg(all(test, feature = "legacy-runtime"))]
use pg_job_scheduling_wire::PgJobSchedulingReadback;
#[cfg(all(test, feature = "legacy-runtime"))]
use ordivon_runtime_core::resource_scheduling::ResourceScheduling;

#[cfg(all(test, feature = "legacy-runtime"))]
#[path = "pg_output_contract/legacy_consumer_tests.rs"]
mod pg_scheduling_output_contract_tests;
#[cfg(all(test, feature = "postgres-runtime"))]
#[path = "pg_output_contract/pg_only_consumer_tests.rs"]
mod pg_only_qualified_partial_job_list_schema_tests;
