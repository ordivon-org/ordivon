import time
import duckdb
from pathlib import Path
from typing import Any
from app.core.config import settings

def get_db_connection(read_only: bool = False, attempts: int = 5, sleep_seconds: float = 0.5) -> duckdb.DuckDBPyConnection:
    """获取 DuckDB 数据库连接 (带重试逻辑)"""
    db_path = settings.db_abs_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return duckdb.connect(str(db_path), read_only=read_only)
        except duckdb.IOException as exc:
            last_error = exc
            if "Could not set lock on file" not in str(exc) or attempt == attempts:
                raise
            time.sleep(sleep_seconds * attempt)
    
    if last_error:
        raise last_error
    return duckdb.connect(str(db_path), read_only=read_only)

def ensure_pipeline_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """初始化 PFIOS 全层级 Schema (v1.1)"""
    # 0. 系统元数据
    conn.execute("""
        create table if not exists system_init (
            id integer primary key,
            initialized_at timestamp not null
        )
    """)
    if conn.execute("select count(*) from system_init").fetchone()[0] == 0:
        conn.execute("insert into system_init values (1, current_timestamp)")

    # 1. 基础行情与特征
    conn.execute("""
        create table if not exists ohlcv (
            exchange varchar not null, symbol varchar not null, timeframe varchar not null,
            ts bigint not null, open double, high double, low double, close double, volume double,
            primary key (exchange, symbol, timeframe, ts)
        )
    """)
    
    # 2. 信号与推理 (Signals & AI Reviews)
    conn.execute("""
        create table if not exists signals (
            signal_id varchar primary key, exchange varchar not null, symbol varchar not null,
            timeframe varchar not null, ts bigint not null, strategy_name varchar not null,
            signal_side varchar not null, signal_strength double not null,
            supporting_evidence varchar, contradicting_evidence varchar,
            expires_at timestamp, context_json varchar not null, status varchar not null,
            created_at timestamp not null, updated_at timestamp not null
        )
    """)
    
    conn.execute("""
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
    """)

    # 3. 账户与持仓 (Account & Positions)
    conn.execute("""
        create table if not exists account_balances (
            sync_id varchar not null, exchange varchar not null, currency varchar not null,
            free double, used double, total double, created_at timestamp not null
        )
    """)

    conn.execute("""
        create table if not exists position_states (
            exchange varchar not null, symbol varchar not null, side varchar not null,
            contracts double, notional double, entry_price double, mark_price double,
            unrealized_pnl double, margin_mode varchar, sync_id varchar not null,
            updated_at timestamp not null, primary key (exchange, symbol, side)
        )
    """)

    # 4. 交易执行与审计 (Executions & Audits)
    conn.execute("""
        create table if not exists order_requests (
            order_request_id varchar primary key, execution_id varchar not null,
            signal_id varchar not null, approval_id varchar not null,
            exchange varchar not null, symbol varchar not null,
            side varchar not null, status varchar not null,
            created_at timestamp not null, updated_at timestamp not null
        )
    """)

    conn.execute("""
        create table if not exists order_events (
            order_event_id varchar primary key, order_request_id varchar not null,
            event_type varchar not null, payload_json varchar not null,
            created_at timestamp not null
        )
    """)

    # 5. 核心资产与策略模型 (PFIOS Deep Assets)
    conn.execute("""
        create table if not exists assets (
            symbol varchar primary key, asset_class varchar not null,
            exchange varchar not null, risk_level integer, tags varchar,
            metadata_json varchar, created_at timestamp not null
        )
    """)

    conn.execute("""
        create table if not exists strategies (
            strategy_id varchar primary key, name varchar not null,
            logic_md varchar, market_regime varchar, win_rate double,
            status varchar not null, created_at timestamp not null,
            updated_at timestamp not null
        )
    """)

    conn.execute("""
        create table if not exists observations (
            obs_id varchar primary key, symbol varchar,
            content varchar not null, sentiment double,
            source varchar not null, created_at timestamp not null
        )
    """)

    # 6. 治理与系统 (Governance & Metadata)
    conn.execute("""
        create table if not exists policies (
            policy_id varchar primary key, name varchar not null,
            rule_yaml varchar not null, status varchar not null,
            created_at timestamp not null
        )
    """)

    conn.execute("""
        create table if not exists risk_audits (
            event_id varchar primary key, workflow_name varchar not null,
            stage varchar not null, decision varchar not null,
            subject_id varchar, status varchar not null,
            triggered_rules_json varchar not null,
            context_summary varchar not null, details_json varchar not null,
            report_path varchar, created_at timestamp not null
        )
    """)

    conn.execute("""
        create table if not exists approvals (
            approval_id varchar primary key, signal_id varchar not null,
            review_id varchar not null, decision varchar not null,
            approved_size double not null, operator_note varchar not null,
            created_at timestamp not null
        )
    """)

    conn.execute("""
        create table if not exists executions (
            execution_id varchar primary key, signal_id varchar not null,
            approval_id varchar not null, executor varchar not null,
            mode varchar not null, status varchar not null,
            submitted_at timestamp not null, filled_at timestamp,
            fill_summary_json varchar not null
        )
    """)

    # 7. 建议与工作流闭环 (Recommendations & Closures) - Step 10
    conn.execute("""
        create table if not exists recommendations (
            recommendation_id varchar primary key,
            source_report_id varchar not null,
            source_audit_id varchar,
            symbol varchar not null,
            action varchar not null,
            confidence double not null,
            decision varchar not null,
            lifecycle_status varchar not null, -- generated|adopted|ignored|tracking|closed
            review_status varchar not null, -- pending|reviewed
            adopted boolean,
            adopted_at timestamp,
            outcome_status varchar not null, -- pending|tracking|closed
            user_note varchar,
            created_at timestamp not null
        )
    """)

    conn.execute("""
        create table if not exists performance_reviews (
            review_id varchar primary key,
            linked_report_id varchar not null,
            linked_recommendation_id varchar,
            symbol varchar not null,
            expected_outcome varchar,
            actual_outcome varchar,
            deviation varchar,
            mistake_tags varchar, -- 逗号分隔或 JSON
            lessons_json varchar not null, -- 结构化 Lessons: [{type, text}]
            new_rule_candidate varchar,
            created_at timestamp not null
        )
    """)

    # 8. 真实使用验证与稳定化 (Validation & Stabilization) - Step 11
    conn.execute("""
        create table if not exists usage_logs (
            date varchar primary key,
            analysis_runs integer not null,
            recommendations_updated integer not null,
            reviews_completed integer not null,
            blocking_issue_count integer not null,
            notes varchar,
            created_at timestamp not null
        )
    """)

    conn.execute("""
        create table if not exists issue_triage (
            issue_id varchar primary key,
            severity varchar not null, -- P0|P1|P2
            area varchar not null, -- dashboard|analyze|audits|reports|recommendation|review|reasoning
            description varchar not null,
            status varchar not null, -- open|fixed|deferred
            created_at timestamp not null
        )
    """)

    conn.execute("""
        create table if not exists validation_summaries (
            week_id varchar primary key,
            days_used integer not null,
            analysis_count integer not null,
            recommendations_count integer not null,
            reviews_count integer not null,
            open_p0_count integer not null,
            open_p1_count integer not null,
            key_lessons_json varchar not null,
            go_no_go varchar not null, -- continue|stabilize_more
            created_at timestamp not null
        )
    """)

def init_db():
    conn = get_db_connection()
    try:
        ensure_pipeline_schema(conn)
    finally:
        conn.close()
