"""
DuckDB Pipeline Schema — LEGACY (DuckDB-native, analytics support only)
NOT DOMAIN TRUTH FOR P4 — the SQLAlchemy ORM is the single source of truth.

**IMPORTANT — PostgreSQL migration note:**
This module uses the native ``duckdb`` driver directly, NOT SQLAlchemy.
It is NOT the schema authority for the primary database.  The canonical
startup path uses ``state/db/bootstrap.py`` (SQLAlchemy ``Base.metadata.create_all``)
which works with both DuckDB and PostgreSQL.

This module is retained for:
  1. DuckDB-native legacy table definitions (historical data access).
  2. Optional DuckDB analytics engine use (post-PostgreSQL migration).
  3. Backward compatibility — ``ensure_pipeline_schema`` may be called by
     external scripts that expect DuckDB-specific behavior.

**PostgreSQL schema management (future):**
When PostgreSQL becomes the primary database, all schema changes must be
managed through Alembic migrations (``alembic/``), not through this module.
Do NOT add PostgreSQL-specific DDL here.

This module defines DuckDB tables inherited from the pre-PFIOS monolithic
trading system.  **None of these tables are actively read or written by the
current domain layer.**  All current domain truth lives in SQLAlchemy ORM
models registered in ``state/db/bootstrap.py``.

These DDL statements are retained so that:
  1. Historical data in existing .duckdb files remains accessible.
  2. The ``ensure_pipeline_schema`` entrypoint does not break on startup.

Tables marked LEGACY below have **no active Python read/write code** as of
2026-04-24.  They are candidates for removal once historical data has been
migrated or archived.

Tables marked ACTIVE are still referenced by the current pipeline.
"""

from __future__ import annotations

import duckdb


def ensure_pipeline_schema(conn: duckdb.DuckDBPyConnection) -> None:
    # ACTIVE — used for startup initialization check
    conn.execute(
        """
        create table if not exists system_init (
            id integer primary key,
            initialized_at timestamp not null
        )
        """
    )
    if conn.execute("select count(*) from system_init").fetchone()[0] == 0:
        conn.execute("insert into system_init values (1, current_timestamp)")

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists ohlcv (
            exchange varchar not null, symbol varchar not null, timeframe varchar not null,
            ts bigint not null, open double, high double, low double, close double, volume double,
            primary key (exchange, symbol, timeframe, ts)
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists features (
            exchange varchar not null, symbol varchar not null, timeframe varchar not null,
            ts bigint not null, close double,
            sma_fast double, sma_slow double, volatility_20 double, volume_change double,
            feature_context_json varchar,
            primary key (exchange, symbol, timeframe, ts)
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists signals (
            signal_id varchar primary key, exchange varchar not null, symbol varchar not null,
            timeframe varchar not null, ts bigint not null, strategy_name varchar not null,
            signal_side varchar not null, signal_strength double not null,
            supporting_evidence varchar, contradicting_evidence varchar,
            expires_at timestamp, context_json varchar not null, status varchar not null,
            created_at timestamp not null, updated_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists ai_reviews (
            review_id varchar primary key, signal_id varchar not null,
            thesis_json varchar not null, risk_json varchar not null,
            expectation_vs_reality varchar, deviation double,
            mistake_tags varchar, emotion_tags varchar,
            action varchar not null, size_multiplier double not null,
            confidence double not null, must_review boolean not null,
            note_md varchar not null, model_provider varchar not null,
            model_name varchar not null, created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists account_sync_runs (
            sync_id varchar primary key, exchange varchar not null,
            status varchar not null, note varchar,
            created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists account_balances (
            sync_id varchar not null, exchange varchar not null, currency varchar not null,
            free double, used double, total double, created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists account_positions (
            sync_id varchar not null, exchange varchar not null,
            symbol varchar not null, side varchar, contracts double,
            notional double, entry_price double, mark_price double,
            unrealized_pnl double, margin_mode varchar,
            created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists account_open_orders (
            sync_id varchar not null, exchange varchar not null,
            order_id varchar, client_order_id varchar,
            symbol varchar not null, side varchar, order_type varchar,
            price double, amount double, filled double, remaining double,
            status varchar, reduce_only boolean, created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists position_states (
            exchange varchar not null, symbol varchar not null, side varchar not null,
            contracts double, notional double, entry_price double, mark_price double,
            unrealized_pnl double, margin_mode varchar, sync_id varchar not null,
            updated_at timestamp not null, primary key (exchange, symbol, side)
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists position_lifecycles (
            position_id varchar primary key, exchange varchar not null,
            symbol varchar not null, side varchar not null,
            status varchar not null, entry_price double,
            current_contracts double, current_notional double,
            opened_sync_id varchar, last_sync_id varchar,
            created_at timestamp not null, updated_at timestamp not null,
            closed_at timestamp
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists position_events (
            position_event_id varchar primary key, position_id varchar not null,
            event_type varchar not null, payload_json varchar not null,
            created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code (approvals now use SQLAlchemy ApprovalRecordORM)
    # NOT DOMAIN TRUTH FOR P4 — do not read/write governance state from DuckDB.
    conn.execute(
        """
        create table if not exists approvals (
            approval_id varchar primary key, signal_id varchar not null,
            review_id varchar not null, decision varchar not null,
            approved_size double not null, operator_note varchar not null,
            created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code (executions now use SQLAlchemy ExecutionReceiptORM)
    # NOT DOMAIN TRUTH FOR P4 — do not read/write governance state from DuckDB.
    conn.execute(
        """
        create table if not exists executions (
            execution_id varchar primary key, signal_id varchar not null,
            approval_id varchar not null, executor varchar not null,
            mode varchar not null, system_mode varchar,
            exchange_order_ref varchar,
            status varchar not null,
            submitted_at timestamp not null, filled_at timestamp,
            fill_summary_json varchar not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists order_requests (
            order_request_id varchar primary key, execution_id varchar not null,
            signal_id varchar not null, approval_id varchar not null,
            exchange varchar not null, symbol varchar not null,
            instrument_type varchar, position_action varchar,
            side varchar not null, order_type varchar, time_in_force varchar,
            margin_mode varchar, leverage double, post_only boolean, reduce_only boolean,
            target_price double, stop_price double, stop_loss_pct double,
            take_profit_price double, take_profit_pct double,
            risk_budget_quote double, quote_notional double, base_amount double,
            limit_offset_bps double, params_json varchar, risk_decision_id varchar,
            exchange_order_id varchar, client_order_id varchar,
            exchange_status varchar, submitted_at timestamp, closed_at timestamp,
            filled_amount double, average_price double, last_synced_at timestamp,
            status varchar not null,
            created_at timestamp not null, updated_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists order_events (
            order_event_id varchar primary key, order_request_id varchar not null,
            event_type varchar not null, payload_json varchar not null,
            created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists risk_decisions (
            risk_decision_id varchar primary key,
            signal_id varchar not null, approval_id varchar,
            mode varchar not null, exchange varchar not null, symbol varchar not null,
            signal_side varchar not null, approved_size double,
            decision varchar not null, reasons varchar not null,
            context_json varchar, created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists journals (
            journal_id varchar primary key, signal_id varchar not null,
            execution_id varchar not null, summary_md varchar not null,
            report_path varchar, wiki_path varchar,
            created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists assets (
            symbol varchar primary key, asset_class varchar not null,
            exchange varchar not null, risk_level integer, tags varchar,
            metadata_json varchar, created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists strategies (
            strategy_id varchar primary key, name varchar not null,
            logic_md varchar, market_regime varchar, win_rate double,
            status varchar not null, created_at timestamp not null,
            updated_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists observations (
            obs_id varchar primary key, symbol varchar,
            content varchar not null, sentiment double,
            source varchar not null, created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code (policies now use GovernancePolicySource)
    # NOT DOMAIN TRUTH FOR P4 — do not read/write governance state from DuckDB.
    conn.execute(
        """
        create table if not exists policies (
            policy_id varchar primary key, name varchar not null,
            rule_yaml varchar not null, status varchar not null,
            created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code (audits now use SQLAlchemy AuditEventORM)
    # NOT DOMAIN TRUTH FOR P4 — do not read/write governance state from DuckDB.
    conn.execute(
        """
        create table if not exists risk_audits (
            event_id varchar primary key, workflow_name varchar not null,
            stage varchar not null, decision varchar not null,
            subject_id varchar, status varchar not null,
            triggered_rules_json varchar not null,
            context_summary varchar not null, details_json varchar not null,
            report_path varchar, created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code (recommendations now use SQLAlchemy RecommendationORM)
    # NOT DOMAIN TRUTH FOR P4 — do not read/write governance state from DuckDB.
    conn.execute(
        """
        create table if not exists recommendations (
            recommendation_id varchar primary key,
            source_report_id varchar not null,
            source_audit_id varchar,
            symbol varchar not null,
            action varchar not null,
            confidence double not null,
            decision varchar not null,
            lifecycle_status varchar not null,
            review_status varchar not null,
            adopted boolean,
            adopted_at timestamp,
            outcome_status varchar not null,
            user_note varchar,
            created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code (reviews now use SQLAlchemy ReviewORM)
    # NOT DOMAIN TRUTH FOR P4 — do not read/write governance state from DuckDB.
    conn.execute(
        """
        create table if not exists performance_reviews (
            review_id varchar primary key,
            linked_report_id varchar not null,
            linked_recommendation_id varchar,
            symbol varchar not null,
            expected_outcome varchar,
            actual_outcome varchar,
            deviation varchar,
            mistake_tags varchar,
            lessons_json varchar not null,
            new_rule_candidate varchar,
            created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code (usage now uses SQLAlchemy UsageSnapshotORM)
    # NOT DOMAIN TRUTH FOR P4 — do not read/write governance state from DuckDB.
    conn.execute(
        """
        create table if not exists usage_logs (
            date varchar primary key,
            analysis_runs integer not null,
            recommendations_updated integer not null,
            reviews_completed integer not null,
            blocking_issue_count integer not null,
            notes varchar,
            created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code (issues now use SQLAlchemy IssueORM)
    # NOT DOMAIN TRUTH FOR P4 — do not read/write governance state from DuckDB.
    conn.execute(
        """
        create table if not exists issue_triage (
            issue_id varchar primary key,
            severity varchar not null,
            area varchar not null,
            description varchar not null,
            status varchar not null,
            created_at timestamp not null
        )
        """
    )

    # LEGACY — no active read/write code
    conn.execute(
        """
        create table if not exists validation_summaries (
            week_id varchar primary key,
            days_used integer not null,
            analysis_count integer not null,
            recommendations_count integer not null,
            reviews_count integer not null,
            open_p0_count integer not null,
            open_p1_count integer not null,
            key_lessons_json varchar not null,
            go_no_go varchar not null,
            created_at timestamp not null
        )
        """
    )
