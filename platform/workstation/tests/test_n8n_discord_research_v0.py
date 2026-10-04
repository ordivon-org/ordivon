import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "n8n" / "workflows" / "ordivon-discord-research-v0.json"
SCHEMA = ROOT / "n8n" / "contracts" / "ordivon-discord-research-v0.schema.json"


def load_workflow() -> dict:
    return json.loads(WORKFLOW.read_text(encoding="utf-8"))


def node(workflow: dict, name: str) -> dict:
    return next(n for n in workflow["nodes"] if n["name"] == name)


def run_code(js_code: str, input_json: dict, named: dict | None = None) -> list[dict]:
    node_bin = shutil.which("node")
    assert node_bin, "node is required for n8n Code-node fixture verification"
    harness = f"""
const INPUT = {json.dumps(input_json)};
const NAMED = {json.dumps(named or {})};
const $input = {{ first: () => ({{ json: INPUT }}) }};
const $ = (name) => ({{ first: () => ({{ json: NAMED[name] }}) }});
const fn = () => {{
{js_code}
}};
try {{
  const out = fn();
  process.stdout.write(JSON.stringify({{ ok: true, out }}));
}} catch (error) {{
  process.stdout.write(JSON.stringify({{ ok: false, error: String(error && error.message || error) }}));
  process.exitCode = 3;
}}
"""
    proc = subprocess.run(
        [node_bin, "-e", harness],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    if not payload["ok"]:
        raise RuntimeError(payload["error"])
    assert proc.returncode == 0, proc.stderr
    return payload["out"]


def valid_event() -> dict:
    return {
        "specversion": "1.0",
        "id": "req-1",
        "source": "urn:test:discord-research",
        "type": "io.ordivon.research.community.discord.search.request.v1",
        "data": {
            "authorityRef": "authority:discord:test-r1",
            "guildId": "123456789012345678",
            "channelIds": ["234567890123456789", "345678901234567890"],
            "content": "browserless challenge",
            "authorIds": ["456789012345678901"],
            "has": ["link", "-video"],
            "limit": 10,
            "offset": 25,
            "sortBy": "relevance",
            "sortOrder": "desc",
        },
    }


def validated_request(workflow: dict) -> dict:
    code = node(workflow, "Validate And Build Search")["parameters"]["jsCode"]
    return run_code(code, valid_event())[0]["json"]


def normalize(workflow: dict, response: dict) -> dict:
    validated = validated_request(workflow)
    code = node(workflow, "Normalize Discord Result")["parameters"]["jsCode"]
    out = run_code(
        code,
        response,
        named={"Validate And Build Search": validated},
    )
    return out[0]["json"]


def test_template_is_inactive_read_only_and_secret_free() -> None:
    workflow = load_workflow()
    assert workflow["active"] is False
    http = node(workflow, "Discord Search Guild Messages")
    assert http["parameters"]["method"] == "GET"
    assert http["parameters"]["authentication"] == "predefinedCredentialType"
    assert http["parameters"]["nodeCredentialType"] == "discordBotApi"
    assert "credentials" not in http
    response = http["parameters"]["options"]["response"]["response"]
    assert response == {
        "fullResponse": True,
        "neverError": True,
        "responseFormat": "json",
    }
    raw = WORKFLOW.read_text(encoding="utf-8")
    assert "Authorization" not in raw
    assert "DISCORD_BOT_TOKEN" not in raw
    assert "externalEffectPerformed: false" in raw


def test_machine_contract_statuses_match_workflow() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    statuses = schema["$defs"]["result"]["properties"]["data"]["properties"]["status"]["enum"]
    assert statuses == [
        "OK",
        "INDEXING_RETRY",
        "RATE_LIMITED",
        "DENIED",
        "PROVIDER_REQUEST_REJECTED",
        "NOT_FOUND",
        "PROVIDER_UNAVAILABLE",
        "UNKNOWN",
    ]


def test_valid_request_builds_bounded_discord_search_url() -> None:
    workflow = load_workflow()
    validated = validated_request(workflow)
    provider = validated["provider"]
    assert provider["method"] == "GET"
    parsed = urlparse(provider["url"])
    assert parsed.scheme == "https"
    assert parsed.netloc == "discord.com"
    assert parsed.path == "/api/v10/guilds/123456789012345678/messages/search"
    query = parse_qs(parsed.query)
    assert query["content"] == ["browserless challenge"]
    assert query["channel_id"] == ["234567890123456789", "345678901234567890"]
    assert query["author_id"] == ["456789012345678901"]
    assert query["has"] == ["link", "-video"]
    assert query["limit"] == ["10"]
    assert query["offset"] == ["25"]
    assert query["include_nsfw"] == ["false"]


def test_content_free_or_channel_free_search_is_rejected() -> None:
    workflow = load_workflow()
    code = node(workflow, "Validate And Build Search")["parameters"]["jsCode"]
    event = valid_event()
    event["data"]["content"] = ""
    try:
        run_code(code, event)
    except RuntimeError as exc:
        assert "broad unfiltered search" in str(exc)
    else:
        raise AssertionError("content-free query unexpectedly admitted")

    event = valid_event()
    event["data"]["channelIds"] = []
    try:
        run_code(code, event)
    except RuntimeError as exc:
        assert "channelIds must be explicit" in str(exc)
    else:
        raise AssertionError("channel-free query unexpectedly admitted")


def test_http_200_normalizes_source_bound_messages_without_claiming_completeness() -> None:
    workflow = load_workflow()
    result = normalize(
        workflow,
        {
            "statusCode": 200,
            "headers": {},
            "body": {
                "doing_deep_historical_index": False,
                "total_results": 100,
                "messages": [
                    [
                        {
                            "id": "777",
                            "channel_id": "234567890123456789",
                            "author": {
                                "id": "999",
                                "username": "alice",
                                "global_name": "Alice",
                            },
                            "content": "browserless challenge notes",
                            "timestamp": "2026-10-01T12:00:00+00:00",
                            "edited_timestamp": None,
                            "pinned": False,
                            "type": 0,
                            "attachments": [
                                {
                                    "id": "888",
                                    "filename": "notes.txt",
                                    "content_type": "text/plain",
                                    "size": 42,
                                    "url": "https://cdn.discordapp.com/secretish-signed-url",
                                }
                            ],
                        }
                    ]
                ],
                "threads": [{"id": "555"}],
            },
        },
    )
    assert result["correlationid"] == "req-1"
    assert result["data"]["status"] == "OK"
    assert result["data"]["provider"]["providerTotalResults"] == 100
    assert result["data"]["provider"]["paginationComplete"] is False
    message = result["data"]["messages"][0]
    assert message["sourceRef"] == (
        "discord:guild:123456789012345678:"
        "channel:234567890123456789:message:777"
    )
    assert message["attachments"] == [
        {
            "id": "888",
            "filename": "notes.txt",
            "contentType": "text/plain",
            "size": 42,
        }
    ]
    assert "url" not in message["attachments"][0]
    assert result["data"]["externalEffectPerformed"] is False


def test_202_429_403_and_5xx_are_typed_not_silently_successful() -> None:
    workflow = load_workflow()

    indexing = normalize(
        workflow,
        {
            "statusCode": 202,
            "headers": {},
            "body": {"code": 110000, "retry_after": 2, "documents_indexed": 17},
        },
    )
    assert indexing["data"]["status"] == "INDEXING_RETRY"
    assert indexing["data"]["provider"]["retryAfterSeconds"] == 2
    assert indexing["data"]["provider"]["documentsIndexed"] == 17

    limited = normalize(
        workflow,
        {
            "statusCode": 429,
            "headers": {"retry-after": "3.5"},
            "body": {},
        },
    )
    assert limited["data"]["status"] == "RATE_LIMITED"
    assert limited["data"]["provider"]["retryAfterSeconds"] == 3.5

    denied = normalize(workflow, {"statusCode": 403, "headers": {}, "body": {}})
    assert denied["data"]["status"] == "DENIED"

    unavailable = normalize(workflow, {"statusCode": 503, "headers": {}, "body": {}})
    assert unavailable["data"]["status"] == "PROVIDER_UNAVAILABLE"


def test_unknown_status_stays_unknown() -> None:
    workflow = load_workflow()
    result = normalize(workflow, {"statusCode": 418, "headers": {}, "body": {}})
    assert result["data"]["status"] == "UNKNOWN"
