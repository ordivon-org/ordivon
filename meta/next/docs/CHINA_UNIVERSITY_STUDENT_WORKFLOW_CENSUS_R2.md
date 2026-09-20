# China University Student Workflow Census R2

Date: 2026-09-20
Status: CHINA-SPECIFIC MARKET DISCOVERY / HYPOTHESES — not a validated ICP and not a private Ordivon education ontology.

## 0. Why R2 exists

R1 over-weighted high-agency research/engineering/career users and under-modeled the ordinary mainland-China university experience.

China-specific student demand is not only "learn better" or "use stronger AI." It includes a large amount of institution-shaped, deadline-shaped and information-shaped work:

- course attendance and classroom systems;
- PE running / physical-education requirements;
- second-classroom activities and credits;
- competitions;
- scholarships, honours, certificates and volunteer records;
- internship and employment information;
- postgraduate entrance examination;
- recommendation/exemption ("推免/保研");
- civil-service and public-institution recruitment;
- study-abroad and credential/visa/application information;
- research, capstones, GitHub/open-source projects;
- club/social/event participation and ordinary campus administration.

This R2 therefore treats the market as a **student-life workflow environment**, not an "AI study assistant" market.

## 1. Current China context

### 1.1 Scale

The Ministry of Education reports 39.5396 million students in ordinary/occupational undergraduate and junior-college programmes in 2025, including 21.3577 million ordinary undergraduates.

That is a very large user population, but population size alone does not establish willingness to pay.

### 1.2 The student is highly online, but global-AI access cannot be assumed

CNNIC reports that by the end of 2025:
- China had 1.125 billion internet users and 80.1% internet penetration;
- generative-AI users reached 602 million, or 42.8% of internet users.

This proves broad domestic internet/GenAI adoption. It does **not** prove routine access to global web/AI services.

Current provider reality matters:
- OpenAI's current supported-country list does not list mainland China; OpenAI warns that access from unsupported regions may lead to blocking/suspension.
- Google's Gemini web-app list says "Mainland China (Workspace only)", and the consumer mobile availability list does not list mainland China.

Therefore a China-student product must not assume:
- ChatGPT account/payment availability;
- Google consumer services;
- stable access to every foreign site/API;
- English-first UX;
- students knowing how to compose specialist AI/research/dev tools.

"Use the best global AI product" is not a complete local-market answer.

### 1.3 AI sophistication is heterogeneous

A 2026 survey of 12,678 undergraduates at 20 Chinese universities found four materially different GenAI-use profiles:
- cautious experimenters 42%;
- labour substitutes 24%;
- balanced explorers 21.2%;
- deep users 12.8%.

This supports a key design implication:
most of the market should not be modeled as expert agent users.

The product should work for people who think in terms of:
"what do I need to do next?"
rather than:
"which model/tool/agent/MCP should I invoke?"

### 1.4 "Down-market" should be interpreted operationally, not as a value judgment

For market design, the useful characteristics are:

- very large population;
- high price sensitivity;
- mobile-first behaviour;
- preference for low-configuration convenience;
- local-platform dependence;
- strong peer/social distribution;
- uneven information access;
- frequent deadline/eligibility constraints;
- many one-off high-stakes transitions;
- limited tolerance for complex professional tooling.

This makes the market structurally different from enterprise SaaS and from globally connected power users.

## 2. The China-student operating environment

A realistic student does not live in one product.

A typical environment may include combinations of:

```text
university portal / 教务系统
course platform
雨课堂 / 学习通 / other teaching systems
今日校园 / local campus app
到梦空间 / second-classroom system
步道乐跑 / PE platform
WeChat groups / public accounts
QQ groups
school/department websites
counsellor/class-group notices
competition websites
研招网
推免服务系统
国家大学生就业服务平台
employer recruitment sites
government / public-institution recruitment sites
study-abroad university/agency/credential sites
GitHub / Gitee / coding platforms
Bilibili / Xiaohongshu / Zhihu / Douyin and peer content
AI chatbots
```

The strategic opportunity may therefore be **cross-system orientation and execution**, not another content database.

## 3. Domain census

### A. Course / classroom operations

Primitive workflows:

- timetable ingestion and change awareness;
- attendance/sign-in reminder;
- classroom/location/time confirmation;
- rain-classroom or other platform participation;
- assignment/rubric collection;
- deadline aggregation;
- submission confirmation;
- grade/review notification;
- absence/exception evidence and appeal preparation;
- course-policy / AI-policy capture.

Current evidence:
Rain Classroom's student flow includes account binding, attendance/sign-in, question answering, submissions and after-class records.

Potential value:
- "what must I do today?"
- avoid missed attendance/deadlines;
- unify fragmented course requirements.

Boundary:
Do not build attendance spoofing, proxy sign-in, fake location, or mechanisms that misrepresent physical/class participation.

### B. Physical education / campus running

Primitive workflows:

- semester running requirement discovery;
- valid zone/rule discovery;
- run scheduling;
- progress tracking;
- valid/invalid-run reconciliation;
- GPS/device troubleshooting;
- exception/competition exemption workflow;
- deadline warning;
- evidence for legitimate appeal.

Current evidence:
"步道乐跑" markets itself as a campus smart-sports platform used by 600+ universities, including anti-cheating running, physical testing, course management and venues. A 2026 university notice shows campus long-run requirements can be compulsory for multiple year groups and depend on valid zones/checkpoints.

Potential value:
high-frequency, concrete, low-complexity student pain.

Boundary:
No GPS spoofing, fake runs, anti-cheat bypass or fraudulent completion. The legitimate wedge is planning, reminders, reconciliation and exception handling.

### C. Second classroom / activity credits

Primitive workflows:

- activity discovery;
- eligibility matching;
- registration deadline;
- capacity/lottery awareness;
- sign-in/participation;
- evidence upload;
- credit/category accounting;
- missing-credit reconciliation;
- graduation/award threshold tracking;
- transcript generation;
- activity-to-career evidence extraction.

Current evidence:
The Ministry of Education / CYL second-classroom framework explicitly covers innovation/entrepreneurship, social practice, volunteer work, interests and social participation, with participation records used in comprehensive evaluation. "到梦空间" supports activity publication, registration, sign-in, credits and second-classroom transcripts; its service pages describe university integration and data interfaces.

Potential value:
This is a highly China-specific institutional workflow and much closer to "student operations" than generic learning AI.

### D. Competition intelligence

Primitive workflows:

- discover competitions relevant to major/year/skills;
- distinguish official/high-value competition from marketing noise;
- registration window;
- school-level internal selection;
- team requirement;
- advisor requirement;
- materials/template;
- competition timeline;
- prior winning works / rubric;
- project execution;
- submission proof;
- result/certificate;
- credit/second-classroom/scholarship mapping;
- portfolio conversion.

Current evidence:
Chinese universities commonly rely on the China Association of Higher Education competition-analysis catalogue and school-maintained calendars. University teaching offices publish month-by-month competition lists specifically to help students plan participation.

Key pain hypothesis:
students often learn about opportunities from classmates, counsellors or scattered groups **after** the optimal preparation window has passed.

This is a strong information-asymmetry candidate.

### E. Internship / graduate-employment intelligence

Primitive workflows:

- role/opportunity discovery;
- eligibility extraction;
- location / major / graduation-year matching;
- application deadline;
- company verification;
- application-material readiness;
- application state;
- interview schedule;
- offer comparison;
- internship-to-return-offer tracking.

Current evidence:
The Ministry of Education's National College Student Employment Service Platform currently exposes dedicated internship listings and warns students to verify employer/job authenticity and protect personal information.

Opportunity:
not "write my résumé", but:
```text
trusted opportunity
-> am I eligible?
-> what is the deadline?
-> what must I prepare?
-> have I applied?
-> what happened?
```

### F. Postgraduate entrance examination (考研)

Primitive workflows:

- school/programme discovery;
- exact current admission policy;
- subject combination;
- syllabus/reference materials;
- past admission/retest information;
- registration eligibility;
- registration-point constraints;
- timeline;
- exam plan;
- score/retest;
- adjustment/调剂;
- document/checklist.

Current evidence:
The Ministry of Education / China Graduate Admissions Information Network publishes annual rules, programme information and the national application/adjustment systems. Current rules require institutions to publish programme-specific admission conditions and procedures.

Opportunity:
the hard part is not generic test tutoring alone. It is keeping current:
```text
policy + programme + eligibility + deadline + evidence + decision
```

### G. Recommendation / exemption (保研 / 推免)

Primitive workflows:

- home-university eligibility calculation;
- GPA/rank/course requirements;
- research/competition/activity evidence;
- summer-camp / pre-recommendation opportunity discovery;
- target-school programme rules;
- application windows;
- material checklist;
- interview;
- official recommendation status;
- parallel choices;
- acceptance decision;
- official system confirmation.

Current evidence:
The national 推免 system is the unified platform for qualification confirmation, applications, offers and final records. For 2027 recommendation, the platform states students begin personal-data registration from 2026-09-18 and applications run through the official system.

This is an archetypal information-fragmentation + deadline + evidence workflow.

### H. Study abroad

Primitive workflows:

- country/programme discovery;
- entry requirements;
- GPA/language/test mapping;
- tuition/living cost;
- scholarship;
- supervisor/lab fit;
- application timeline;
- statement/CV/reference workflow;
- document authentication;
- offer comparison;
- visa;
- credential recognition;
- return/employment implications.

Current evidence:
China Service Center for Scholarly Exchange runs official online services for overseas-degree recognition, employment reporting, study records and public-study-abroad services.

Opportunity:
"留学信息差" is not one problem. It is a long decision chain with high information cost and high commercial conflict-of-interest risk.

Product principle:
official-source-first; clearly separate neutral decision support from paid agency/referral economics.

### I. Civil service (考公) / public institution (考编)

Primitive workflows:

- opportunity discovery;
- central/provincial/local route;
- position table parsing;
- major-code/degree/graduate-status eligibility;
- household/residency/age/experience constraints where applicable;
- deadline;
- document preparation;
- exam plan;
- qualification review;
- interview/physical/medical steps;
- result tracking.

Current evidence:
public-institution recruitment notices show highly structured, position-specific eligibility and application procedures, with special conditions for current/recent graduates.

Opportunity:
This is a **rules + eligibility + deadline** problem, not merely a content-learning problem.

Boundary:
Provide neutral procedural information and official-source traceability; do not make political advocacy or ideological recommendations.

### J. Scholarships / honours / awards / certificates

Primitive workflows:

- discover opportunity;
- map eligibility;
- required GPA/rank/financial or activity conditions;
- material checklist;
- nomination/approval chain;
- deadlines;
- proof;
- status;
- result;
- future reuse of the evidence.

These often share infrastructure with competition, second-classroom and academic-record workflows.

### K. Research

Retain the R1 long-chain research workflow:
question -> literature -> protocol -> experiment -> data/code -> analysis -> reproducibility -> figures -> claims -> manuscript -> submission/review.

China-specific additions:
- advisor/lab hierarchy;
- domestic academic platforms;
- school innovation projects;
- undergraduate research programmes;
- competition/research overlap;
- scholarship/推免 linkage;
- local-access constraints for foreign research/AI services.

### L. GitHub / open-source / technical projects

Primitive workflows:
- opportunity/project discovery;
- environment setup;
- issue selection;
- contribution;
- tests;
- PR;
- maintainer feedback;
- merge;
- portfolio evidence;
- competition/research/job linkage.

Important China-specific friction:
Do not assume every student has stable, skilled access to GitHub/global developer tooling. Where mature domestic alternatives or mirrors are needed, treat them as provider choices rather than forcing one global dependency.

### M. Social / love / games / clubs / attention

These are not dismissed as "unproductive." They matter because they consume attention and shape distribution.

Market implications:
- a tool requiring daily disciplined configuration will lose against entertainment/social habits;
- notifications, peer proof, deadlines and immediate utility may outperform "learn agent workflows";
- campus clubs/communities can become acquisition channels;
- relationship/mental-health/life-advice is a different safety and trust domain and should not be silently mixed into academic/career workflow products;
- game/social usage competes for time, so product time-to-value must be short.

## 4. Cross-domain primitive: Information Asymmetry

The user's added examples expose one repeated structure:

```text
important opportunity / obligation exists
        ↓
information is fragmented across official sites,
school pages, public accounts, groups and peers
        ↓
student may not know it exists
        ↓
eligibility is difficult to interpret
        ↓
deadline/materials are easy to miss
        ↓
late discovery destroys option value
```

This repeats across:

- competitions;
- internships;
- 推免;
- 考研;
- 留学;
- 考公;
- 考编;
- scholarships;
- second-classroom activities;
- research programmes;
- exchange programmes;
- certificates;
- campus administrative tasks.

This is substantially broader than the R1 "high-agency technical student" thesis.

## 5. Candidate product primitive: Opportunity Graph, not "AI chatbot"

A useful local composition could be:

```text
official / school / provider sources
        ↓
source identity + currentness
        ↓
event / opportunity extraction
        ↓
eligibility rules
        ↓
student profile facts
        ↓
match / mismatch / unknown
        ↓
deadline and prerequisite graph
        ↓
action checklist
        ↓
reminders
        ↓
application / participation evidence
        ↓
result / outcome
```

The user interaction should often be:
- "这些与你有关";
- "你缺这个材料";
- "三天后截止";
- "这个规则来自这里";
- "你不确定这一条，需要问学院";
- "你已经报名，但还没有提交材料";

rather than:
- "Ask me anything."

That is a fundamentally different product posture.

## 6. China-specific design constraints

### 6.1 Local-first availability

Do not make product function depend on unsupported/unreliable global consumer services.

Prefer:
- accessible domestic model/provider paths where needed;
- official Chinese websites and school/provider sources;
- graceful fallback when a foreign source is unavailable;
- cached/source-identity evidence where legally allowed;
- Chinese-language primary UX.

### 6.2 Mobile-first, low-configuration

Assume many users:
- will not install developer tooling;
- will not understand agents/MCP;
- will not maintain workflows manually;
- will not read long setup guides.

The product should convert complexity into:
```text
discover -> tell me why it matters -> tell me what to do -> prove source -> remind me
```

### 6.3 Official-source hierarchy

For consequential eligibility/admission/recruitment rules:
```text
official national/provincial/institution source
> school/department official notice
> provider-native system
> reputable secondary explanation
> social post / peer message
```

Social sources are discovery signals, not final authority.

### 6.4 Price sensitivity

Do not assume enterprise SaaS pricing.

Test:
- free discovery/basic reminders;
- low-price premium workflow;
- event/season pass;
- university/programme sponsorship;
- employer/lab/incubator B2B2C;
- carefully disclosed referral economics only where conflicts can be managed.

No model is validated yet.

## 7. Revised candidate families

R2 expands R1 from 4 to 8 evidence families.

### Family 1 — Student Opportunity Intelligence
Competitions + scholarships + research programmes + internships + exchanges + second-classroom opportunities.

Core residual:
```text
discover + verify + eligibility + deadline + action
```

### Family 2 — Campus Obligation Assistant
Attendance reminders, course deadlines, campus running requirements, second-classroom credit status, administrative tasks.

Core residual:
```text
obligation + rule + state + deadline + legitimate evidence
```

No spoofing/proxy-completion.

### Family 3 — Postgraduate / Recommendation Navigation
考研 + 推免/保研.

Core residual:
```text
official rules + personal eligibility + target programme + timeline + evidence
```

### Family 4 — Employment / Public Recruitment Navigation
Internships + graduate jobs + 考公 + 考编.

Core residual:
```text
opportunity + eligibility + materials + deadline + outcome
```

### Family 5 — Study-Abroad Decision & Application Navigation
Official-source-first programme/requirement/cost/scholarship/application/credential workflow.

### Family 6 — Student Research Execution & Reproducibility
Retained from R1.

### Family 7 — Technical Project / GitHub / Competition Execution
Retained and expanded from R1.

### Family 8 — Student Founder / High-agency Execution
Retained from R1 as a smaller premium segment.

## 8. Two very different market layers

This is the key R2 insight.

### Layer A — Mass student utility

Characteristics:
- huge population;
- low willingness to configure;
- lower ARPU;
- frequent simple pains;
- fragmented information;
- deadlines;
- strong mobile/social distribution.

Likely products:
Opportunity Intelligence + Campus Obligations + Education/Career Navigation.

### Layer B — High-agency premium workflows

Characteristics:
- smaller population;
- complex work;
- higher outcome value;
- higher willingness to invest time/money;
- more Ordivon execution capabilities relevant.

Likely products/services:
Research Execution + Technical Projects + Career Evidence + Student Founder workflows.

These layers can coexist:

```text
Mass utility
    ↓ discovers / earns trust / distribution
High-agency workflows
    ↓ deeper value / monetization / learning
B2B2C institutional payer
```

This is a stronger hypothesis than choosing only one stereotypical "college student."

## 9. What not to build

Do not build:

- generic AI chatbot;
- generic tutoring bot;
- another résumé generator;
- another competition content website with copied lists;
- fake check-in / GPS spoofing / campus-run cheating;
- automated completion of prohibited assessed work;
- opaque "保研成功率"/"考公上岸率" predictions;
- untraceable policy answers;
- an Ordivon Student ontology/runtime before demand exists.

## 10. New strategic hypothesis

The China-specific wedge may be less about "AI intelligence" and more about:

```text
information advantage
+ rule understanding
+ deadline memory
+ cross-platform state
+ evidence-backed action
```

In compact form:

```text
Student Life
-> Events / Obligations / Opportunities
-> Verified Rules
-> Personal Eligibility
-> Action Graph
-> Deadline
-> Evidence
-> Outcome
```

AI is an implementation primitive, not the product identity.

## 11. Evidence standing

Current:

```text
China student population size        ESTABLISHED
Domestic internet/GenAI scale        ESTABLISHED
Student AI heterogeneity             ESTABLISHED
Campus platform fragmentation        STRONGLY INDICATED
Second-classroom institutional flow  ESTABLISHED
Campus-run institutional flow        ESTABLISHED IN EXAMPLES / PROVIDER
Internship official platform         ESTABLISHED
研招 / 推免 official systems          ESTABLISHED
Global-AI availability constraints   ESTABLISHED AT PROVIDER LEVEL
"most students rarely access foreign internet" USER FIELD HYPOTHESIS, NOT YET POPULATION-VALIDATED
Student willingness to pay           UNVALIDATED
Best beachhead                       UNVALIDATED
Best payer                            UNVALIDATED
```

Do not upgrade the user's field observation about foreign-internet use into a population statistic without proper evidence.

## 12. External references

- Ministry of Education, 2025 national education statistics.
- CNNIC, 57th Statistical Report on China's Internet Development, 2026.
- 2026 empirical survey of 12,678 Chinese undergraduates on GenAI use.
- OpenAI supported-country and unsupported-region guidance.
- Google Gemini supported-country guidance.
- Ministry of Education / CYL second-classroom policy.
- 到梦空间 product/service documentation.
- 步道乐跑 product information and university implementation notices.
- Rain Classroom student guide.
- National College Student Employment Service Platform.
- China Graduate Admissions Information Network and 推免 system.
- China Service Center for Scholarly Exchange.
- current public-institution recruitment notices and natural government recruitment authorities.
