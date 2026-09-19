# China Student Seed Portfolio R3

Date: 2026-09-20
Status: SEED DISCOVERY / NOT MARKET VALIDATION / NOT A PRODUCT ROADMAP

## 0. Purpose

R2 established that mainland-China university students should be modeled as a fragmented life/work environment rather than a generic AI-study market.

R3 asks a narrower question:

> Which repeated structures are small enough to test now, but rich enough to grow into durable businesses if reality confirms them?

A "seed" here is not a feature. It is a small entry point that can plausibly grow a repeated user workflow, distribution loop, payer relationship, data/evidence loop and product surface.

## 1. Competitive evidence changes the question

Current products already validate several pieces of demand:

- Super Curriculum Schedule / 小应校园 / school-specific open-source apps aggregate timetable, exams, campus cards, electricity, notices and local campus services.
- PU Pocket Campus / 到梦空间 / 校友邦 prove universities will operate or purchase systems spanning second-classroom, internships, activities, credits and student growth.
- 竞观 / 创赛云 prove students seek competition discovery, deadlines, reminders, team formation and preparation resources; 创赛云 also sells competition systems and promotion to organizers.
- Seekoffer proves recommendation-exemption users value notification aggregation, material tracking, application state and deadline management.
- 实习僧 / 牛客 prove employers pay to access and process student talent while students consume jobs, preparation and community information.
- study-abroad agencies prove families will pay materially for high-stakes navigation, while some "free" models are funded by institution commissions.

Therefore:
- "information exists" is not enough;
- "one-stop" is not differentiated by itself;
- "AI" is not differentiated by itself;
- the residual must be a cross-domain personal action layer, a stronger authority/eligibility layer, an execution loop, or a new payer relationship.

## 2. Seed anatomy

For every seed inspect:

```text
entry trigger
-> repeated user action
-> data/state accumulated
-> outcome signal
-> distribution mechanism
-> payer / economic beneficiary
-> expansion adjacency
-> substitution risk
```

A seed is attractive when it can start with one narrow job without requiring university-wide integration.

## 3. Seed A — "本周与你有关" Personal Opportunity Radar

### Entry
A weekly or daily personalized digest:
- competitions;
- internships;
- scholarships;
- research programmes;
- second-classroom activities;
- exchanges;
- postgraduate/recommendation opportunities;
- selected public-recruitment opportunities.

### Core job
```text
find relevant things before I miss them
```

### Why it may work
The user does not need to learn a new AI workflow. The product pushes a tiny number of relevant, source-backed items.

### Minimal state
- university;
- major;
- year;
- location;
- goals;
- selected eligibility facts;
- previously acted/dismissed items.

### Compounding loop
```text
recommend
-> open/dismiss/save/apply
-> learn relevance
-> improve prioritization
-> more trust
```

### Expansion
Opportunity -> eligibility -> checklist -> application state -> outcome.

### Payer options
- consumer premium;
- employer/recruiter;
- event organiser;
- university/programme;
- carefully disclosed referral/lead fee.

### Risk
Becoming an ad feed destroys trust. Ranking must not secretly optimise sponsor revenue over student fit.

## 4. Seed B — Verified Eligibility Compiler

### Entry
A student asks:
- "我能不能报这个？"
- "这个岗位我符合吗？"
- "我能不能申请这个夏令营？"
- "这个奖学金我满足条件吗？"

### Core primitive
```text
official rule
+ personal facts
-> eligible / not eligible / unknown
-> explain exact rule/source
```

### Why this is deeper than search
The hard part is often not finding the notice; it is interpreting:
- major codes;
- degree/year;
- GPA/rank;
- residence;
- language score;
- competition/research prerequisites;
- prior status;
- special exceptions.

### Moat candidate
A growing library of tested rule interpretations, official-source provenance and exception patterns.

### Expansion
Eligibility -> missing prerequisites -> action plan.

### Important boundary
Unknown must remain UNKNOWN. Do not convert ambiguous institutional discretion into fake certainty.

## 5. Seed C — Deadline / Obligation Inbox

### Entry
All "must not forget" student obligations:
- class/course deadlines;
- attendance;
- exams;
- campus running;
- second-classroom;
- administrative forms;
- scholarship submissions;
- applications.

### Core job
```text
what must I do, by when, and is it done?
```

### Why it matters
Calendar apps know time. They do not naturally know:
- institutional rules;
- state;
- prerequisites;
- evidence;
- whether a run or credit was actually recognised.

### Expansion
calendar -> prerequisite graph -> state reconciliation -> exception handling.

### Distribution
Immediate utility, habit-forming, shareable among classmates.

### Risk
High notification fatigue. It must aggressively compress rather than add more alerts.

## 6. Seed D — Four-Year Option Map

### Entry
Freshman/sophomore asks:
- "我大学四年应该什么时候准备什么？"

### Product shape
Not a generic life plan. A dynamic option graph:

```text
today
-> possible future routes
   ├─ internship
   ├─ research
   ├─ competition
   ├─ recommendation exemption
   ├─ postgraduate exam
   ├─ study abroad
   ├─ public recruitment
   └─ employment
-> prerequisite windows
-> irreversible/expensive-to-delay decisions
```

### Strategic value
It converts "information asymmetry" into **option preservation**.

The strongest value claim may be:
> do not discover an important path after the preparation window has closed.

### Expansion
Opportunity Radar and Eligibility Compiler naturally plug in.

### Risk
Planning advice can become overconfident and socially coercive. Preserve multiple routes and user goals.

## 7. Seed E — Evidence Wallet / Student Achievement Ledger

### Entry
Students repeatedly recreate the same proof for:
- scholarships;
- second-classroom;
- internship;
- résumé;
- recommendation exemption;
- study abroad;
- research;
- competitions.

### Core graph
```text
claim
-> source artifact
-> issuer
-> date
-> verification
-> category
-> where it is accepted
```

Examples:
- transcript;
- competition certificate;
- research contribution;
- GitHub PR;
- project release;
- volunteer record;
- second-classroom record;
- internship evidence;
- language score.

### Why this is interesting
Current platforms often own one slice of the evidence. The student repeatedly needs the same facts in new contexts.

### Expansion
Evidence -> résumé/portfolio -> eligibility -> application material generation.

### Payer
student, university, employer, programme.

### Risk
Sensitive-data concentration. Start with user-controlled references/files, not a giant central identity database.

## 8. Seed F — Competition ROI & Team Formation

### Entry
"有哪些比赛值得参加？"

### Residual after competition aggregators
Listing alone is already crowded.

Potential residual:
```text
my goals / major / current skills
+ competition authority/recognition
+ preparation cost
+ team requirements
+ timeline
-> whether this is worth my time
```

Then:
- team-role matching;
- advisor/resource needs;
- project execution;
- outcome/evidence conversion.

### Why it compounds
Competition work can feed:
research, projects, recommendation exemption, scholarships, career portfolio and founder workflows.

### Risk
"含金量评分" can become opaque or manipulable. Prefer explicit institutional recognition and user-specific goal fit over one universal score.

## 9. Seed G — Transition Workbench

High-stakes transitions deserve their own workbench:
- 保研;
- 考研;
- 留学;
- internship/job;
- public recruitment.

Each has:
```text
target set
-> eligibility
-> materials
-> deadlines
-> application state
-> interviews/exams
-> offers/results
-> decision
```

Seekoffer is strong evidence for the 保研-specific version.

### Business logic
Students tolerate more structure and potentially more payment during short high-stakes windows than for generic daily productivity.

### Monetisation shape
Season pass may fit better than annual SaaS:
- "2027 推免季";
- "秋招季";
- "留学申请季".

### Risk
Each vertical has existing incumbents and domain-specific complexity. Do not launch all transitions simultaneously.

## 10. Seed H — Student Execution Concierge

### Entry
Student has a real project but lacks execution discipline:
- research;
- capstone;
- GitHub;
- competition;
- founder project.

### Core job
```text
turn a vague objective into completed verified work
```

### Why Ordivon fits
This is where existing Research / Engineering / Runtime / Artifact / Evidence capabilities are genuinely differentiated.

### Position
Premium, smaller audience.

### Relationship to mass utility
Mass utility can identify high-agency users who later need deeper execution.

## 11. Seed I — School Adapter Layer

Open-source campus assistants such as 四川大学“不高山上” and Fudan "旦夕/旦挞" repeatedly rebuild:
- timetable;
- exams;
- grades;
- notices;
- campus card;
- electricity;
- physical-exercise state;
- second classroom;
- local campus services.

This suggests a repeated engineering primitive:

```text
one university's fragmented systems
-> local adapter
-> normalized user-facing capabilities
```

### Important strategic warning
Do not prematurely build a universal campus integration framework.

First learn:
- which integrations are public;
- which have permitted APIs/exports;
- which require student credentials;
- which break often;
- which create security/privacy/support burden.

### Safe initial approach
Use public sources + user-provided exports/files/notifications before authenticated automation.

## 12. Seed J — Authority / Freshness Graph

Information quality is itself a product primitive.

For every consequential item:
```text
claim
-> official source
-> publication/update date
-> scope
-> superseded?
-> school-specific?
-> interpretation
-> unresolved ambiguity
```

### Why it matters
Social media creates discovery, but official sources establish consequential rules.

### Product value
Every answer can show:
- "来源";
- "更新时间";
- "适用于谁";
- "仍需确认什么".

This can differentiate from peer posts and generic chatbots.

## 13. Seed K — Peer Intelligence without Peer Rumour as Authority

Students rely heavily on:
- classmates;
- seniors;
- WeChat/QQ groups;
- Bilibili/Xiaohongshu;
- alumni/community experience.

Peer information is valuable for:
- experience;
- hidden workflow;
- timing;
- interview style;
- practical effort.

But it is weak authority for formal eligibility.

Useful separation:
```text
official fact layer
+
peer experience layer
```

Never collapse them.

### Potential network effect
Students annotate:
- "我实际遇到什么";
- "材料后来被要求补什么";
- "面试流程如何";
while official requirements remain separately sourced.

## 14. Seed L — Distribution through Existing Attention, not a New Attention Habit

Current survey evidence indicates Chinese university students concentrate heavily on WeChat and video/social platforms; social and entertainment are major phone uses.

Therefore the early distribution primitive may be:
- WeChat/QQ share cards;
- mini-program or web entry;
- class/club/community forwarding;
- calendar/reminder integration;
- "deadline card";
- "这周与你有关".

Do not require users to build a new daily habit before delivering value.

## 15. Seed M — B2B2C Student Action Network

The payer map is already visible:

```text
student wants correct opportunity/action
university wants completion / development / employment
employer wants suitable applicants
competition organiser wants qualified participants
lab/PI wants research throughput
incubator wants founder progress
```

A student-facing product can eventually monetise the beneficiary side.

### Critical rule
Paid placement must be visibly separated from neutral recommendation.

Trust is an asset; hidden pay-to-rank destroys the core product.

## 16. Seed N — Personal Outcome Graph

Most current systems stop at:
- notification;
- registration;
- application.

A longer loop records:
```text
opportunity
-> action
-> result
-> consequence
```

Examples:
- applied -> interview -> offer;
- competition -> award/no award;
- activity -> credit recognised;
- research -> accepted/rejected;
- application -> admitted;
- project -> merged/deployed.

### Why it matters
This is the learning loop needed to improve future recommendations.

### Privacy boundary
Outcome data is sensitive and must be explicitly scoped; do not assume training rights.

## 17. The strongest cross-seed composition

The most coherent mass-market chain currently looks like:

```text
Source Graph
    ↓
Opportunity / Obligation Radar
    ↓
Eligibility Compiler
    ↓
Deadline / Prerequisite Graph
    ↓
Next Action
    ↓
Evidence Wallet
    ↓
Outcome Graph
```

That is a candidate **personal action layer**.

It is not yet a product architecture commitment.

## 18. Why a chatbot is the wrong primary UI metaphor

A chatbot requires the student to:
- know what to ask;
- remember to ask;
- know which missing opportunity exists.

But information asymmetry is often about **unknown unknowns**.

A better system can proactively say:

```text
You did not ask,
but this affects you.
Here is why.
Here is the authoritative source.
Here is the deadline.
Here is the next action.
```

Chat remains useful for explanation after discovery.

## 19. Why this can work in a lower-configuration mass market

The mass-market product should optimise:

```text
minimum setup
minimum reading
minimum decisions per day
maximum source trust
maximum timing value
```

Not:
- model selection;
- prompt engineering;
- agent configuration.

## 20. Seed-to-business expansion paths

### Path 1 — consumer utility
Opportunity Radar
-> premium reminders/eligibility/workbench
-> seasonal transition products.

### Path 2 — employer / organiser-funded
Free student discovery
-> high-quality eligible candidates/participants
-> employer/organiser pays.

### Path 3 — institutional
Student utility
-> aggregate completion/outcome evidence
-> university/programme deployment.

### Path 4 — premium execution
Mass utility identifies high-agency user
-> Research / Project / Career / Founder concierge
-> higher-value service/product.

These paths may coexist but should not be activated simultaneously before demand evidence.

## 21. What could become a moat

Not the scraped list.

Potential durable advantages:

- school-specific source/adapters;
- authority/freshness history;
- eligibility edge cases;
- user action/outcome feedback;
- credential/evidence graph;
- distribution inside campus communities;
- trust from separating sponsored content and official authority;
- integration into recurring student state;
- repeated execution/evaluation assets in premium workflows.

## 22. Failure modes

### Super-app trap
Trying to launch timetable + campus card + competition + job + study abroad + research + social at once.

### Scraping trap
Mistaking a large scraped database for a product or moat.

### Notification trap
Creating another noisy feed.

### AI-wrapper trap
Selling "AI" instead of a student outcome.

### institution-first trap
Waiting for university procurement before proving student value.

### cheating trap
Optimising fake attendance/runs/graded work.

### hidden-ad trap
Selling ranking while pretending recommendations are neutral.

### prediction trap
Making opaque "上岸概率/保研概率" claims without valid evidence.

## 23. Best low-cost experiment seeds

These are not ranked market winners. They are low-cost falsifiable probes.

### Probe 1 — "本周与你有关"
For one university/major/year:
5-10 verified items/week, each with relevance reason, source, deadline and action.

### Probe 2 — "你能不能报"
Students send an opportunity notice; return source-backed eligibility analysis and unknowns.

### Probe 3 — "别漏掉"
User forwards screenshots/links/notices; system converts them to deadline/action state.

### Probe 4 — "大学四年机会地图"
One-time onboarding and option/preparation map, updated when official opportunities appear.

### Probe 5 — one transition workbench
Choose exactly one of 推免 / internship / competition and test state tracking.

## 24. Evidence needed before product build

For at least one seed, obtain repeated evidence that:

- users already experience the problem;
- users currently use a workaround;
- missed opportunities/obligations have meaningful cost;
- users trust official-source explanations;
- personalized filtering beats an information feed;
- users act on recommendations;
- users return without heavy prompting;
- one payer path is plausible;
- collection/currentness cost is operationally manageable.

Until then, stay in concierge mode.

## 25. Current R3 conclusion

The strongest conceptual seed is no longer "student AI assistant."

It is:

```text
Personal Opportunity & Obligation Action Layer
```

with two downstream branches:

```text
Mass utility
-> information / eligibility / deadline / action

Premium execution
-> research / engineering / career / founder workflows
```

This remains a hypothesis, but it explains a much larger fraction of the observed Chinese university-student environment than a generic chatbot.
