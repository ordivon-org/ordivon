# China Student Seed Deep Structures R3

Date: 2026-09-20
Status: COMPLEMENT TO CHINA_STUDENT_SEED_PORTFOLIO_R3 — task-local hypotheses, not a product ontology.

## 0. Purpose

CHINA_STUDENT_SEED_PORTFOLIO_R3 identifies concrete seed entry points and an emerging personal opportunity/obligation action layer.

This document records deeper structures that recur across those seeds so future experiments do not rebuild the same logic separately for competitions, second classroom, recommendation, internships, graduation, study abroad and other workflows.

## 1. Six shared primitives

### 1. Authority watcher

Monitor relevant public authoritative sources, detect new/changed notices, preserve source identity/date/scope, and distinguish authority from social repost.

Useful across course/admin notices, scholarship, competition, second classroom, innovation projects, internship, postgraduate/recommendation, study abroad and public recruitment.

### 2. Eligibility compiler

official rule + explicit student facts -> MATCH / NO MATCH / UNKNOWN

UNKNOWN must stay explicit when a rule depends on institutional discretion, ambiguous major codes, rank, adviser approval, school interpretation, residence/status, or another missing fact.

The product question is often not "what does the notice say?" but "does it apply to me?"

### 3. Deadline / prerequisite graph

A deadline is often useless if the student discovers it after the real preparation window.

Example:
external competition deadline <- school internal nomination <- adviser confirmation <- team formation <- proposal preparation

The product should expose the earliest action that preserves the option.

### 4. Student evidence passport

Maintain user-controlled factual evidence from legitimate activity: grade/transcript facts, competition records, second-classroom records, research/project artifacts, certificates, open-source/GitHub/Gitee evidence, volunteer/service records, internship/project outcomes.

Bind:
claim -> evidence -> issuer/source -> date -> verification/currentness

Do not invent or embellish claims.

### 5. Action/state tracker

Discovery is not completion.

Useful state:
discovered -> relevant? -> eligible? -> prerequisites missing -> saved -> registered -> submitted -> accepted/rejected -> evidence retained -> follow-up due

### 6. Outcome loop

Where lawful and consented, capture applied/not applied, accepted/rejected, activity credit granted/rejected, run counted/invalid, interview/offer, competition result and research review outcome.

This is the feedback needed to improve future filtering and workflow support. Technical access does not imply training/product-improvement rights.

## 2. Three economic classes

### Loss avoidance

Examples: graduation requirement, second-classroom shortfall, PE running, attendance/deadline, administrative materials.

User motivation: "Do not let me lose something I should already have."

Characteristics: high urgency, easy outcome verification, frequent reminder value, but consumer willingness to pay may be modest unless failure cost is salient.

### Opportunity capture

Examples: competition, scholarship, research programme, exchange, internship, volunteer programme.

User motivation: "Show me valuable options before the preparation window closes."

Characteristics: information asymmetry, peer sharing, relevance/precision problem, strong need for authoritative freshness.

### Transition navigation

Examples: recommendation/exemption, postgraduate examination, study abroad, graduate employment, public recruitment.

User motivation: "This affects years of my future."

Characteristics: higher trust burden, seasonal use, complex eligibility/materials, potentially higher willingness to pay for a bounded season.

The same primitives can support all three while customer offer and economics remain different.

## 3. New seed — Graduation Risk Auditor

Graduation risk is unusually attractive structurally because there is an external authoritative outcome.

Observed university practice shows graduation review can depend on completed credits, current/final course state, major curriculum, minor/double-major curriculum, programme changes and manual course matching. Other institutions can additionally bind second-classroom or PE requirements.

Candidate workflow:
programme requirements + completed state + current state -> confirmed complete / confirmed gap / ambiguous mapping -> next correction deadline / authority

Important: this is school-specific and cannot be generalized from one university's rules.

## 4. New seed — Second-Classroom Gap -> Opportunity Match

Incumbent systems such as 到梦空间/PU already record activities, registrations, credits and transcripts.

The residual may be:
my required categories + current credited state -> exact shortfall + currently available legitimate activities -> actions that can close the gap

The value is not replacing the record system; it is interpreting the student's state against requirements and options.

## 5. New seed — One Evidence, Many Applications

Students repeatedly recreate the same factual identity and evidence across scholarship -> competition -> research programme -> recommendation -> internship/job -> study abroad.

Candidate value:
one verified factual record -> reuse in multiple legitimate workflows -> less re-entry -> fewer unsupported claims -> easier update/currentness

Consequential submissions still require explicit user review/authorization.

## 6. New seed — Official Notice -> Calendar / Action

A very small wedge can be:
notice/link/PDF -> authority/currentness -> exact dates -> prerequisites -> next action -> calendar/reminder

This is small enough for manual concierge testing and useful across almost every student domain.

## 7. New seed — Change Detection

Freshness is itself valuable.

Student saves a rule/opportunity; later the authority posts an amendment, correction, deadline extension, qualification change, or venue/system change.

The product should identify which saved users are affected.

This is stronger than a static information database.

## 8. New seed — Legitimate Appeal / Exception Evidence Pack

When a legitimate action is not recognized — for example a running record, activity credit, administrative submission, or another school-record state — the student often needs factual chronology, screenshots/receipts/logs, applicable rule, correct authority and missing evidence.

This is a high-value failure-time workflow.

Boundary: do not fabricate evidence or bypass anti-cheating/attendance controls.

## 9. Student Option Graph

The deeper object may be future option value rather than a task list.

current facts -> available future options -> requirements / lead time -> action now -> evidence produced -> new options unlocked

Example:
大创 -> research/project artifact -> competition or publication opportunity -> recommendation / internship evidence -> later career/research option

This explains why a student may value early notification even when the immediate event itself has little direct monetary value.

## 10. Source/integration difficulty ladder

### Tier 1 — public authoritative source

University public notices, official admissions/recruitment/programme pages.

Best initial surface: low integration friction and strong traceability.

### Tier 2 — public fragmented local source

Department pages, event pages, public web mirrors.

Need discovery/deduplication.

### Tier 3 — user-provided source

Forwarded notice, screenshot, PDF, exported calendar, copied group message.

Treat as user-provided until reconciled with an authority.

### Tier 4 — authenticated student portal

Requires user-authorized access, provider terms, least privilege and security.

### Tier 5 — closed group / mini-program state

Highest friction.

Initial viability should not depend on privileged access to closed systems.

This favors a public-source-first concierge MVP.

## 11. Negative-space seeds

Real student needs that currently look lower-fit for Ordivon include campus second-hand, parcel/errand service, printing/copying, local rideshare, food/group-buying, dormitory repair/logistics and hyperlocal part-time marketplaces.

Reason: their value is dominated by local supply density, transaction operations, physical fulfilment and network effects rather than reasoning/evidence. Existing templates and campus products also make implementation easy to copy.

They may become distribution/partnership surfaces, but are not obvious Ordivon beachheads.

## 12. Competitive implication

Current incumbents demonstrate that "one-stop campus app" is not an empty category:

- 到梦空间 owns much of the second-classroom record workflow;
- PU advertises 590+ partner universities and 10 million student users, and spans second classroom/employment/services;
- 超级课程表 already spans timetable, exam countdown, campus dynamics, flea market and social;
- 完美校园 spans campus card/payment/identity and employment/growth services.

Therefore residual value should not be "put more campus features in one app."

It is more plausibly the student-owned interstitial layer:
many provider systems -> what matters to me? -> what changed? -> am I eligible? -> what must happen first? -> what should I do now? -> what proves completion?

## 13. Field-test implication

Before building software, test these separately: source-backed personalized relevance, eligibility interpretation, lead-time/prerequisite warnings, graduation/obligation risk, evidence reuse, and one seasonal transition.

A raw official link and a generic AI summary should be used as controls. The product hypothesis is valuable only if source-backed personalization/actionability changes user behaviour.

## 14. Current structural hypothesis

The strongest shared composition is:
Authority / Freshness -> Opportunity or Obligation -> Personal Eligibility -> Prerequisite / Deadline Graph -> Next Action -> Evidence -> Outcome

AI remains an implementation primitive.

The business is not validated until real students act, return, and produce payer/commitment evidence.
