# Student Market Primitive Census R1

Date: 2026-09-20
Status: TASK-LOCAL MARKET DISCOVERY / HYPOTHESES — not a validated ICP, not an Ordivon market ontology.

## 0. Decision boundary

"University students" is a population, not yet an ICP.

The purpose of this census is to decompose student work into concrete workflows, compare them against current Ordivon capabilities and current market substitutes, and select a small number of hypotheses for real customer discovery.

Use mature external disciplines directly:

- Roger Martin Strategy Choice Cascade for where-to-play / how-to-win choices;
- Strategyzer VPC/BMC for customer/value/business-model hypotheses;
- Lean Startup for validated learning;
- ISO 20252:2026 / ICC-ESOMAR 2025 where customer-research rigor is useful;
- UNESCO human-centred GenAI guidance and institution/course policy for education-use boundaries;
- domain-native research/software/career practices for the workflow itself.

Internal architecture, capability breadth and a successful demo do not establish demand.

## 1. Current external market observations

Observed 2026-09-20 from current public sources:

- China's Ministry of Education reports 39.5396 million students in ordinary/occupational undergraduate and junior-college programmes in 2025, including 21.3577 million ordinary undergraduates.
- QS reported in June 2026 that 62% of surveyed students used GenAI at least weekly and 53% described themselves as extremely/very familiar with it.
- A 2026 empirical study covering 12,678 undergraduates at 20 Chinese universities found four materially different GenAI-use profiles; only 12.8% were classified as high-acceptance/high-critical-use "deep users", while 42% were cautious experimenters.
- Another Chinese university-student study reported use frequency highest in research activities, then course study, daily life, and further-study/job-search activities; engineering students, higher-year students, research-university students and national-competition participants used GenAI more.
- Jisc reports persistent student concerns around academic integrity, privacy, uneven policy, and unequal access to premium tools.
- Generic study support is already a highly contested layer: ChatGPT Study Mode, Gemini study notebooks/Gemini Notebook, and institution-integrated education AI all cover tutoring, quizzes, study plans, course-material grounding and progress support.
- Coding assistance is also highly commoditized for students: verified GitHub Education students can receive Copilot Student at no cost.
- Research retrieval/synthesis is crowded by Elicit, Consensus and Scite, including systematic-review support, large scholarly corpora, evidence-grounded answers, citation intelligence, APIs and MCP surfaces.
- Job discovery/matching is being absorbed by platforms: LinkedIn is rolling out AI-powered job search globally. NACE's 2025 Student Survey nevertheless found only about one-third of graduating seniors used AI in job search, with ethics, lack of expertise and detection concerns among reasons for non-use.

These observations imply that Ordivon should not enter through a generic "AI answer" surface. Candidate value must come from a longer workflow, execution/evidence, or cross-tool coordination that commodity assistants and point tools do not already own.

## 2. Student population decomposition

The first useful segmentation is by consequential workflow rather than age alone.

```text
University students
├─ Learning / assessment
├─ Research
├─ Engineering / technical projects
├─ Career / employment
├─ Further study / applications
├─ Entrepreneurship / independent building
├─ Creation / communication
└─ Student organizations / operations
```

A second segmentation cuts across those categories:

- low-agency / assignment-completion users;
- achievement-oriented course users;
- research-active students;
- engineering/project-active students;
- competition/hackathon/open-source participants;
- internship/job-search-active students;
- founders/indie builders;
- cross-domain "high-agency students" doing several consequential workflows at once.

The last four groups have the strongest preliminary fit with Ordivon's current execution/evidence substrate.

## 3. Primitive census

Ratings below are task-local discovery judgements, not a reusable scoring system.

Legend:
- Value: likely consequence to the user.
- Repeat: structural recurrence/reuse.
- Outcome: how externally/evidentially measurable the result is.
- Fit: overlap with current Ordivon capability packages.
- Pressure: substitution pressure from strong existing products; HIGH is worse.
- Integrity: academic-integrity/policy sensitivity; HIGH is worse.

| Workflow | Trigger / desired outcome | Likely user / payer | Value | Repeat | Outcome | Ordivon fit | Pressure | Integrity | Current standing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| concept tutoring | student is stuck on a concept | student | M | H | M | M | VERY HIGH | L | deprioritize |
| course-note summarization | dense notes/slides | student | L-M | H | L | M | VERY HIGH | L | deprioritize |
| quiz/flashcard generation | exam preparation | student | M | H | M | M | VERY HIGH | L | deprioritize |
| adaptive study planning | exam/deadline approaching | student / possibly institution | M-H | H | M-H | M | VERY HIGH | L | observe only |
| assignment interpretation | unclear rubric/task | student | M | H | M | M | HIGH | M | possible supporting primitive |
| graded-answer generation | assignment due | student | H to user | H | H | H | HIGH | VERY HIGH | reject as beachhead |
| integrity-safe process coaching | student must show own work | student / institution | H | H | H | H | M-H | M | candidate component |
| writing feedback / revision coaching | draft exists | student | M-H | H | M | H | VERY HIGH | M | component only |
| literature discovery | research begins | student/lab | H | H | H | H | VERY HIGH | L | buy/integrate, do not rebuild |
| evidence synthesis | research question defined | student/lab | H | H | H | H | VERY HIGH | L | buy/integrate, do not rebuild |
| research-question refinement | first research project | student/lab | H | M | M | H | M-H | L | candidate component |
| protocol / experiment design | project moves from idea to study | student/lab | VERY HIGH | M | H | VERY HIGH | M | L | strong candidate |
| research data preparation | data acquired | student/lab | H | H | H | VERY HIGH | M | L | strong candidate |
| statistical analysis | analysis stage | student/lab | VERY HIGH | H | H | VERY HIGH | M | L | strong candidate |
| computational reproducibility | results must rerun | student/lab/PI | VERY HIGH | H | VERY HIGH | VERY HIGH | M-L | L | strongest candidate |
| figure/table production | results ready | student/lab | H | H | H | VERY HIGH | M | L | strong component |
| manuscript evidence/claim check | paper drafting | student/lab | VERY HIGH | H | H | VERY HIGH | M | M | strong candidate |
| submission/rebuttal package | deadline/review received | student/lab | VERY HIGH | M | VERY HIGH | VERY HIGH | M | L | strong component |
| programming tutoring | learning code | student | M | H | H | H | VERY HIGH | M | deprioritize |
| coding task completion | assignment/project task | student | H | H | H | VERY HIGH | VERY HIGH | H | avoid graded-work wedge |
| course software project execution | team/project milestone | student/team | H | H | VERY HIGH | VERY HIGH | HIGH | M-H | candidate if authentic/project-based |
| hackathon/competition execution | event begins | team/sponsor | H | M | VERY HIGH | VERY HIGH | M-H | L-M | candidate |
| capstone engineering | final-year project | student/team/institution | VERY HIGH | M | VERY HIGH | VERY HIGH | M | M | strong candidate |
| open-source contribution | contribution goal | student/project | H | H | VERY HIGH | VERY HIGH | M-H | L | strong learning channel, weak direct payer |
| portfolio evidence packaging | applying for opportunities | student | H | M | H | VERY HIGH | H | L | candidate component |
| career/role discovery | student unsure where to aim | student/career centre | H | M | M | M | VERY HIGH | L | deprioritize |
| skill-gap mapping | target role chosen | student/career centre | H | M-H | H | H | HIGH | L | candidate component |
| resume generation | application begins | student | H | H | M-H | H | VERY HIGH | L | deprioritize |
| evidence-backed resume/portfolio | projects exist but proof is weak | student/employer/institution | VERY HIGH | M-H | H | VERY HIGH | M-H | L | strong candidate |
| job discovery/matching | active search | student | H | H | H | M | VERY HIGH | L | buy/integrate |
| application tailoring | job selected | student | H | H | H | H | VERY HIGH | L | component only |
| interview practice | interview scheduled | student | VERY HIGH | M | H | H | VERY HIGH | L | crowded |
| application outcome tracking | applications underway | student/career centre | VERY HIGH | H | VERY HIGH | H | M-H | L | strong learning-loop component |
| programme discovery | considering master's | student | VERY HIGH | L-M | M-H | H | HIGH | L | component |
| supervisor/research-fit search | research degree planning | student/lab | VERY HIGH | L-M | H | VERY HIGH | M | L | candidate |
| application-material coordination | applications underway | student | VERY HIGH | M | H | VERY HIGH | HIGH | M | possible service |
| scholarship search/fit | funding needed | student | VERY HIGH | L-M | H | H | HIGH | L | component |
| customer discovery for student founder | startup idea | founder | VERY HIGH | H | H | VERY HIGH | M | L | strong candidate, smaller segment |
| market research / competitor mapping | founder choosing market | founder | VERY HIGH | H | H | VERY HIGH | M | L | strong candidate |
| MVP/repository execution | validated need exists | founder/team | VERY HIGH | H | VERY HIGH | VERY HIGH | H | L | strong candidate |
| founder-led outreach/sales ops | offer exists | founder/team | VERY HIGH | H | VERY HIGH | H | M-H | L | candidate |
| pitch/report/presentation production | demo/deadline | student/team | H | H | H | VERY HIGH | HIGH | L | component |
| club/event operations | recurring student org work | club | M | H | H | H | M-H | L | testable but payer weak |

## 4. Immediate eliminations

### 4.1 Generic study assistant

Do not make this the beachhead.

Reason:
- ChatGPT Study Mode already guides learning, quizzes, explains material and works with uploads.
- Google's 2026 study notebooks/Gemini Notebook already provide diagnostic quizzes, adaptive lessons, course-material grounding, flashcards, quizzes and institution integrations.
- price pressure is severe because strong alternatives are free or institution-provided.

Ordivon may consume these products as primitives where useful; it should not recreate them.

### 4.2 Generic coding assistant

Do not make this the beachhead.

Reason:
- verified students can receive GitHub Copilot Student free;
- coding completion itself is rapidly commoditized;
- graded programming work also creates academic-integrity risk.

Potential residual value is project-level engineering evidence: requirements -> repo -> implementation -> tests -> deployment/artifact -> demonstrable outcome.

### 4.3 Literature-search assistant

Do not make this the beachhead.

Reason:
- Elicit, Consensus and Scite own strong research-retrieval/evidence primitives;
- Elicit exposes API/MCP and reproducible systematic-review support;
- Scite exposes MCP/API and citation-context intelligence;
- Consensus has large-scale research search/synthesis and student/researcher use.

Ordivon should integrate these where appropriate. The residual opportunity is what happens after/beside retrieval: research design, experiments, data, reproducibility, claims, artifacts, submission and feedback.

### 4.4 Resume generator / generic job search

Do not make this the beachhead.

Reason:
- LinkedIn now exposes AI-powered natural-language job search and job-match surfaces;
- career centres are increasingly using AI;
- commodity LLMs already produce resumes/cover letters/interview questions.

Residual opportunity may be project-evidence -> skills -> application -> interview -> offer feedback, not document generation.

## 5. Shortlist after substitution

### Candidate A — Student Research Execution & Reproducibility

Initial ICP hypothesis:

> Research-active technical undergraduates / early master's students who already have a concrete research project but lack a reliable end-to-end process from research question and protocol through computation, evidence, figures and submission-ready artifacts.

Core workflow:

```text
question
-> literature primitives from mature research providers
-> protocol / experiment design
-> data / code identity
-> execution
-> statistical analysis
-> reproducibility
-> figures/tables
-> claim-evidence check
-> manuscript / poster / rebuttal artifacts
-> independent review / acceptance
```

Why it survives:
- local Ordivon Research, Engineering, Data, Runtime, Artifact and evidence capabilities already cover much of the long chain;
- current research competitors are strongest at retrieval/synthesis, leaving substantial downstream project work;
- outcomes can be checked: runs reproduce, analysis is valid, artifacts compile, advisor/reviewer findings exist;
- the workflow produces high-quality correction/evaluation traces;
- research-active students are a narrower, higher-agency segment than all students.

Main risks:
- willingness to pay may still be limited;
- research method differs by discipline;
- misuse must not become ghostwriting/fabrication;
- long outcome horizon for publication;
- existing labs/advisors may be the real payer/authority.

### Candidate B — Technical Project / Capstone Execution Evidence

Initial ICP hypothesis:

> CS/software/engineering students doing a consequential capstone, competition, hackathon, open-source or portfolio project where a working, tested, explainable artifact matters more than generated code.

Core workflow:

```text
requirements
-> architecture
-> repo plan
-> implementation
-> tests / security / dependencies
-> build/deploy
-> demo
-> evidence
-> report/presentation
-> retrospective
```

Why it survives:
- generic coding is commoditized, but project completion/verification is not identical to autocomplete;
- Ordivon Engineering + Security + Runtime + Artifact map naturally;
- outcome is observable;
- project evidence can later feed career workflows.

Main risks:
- course projects can cross academic-integrity boundaries;
- GitHub/Copilot and agentic coding systems can move upstream quickly;
- student payer is weak;
- project types are heterogeneous.

### Candidate C — Evidence-backed Technical Career Transition

Initial ICP hypothesis:

> Technical students with real projects/research but weak translation of that evidence into target-role skills, portfolio proof, application decisions and interview stories.

Core workflow:

```text
project/research evidence
-> verified skills/claims
-> target role requirements
-> gap map
-> portfolio/resume evidence
-> selected applications
-> interview evidence
-> outcome tracking
-> correction
```

Why it survives:
- direct outcome loop is unusually strong: recruiter response, interview, offer;
- Ordivon can use source evidence rather than fabricate résumé claims;
- links naturally to Research and Engineering workflows.

Main risks:
- LinkedIn/Handshake/career platforms own distribution and job data;
- consumer career tooling is crowded;
- seasonal workflow;
- outcomes have large confounders.

### Candidate D — Student Founder / Indie Builder Execution

Initial ICP hypothesis:

> technically capable student founders/indie builders who can build but lack repeatable customer-discovery, market-research, bounded delivery and commercialization execution.

Core workflow:

```text
problem hypothesis
-> customer discovery
-> market evidence
-> offer
-> MVP
-> outreach
-> paid pilot
-> delivery/economics
-> repeat/pivot
```

Why it survives:
- very high fit with Ordivon's current internal commercialization work;
- outcomes are real and economic;
- high-agency users;
- strong learning loop.

Main risks:
- small/volatile segment;
- many users have zero budget;
- startup outcomes are noisy and long-tailed;
- direct services may be more viable than software initially.

## 6. Current comparison

No overall winner is claimed yet; these are hypotheses requiring market evidence.

| Dimension | Research execution | Technical project | Career evidence | Student founder |
| --- | --- | --- | --- | --- |
| current Ordivon capability fit | VERY HIGH | VERY HIGH | HIGH | VERY HIGH |
| commodity substitution pressure | MEDIUM | HIGH | HIGH | MEDIUM |
| outcome observability | HIGH | VERY HIGH | VERY HIGH | VERY HIGH |
| repeatable execution structure | HIGH | HIGH | MEDIUM-HIGH | HIGH |
| direct student willingness-to-pay uncertainty | HIGH | HIGH | MEDIUM-HIGH | HIGH |
| plausible non-student payer | lab/PI/program | school/sponsor/employer | university/employer | incubator/program |
| integrity/policy sensitivity | MEDIUM | MEDIUM-HIGH | LOW | LOW |
| likely learning-loop quality | VERY HIGH | HIGH | VERY HIGH | VERY HIGH |

## 7. User != payer possibilities

Do not assume the student must be the final buyer.

| User | Possible payer / beneficiary | Why payer may care |
| --- | --- | --- |
| research student | PI/lab/research programme/university | reproducibility, throughput, research quality |
| capstone/project student | department/programme/competition sponsor/employer | demonstrable skills, completion, employability |
| job seeker | university career centre/employer/training programme | placement outcomes, candidate quality |
| student founder | incubator/accelerator/programme | venture progress and measurable execution |

This B2B2C route is important because student price sensitivity is structurally high.

## 8. Academic-integrity boundary

Ordivon must not define one global "allowed AI" rule.

For any course/assessment workflow:

```text
institution/course/instructor policy
-> exact assignment/assessment context
-> permitted vs prohibited assistance
-> disclosure/citation requirements
-> student-authored work / evidence
```

Where the policy is ambiguous, preserve ambiguity and ask the relevant academic authority rather than silently completing assessed work.

The safer strategic direction is authentic learning/project/research workflow support rather than answer substitution. UNESCO's guidance emphasizes human-centred, safe and meaningful use; current higher-education integrity work increasingly emphasizes transparent use, authentic assessment and assurance of learning.

## 9. Learning-rights boundary

Student context is not automatically reusable training data.

For every experiment distinguish:
- direct service processing;
- account/project history;
- execution logs;
- human corrections;
- acceptance/rejection;
- downstream outcomes;
- de-identified aggregate analytics;
- benchmark/evaluation use;
- product-improvement use;
- model-training/fine-tuning use;
- research/publication use.

The initial discovery programme should avoid sensitive/unnecessary collection and make consent/use explicit.

## 10. Ordivon capability mapping

Current local capability packages already provide useful primitives:

- Research: question/scope, literature workflow, experimental design, statistics, reproducibility, scientific writing/review;
- Engineering: requirements, architecture, implementation, testing, integration/release;
- Security: code/dependency/supply-chain evidence;
- Data & Analytics: ingest, quality, analysis, visualization, lineage;
- Artifact: validated documents, figures, presentations and packages;
- Runtime: exact bounded execution evidence;
- Distribution: publication/provider effects when authorized;
- Business Operations: natural CRM/ERP/accounting owners only when real transactions exist.

Therefore the beachhead experiment should compose these existing capabilities. Do not create a Student v2 platform or education-specific runtime before repeated external demand shows an actual residual capability gap.

## 11. What evidence would change our mind?

Promote a candidate only if customer discovery shows several of these repeatedly:
- same user/buyer class;
- same costly trigger;
- existing spend/time loss;
- real workaround already exists;
- buyer can describe a concrete desired outcome;
- a bounded offer is understandable without explaining Ordivon architecture;
- willingness to commit time, data, introduction, pilot or money;
- repeated workflow structure across respondents;
- policy/rights boundary can be made workable.

Kill or narrow a candidate when:
- users say the problem is interesting but do not currently spend time/money;
- free general AI fully satisfies the job;
- the real buyer is unreachable;
- value depends on doing prohibited assessed work;
- every engagement is structurally unrelated;
- outcome cannot be observed;
- access/privacy/rights make the learning loop impossible.

## 12. Current strategic standing

```text
University-student population       DISCOVERY_SURFACE
Validated student ICP               NONE
Validated beachhead workflow        NONE
Validated payer                     NONE
Paid pilot                          NONE
Repeat-work evidence                NONE
Outcome corpus                      NONE
Learning-rights proof               NONE
```

The shortlist for evidence collection is:

1. student research execution/reproducibility;
2. technical project/capstone execution evidence;
3. evidence-backed technical career transition;
4. student founder/indie-builder execution.

This ordering is a discovery sequence based on current Ordivon capability overlap and substitution analysis, not market validation.

## 13. Current external references

- Ministry of Education PRC, 2025 National Education Development Statistical Bulletin: https://www.moe.gov.cn/jyb_sjzl/sjzl_fztjgb/202607/t20260706_1442870.html
- QS, Generative AI in Higher Education, 2026: https://www.qs.com/insights/generative-ai-higher-education-academic-student-perspectives
- Ma et al., survey of 12,678 undergraduates at 20 Chinese universities, 2026: https://xbjk.ecnu.edu.cn/CN/10.16382/j.cnki.1000-5560.2026.01.006
- Jisc, Student perceptions of AI 2025: https://www.jisc.ac.uk/reports/student-perceptions-of-ai-2025
- UNESCO, Guidance for generative AI in education and research: https://www.unesco.org/en/articles/guidance-generative-ai-education-and-research
- OpenAI, Study Mode: https://help.openai.com/en/articles/11780217-using-study-mode-in-chatgpt
- Google Education / Gemini study notebooks: https://blog.google/products-and-platforms/products/education/iste-students-2026/
- GitHub Education / Copilot Student: https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/enable-copilot/set-up-for-students
- Elicit: https://elicit.com/
- Consensus: https://consensus.app/
- Scite: https://scite.ai/
- LinkedIn AI-powered job search: https://www.linkedin.com/help/linkedin/answer/a6889044
- NACE, student AI use in job search, 2026 article based on 2025 survey: https://www.naceweb.org/job-market/trends-and-predictions/student-concerns-about-ai-tempering-their-use-of-it-in-job-search
