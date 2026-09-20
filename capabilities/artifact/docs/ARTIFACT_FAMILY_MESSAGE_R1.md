# Artifact E2E — Message Family R1

## Standing

`SHADOW_PROFILE_LIVE_PROVEN`

Message R1 proves one bounded Internet Message profile: RFC 5322 message syntax plus MIME 1.0 single-part UTF-8 `text/plain`. It does not claim mailbox-container, authentication or transport semantics.

## Profile

`message-internet-text-r1`

R1 requires:

- CRLF physical line endings;
- RFC 5322 physical-line hard limit <= 998 characters;
- exactly one Date / From / To / Subject / Message-ID / MIME-Version / Content-Type / Content-Transfer-Encoding header;
- one From address and one To address;
- MIME-Version 1.0;
- `text/plain; charset=utf-8`;
- `Content-Transfer-Encoding: 8bit`;
- no multipart, attachment, HTML, Cc or Bcc.

## Evidence topology

### Raw syntax policy

Raw bytes are checked independently from parser behavior. A message that parsers accept with LF-only line endings therefore still fails the bounded R1 CRLF profile.

### Python email parser

Python 3.14.7 stdlib `email` provides the first parser view and must report no parser defects. It also exposes addresses, message headers, MIME facts and decoded body.

### Node mailparser

`mailparser 3.9.26` provides an independent parser view under the Artifact Node 26.9.0 toolchain. Its npm dependency closure is frozen by package-lock identity under `/opt/ordivon/external/mailparser-js/3.9.26`.

Both parser views are normalized to a common semantic representation before comparison.

## Canonical decoded-text identity

Python preserves CRLF in decoded `text/plain` content while mailparser normalizes decoded text to LF. This is consumer representation behavior, not a semantic disagreement.

R1 therefore defines canonical decoded text as:

```text
CRLF → LF
CR   → LF
UTF-8 encode
SHA-256
```

Raw CRLF correctness remains a separate raw-syntax gate. This yields the important distinction:

```text
RawMessageRepresentation != DecodedTextIdentity
```

## Live proof

Runtime job: `job-01a09630-eb77-7103-9e88-f3add42b0f6f`

Exact EML:

- size: 322 bytes;
- SHA-256: `803f9fa067a0d558fcbaa829fccb929fa469ebd9d4edc95fbfbd013b3405df8b`;
- contract canonical digest: `7378e4bc43bffc8b1502858c8a3664241edc965a490ed924677c5647e0e0a706`;
- canonical decoded body SHA-256: `55b312a3ebddd6b9e7fe6b281c29fe7e57b93625041010e329944290ed298377`.

Both parsers agree on:

- Alice Example `<alice@example.invalid>`;
- Bob Example `<bob@example.invalid>`;
- subject `Ordivon message R1`;
- Message-ID `<ordivon-message-r1@example.invalid>`;
- date `2026-09-12T10:00:00Z`;
- MIME 1.0 / text/plain / UTF-8 / 8bit;
- exact canonical decoded body identity.

## Falsifiers

Eight focused tests pass:

1. exact bounded Internet Message + matching contract → PASS;
2. parsers agree, contract expects different subject → FAIL;
3. LF-only message remains parseable but raw R1 policy → FAIL;
4. duplicate Message-ID → singleton-header policy FAIL;
5. valid multipart MIME message → bounded R1 FAIL;
6. both parsers agree on changed body but body contract digest differs → FAIL;
7. valid HTML MIME message → text/plain R1 FAIL;
8. parser/binding identities match the proven substrate.

Therefore:

```text
MessageParseSuccess != MessageProfileSatisfied
ParserAgreement != ExpectedMessageIdentity
```

## Boundary

R1 does not establish SMTP delivery, sender authenticity, DKIM/SPF/DMARC/ARC, malware/spam classification, mailbox-container semantics, attachments, HTML safety/rendering or content truth.
