# GitHub Global Top-100 Capability Radar R2

Status: **CURRENT SNAPSHOT + R1 CLASSIFICATION CARRY-FORWARD**
Snapshot: **2026-10-31**
Supersedes for current discovery only: github-top100-capability-radar-r1.md. R1 remains immutable historical evidence.

## 1. Source and ranking method

- Primary source: GitHub Search API query stars:>100000, sorted by stars desc, per_page=100, observed 2026-10-31.
- GitHub reported **137 repositories above 100k stars** and returned the requested top 100.
- Repository identity is the join key. Existing R1 decisions are carried forward only for repositories that remain in the top 100; this refresh does not re-prove every old architectural judgment.
- Star count is a volatile discovery/community signal, never an acceptance, security, maintenance, license-compliance or correctness proof.

## 2. R1 → R2 membership delta

- Entered: **morluto/rea** at current rank **5**, observed **413,016 stars** in the ranking capture. Direct follow-up observation changed slightly later, illustrating star-count volatility.
- Exited from top 100: **mrdoob/three.js** (R1 rank 99). This is a ranking exit, not a provider retirement; its prior ON_DEMAND judgment remains historical and workload-specific.
- R1 reported 127 repositories above 100k; R2 reports **137**.

## 3. Decision counts in the current top 100

- **DEEP_STUDY: 10**
- **TARGETED_COMPARE: 4**
- **ABSORB_METHOD: 8**
- **ALREADY_COVERED: 13**
- **ALREADY_SUBSTRATE: 2**
- **ON_DEMAND: 20**
- **DISCOVERY_SOURCE: 10**
- **REFERENCE_ONLY: 14**
- **NO_ACTION: 17**
- **STUDIED_AVOID: 2**

morluto/rea is classified **DEEP_STUDY** because it is a new, extremely high-star and actively released evidence-oriented reverse-engineering MCP/CLI. Its young age and unusually fast popularity growth are reasons for deeper falsification, not shortcuts around it.

## 4. Full current Top-100

| # | Repository | Stars | License | Domain | Decision | Ordivon judgement |
|---:|---|---:|---|---|---|---|
| 1 | `codecrafters-io/build-your-own-x` | 557,688 | — | Knowledge / learning | **REFERENCE_ONLY** | Useful for prototype understanding; conflicts with build-last if treated as implementation strategy. |
| 2 | `sindresorhus/awesome` | 527,618 | CC0-1.0 | Discovery catalog | **DISCOVERY_SOURCE** | Broad discovery index; useful for finding mature projects, not an authority itself. |
| 3 | `public-apis/public-apis` | 493,597 | MIT | Discovery catalog / APIs | **DISCOVERY_SOURCE** | Useful API discovery source before writing adapters. |
| 4 | `freeCodeCamp/freeCodeCamp` | 458,257 | BSD-3-Clause | Education | **NO_ACTION** | Learning platform; no Ordivon capability gap. |
| 5 | `morluto/rea` | 413,016 | MIT | Reverse engineering / Agent tooling | **DEEP_STUDY** | New high-star active entrant: evidence-oriented MCP/CLI reverse-engineering provider. Deep-study provider boundaries and provenance; young/rapid star growth means popularity must not be treated as maturity proof. |
| 6 | `EbookFoundation/free-programming-books` | 400,562 | CC-BY-4.0 | Education / knowledge | **REFERENCE_ONLY** | Human learning/reference corpus; not an execution provider. |
| 7 | `openclaw/openclaw` | 393,501 | MIT | Agent harness / personal agent platform | **DEEP_STUDY** | High-value full agent runtime, skills, sessions, plugins and messaging surface; compare with Runtime/Codex/Hermes. |
| 8 | `donnemartin/system-design-primer` | 376,269 | NOASSERTION | Engineering knowledge | **REFERENCE_ONLY** | Useful systems-design reference, but not authoritative architecture or provider. |
| 9 | `nilbuild/developer-roadmap` | 370,840 | NOASSERTION | Education | **NO_ACTION** | Career learning roadmap, not a capability provider. |
| 10 | `jwasham/coding-interview-university` | 363,604 | CC-BY-SA-4.0 | Education | **NO_ACTION** | Interview curriculum; unrelated to Ordivon architecture. |
| 11 | `awesome-selfhosted/awesome-selfhosted` | 332,221 | NOASSERTION | Discovery catalog / self-hosting | **DISCOVERY_SOURCE** | Useful source for mature self-hostable products before custom building. |
| 12 | `vinta/awesome-python` | 331,454 | NOASSERTION | Discovery catalog | **DISCOVERY_SOURCE** | Useful Python provider/library discovery source. |
| 13 | `obra/superpowers` | 309,558 | MIT | Engineering methodology / Skills | **ALREADY_COVERED** | Batch 1 completed; retain selected engineering discipline, no new platform. |
| 14 | `mattpocock/skills` | 307,642 | MIT | Agent Skills content | **ABSORB_METHOD** | Mine high-quality reusable engineering Skills; Agent Skills primitive already understood. |
| 15 | `affaan-m/ECC` | 293,533 | MIT | Agent harness methodology / memory / eval | **DEEP_STUDY** | Combines skills, agents, memory, security, eval and learning across harnesses; potentially useful composition lessons. |
| 16 | `practical-tutorials/project-based-learning` | 288,518 | MIT | Education | **NO_ACTION** | Tutorial catalog; no capability gap. |
| 17 | `996icu/996.ICU` | 277,197 | NOASSERTION | Community / social | **NO_ACTION** | Not an Ordivon technical/provider capability. |
| 18 | `deepseek-ai/deepseek-harness` | 266,888 | MIT | Agent harness / plugin runtime | **DEEP_STUDY** | Everything-is-plugin + reversible registrations + append-only session events are architecturally relevant. |
| 19 | `NousResearch/hermes-agent` | 258,939 | MIT | General/personal Agent platform | **DEEP_STUDY** | Rich tools, Skills, memory, messaging gateway, scheduling and provider runtime; compare to OpenClaw/Codex/Runtime. |
| 20 | `trimstray/the-book-of-secret-knowledge` | 254,631 | MIT | Knowledge / ops/security reference | **DISCOVERY_SOURCE** | Useful curated operational/security reference; treat as non-authoritative discovery. |
| 21 | `torvalds/linux` | 253,909 | NOASSERTION | OS substrate | **ALREADY_SUBSTRATE** | Underlying workstation/server substrate, not an Ordivon-owned capability layer. |
| 22 | `react/react` | 251,805 | MIT | Web UI framework | **ON_DEMAND** | Valid Distribution provider when a React workload requires it; not global Ordivon dependency. |
| 23 | `multica-ai/andrej-karpathy-skills` | 226,994 | — | Agent instructions / Skills | **ABSORB_METHOD** | Extract concise coding-agent behavior lessons; do not create a new framework. |
| 24 | `TheAlgorithms/Python` | 225,727 | MIT | Algorithms knowledge | **REFERENCE_ONLY** | Algorithm reference/learning; use authoritative literature/stdlib first. |
| 25 | `anomalyco/opencode` | 223,387 | MIT | Coding Agent harness | **DEEP_STUDY** | Strong open coding-Agent alternative; compare tool/permission/session/plugin semantics with Codex/Claude Code. |
| 26 | `vuejs/vue` | 212,489 | MIT | Web UI framework | **NO_ACTION** | Vue 2 is legacy for new work; use current framework only if a concrete existing app requires it. |
| 27 | `ossu/computer-science` | 210,561 | MIT | Education | **NO_ACTION** | Curriculum, not Ordivon capability. |
| 28 | `n8n-io/n8n` | 209,164 | NOASSERTION | Integration automation | **ALREADY_COVERED** | Batch 1 completed; natural authority for API/SaaS integration graphs. |
| 29 | `DigitalPlatDev/FreeDomain` | 206,516 | AGPL-3.0 | Distribution / DNS reference | **REFERENCE_ONLY** | Potential domain/DNS learning resource; not a production authority. |
| 30 | `yt-dlp/yt-dlp` | 204,048 | Unlicense | Media acquisition | **ON_DEMAND** | Strong media-download/acquisition provider when rights and workload permit. |
| 31 | `tensorflow/tensorflow` | 201,236 | Apache-2.0 | ML training/inference framework | **ON_DEMAND** | Mature ML provider if a concrete training/inference workload requires TensorFlow. |
| 32 | `firecrawl/firecrawl` | 197,176 | AGPL-3.0 | Web acquisition | **ALREADY_COVERED** | Batch 1 completed; web search/scrape/crawl context provider. |
| 33 | `massgravel/Microsoft-Activation-Scripts` | 197,027 | GPL-3.0 | License activation tooling | **STUDIED_AVOID** | Full deep-study PASS: mature compatibility resolver + diagnostics/repair + four distinct licensing-state mutation engines; retain engineering lessons but not bypass effects. See `microsoft-activation-scripts-deep-architecture-study.md` and `microsoft-activation-scripts-avoidance-study.md`. |
| 34 | `trekhleb/javascript-algorithms` | 196,714 | MIT | Algorithms knowledge | **REFERENCE_ONLY** | Educational algorithms reference only. |
| 35 | `ultraworkers/claw-code` | 194,996 | MIT | Agent experiment / autonomous project | **REFERENCE_ONLY** | Interesting autonomy case study, not a general provider candidate. |
| 36 | `microsoft/vscode` | 194,397 | MIT | Developer environment | **ON_DEMAND** | Mature IDE surface; use as developer tool, not Ordivon Core. |
| 37 | `microsoft/markitdown` | 193,111 | MIT | Document normalization | **ALREADY_COVERED** | Batch 1 completed; lightweight heterogeneous-file normalization candidate. |
| 38 | `avelino/awesome-go` | 191,248 | MIT | Discovery catalog | **DISCOVERY_SOURCE** | Useful Go ecosystem discovery source. |
| 39 | `ohmyzsh/ohmyzsh` | 190,255 | MIT | Shell UX | **NO_ACTION** | Personal shell configuration framework; no system capability gap. |
| 40 | `Significant-Gravitas/AutoGPT` | 187,839 | NOASSERTION | Agent/application platform | **NO_ACTION** | Broad Agent platform category already covered by stronger current providers/product layers. |
| 41 | `jackfrued/Python-100-Days` | 187,603 | — | Education | **NO_ACTION** | Learning course only. |
| 42 | `CyC2018/CS-Notes` | 186,397 | — | Education / reference | **REFERENCE_ONLY** | Useful human reference, not provider. |
| 43 | `521xueweihan/HelloGitHub` | 185,848 | — | Discovery catalog | **DISCOVERY_SOURCE** | Useful project discovery feed; not authority. |
| 44 | `anthropics/skills` | 185,491 | — | Agent Skills standard/content | **ALREADY_COVERED** | Agent Skills kernel already studied and adopted. |
| 45 | `ollama/ollama` | 185,402 | MIT | Local/open model serving | **DEEP_STUDY** | Missing model-serving layer: simple local model lifecycle/API and integration surface. |
| 46 | `getify/You-Dont-Know-JS` | 184,834 | NOASSERTION | Language knowledge | **REFERENCE_ONLY** | JavaScript reference only. |
| 47 | `DietrichGebert/ponytail` | 181,082 | MIT | Engineering Skill / anti-overengineering | **ABSORB_METHOD** | Strong YAGNI/minimalism discipline aligned with build-last; absorb as optional Skill/method. |
| 48 | `flutter/flutter` | 180,763 | BSD-3-Clause | Mobile/cross-platform app framework | **ON_DEMAND** | Activate only if a concrete mobile/cross-platform app favors Flutter. |
| 49 | `github/gitignore` | 176,110 | CC0-1.0 | Engineering templates | **REFERENCE_ONLY** | Useful template source; consume directly where needed. |
| 50 | `f/prompts.chat` | 175,332 | NOASSERTION | Prompt catalog | **REFERENCE_ONLY** | Prompt examples only; prompts require task-specific validation and ownership. |
| 51 | `twbs/bootstrap` | 174,970 | MIT | Web UI framework | **ON_DEMAND** | Mature UI toolkit but only application-specific; not default Distribution stack. |
| 52 | `huggingface/transformers` | 168,378 | Apache-2.0 | Model-definition / ML ecosystem | **DEEP_STUDY** | Important open-model definition pivot across training and inference ecosystems; study with Ollama/llama.cpp. |
| 53 | `msitarzewski/agency-agents` | 165,551 | MIT | Agent role/Skill content | **ABSORB_METHOD** | Mine role cards/process patterns; no new Agent runtime required. |
| 54 | `AUTOMATIC1111/stable-diffusion-webui` | 165,189 | AGPL-3.0 | Generative media UI | **ALREADY_COVERED** | Media generation surface substantially overlaps selected ComfyUI direction; no new base dependency. |
| 55 | `jlevy/the-art-of-command-line` | 162,636 | — | Shell knowledge | **REFERENCE_ONLY** | Useful command-line reference. |
| 56 | `langgenius/dify` | 160,049 | NOASSERTION | AI application platform | **ALREADY_COVERED** | Batch 2 completed; on-demand product shell with licensing boundary. |
| 57 | `Snailclimb/JavaGuide` | 159,358 | Apache-2.0 | Education / Java reference | **NO_ACTION** | Use only for human Java learning; not provider. |
| 58 | `open-webui/open-webui` | 157,324 | NOASSERTION | AI chat/product surface | **TARGETED_COMPARE** | Potential lightweight front-end for local/OpenAI-compatible models; compare with Dify/custom Distribution when needed. |
| 59 | `langflow-ai/langflow` | 156,181 | MIT | Visual AI workflow/product layer | **TARGETED_COMPARE** | Likely overlaps Dify/LangGraph/MCP; compare only for flow-to-API/MCP and extensibility advantages. |
| 60 | `clash-verge-rev/clash-verge-rev` | 155,227 | GPL-3.0 | Network/VPN client | **ON_DEMAND** | Network provider candidate only if current VPN/network composition needs this client. |
| 61 | `anthropics/claude-code` | 153,995 | — | Coding Agent harness | **DEEP_STUDY** | Major coding-Agent reference with plugins, hooks, MCP and subagents; direct comparison with Codex/OpenCode. |
| 62 | `Genymobile/scrcpy` | 153,619 | Apache-2.0 | Android device control | **ON_DEMAND** | Useful for Android testing/device automation if a mobile workload appears. |
| 63 | `farion1231/cc-switch` | 150,474 | MIT | Agent workstation configuration manager | **TARGETED_COMPARE** | Potentially useful for multi-harness/provider/MCP/Skill configuration; compare against existing config management before adoption. |
| 64 | `langchain-ai/langchain` | 148,751 | MIT | Agent/LLM application framework | **TARGETED_COMPARE** | Most primitives already covered; inspect provider abstraction/middleware only for unresolved gaps. |
| 65 | `airbnb/javascript` | 148,033 | MIT | Coding conventions | **ABSORB_METHOD** | Reference conventions where useful; prefer automated formatter/linter and project-native rules. |
| 66 | `x1xhlol/system-prompts-and-models-of-ai-tools` | 144,372 | GPL-3.0 | Prompt/tool behavior corpus | **STUDIED_AVOID** | Full deep-study PASS: valuable mixed-provenance Agent behavior/tool corpus for comparative research and threat modeling; quarantine as secondary evidence, not Prompt Authority. See `system-prompts-corpus-deep-architecture-study.md`. |
| 67 | `Comfy-Org/ComfyUI` | 144,233 | GPL-3.0 | Generative media workflow | **ALREADY_COVERED** | Batch 1 completed; on-demand media inference graph provider. |
| 68 | `github/spec-kit` | 144,148 | MIT | Engineering methodology | **ALREADY_COVERED** | Batch 1 completed; extracted specification-to-plan method. |
| 69 | `Shubhamsaboo/awesome-llm-apps` | 143,534 | Apache-2.0 | AI application cookbook | **DISCOVERY_SOURCE** | Useful runnable examples for agent/RAG/MCP patterns; not platform authority. |
| 70 | `vercel/next.js` | 143,229 | MIT | Web application framework | **ON_DEMAND** | Application-specific Distribution candidate; existing Astro-first direction remains unless workload proves otherwise. |
| 71 | `yangshun/tech-interview-handbook` | 143,188 | MIT | Education | **NO_ACTION** | Interview preparation content. |
| 72 | `nextlevelbuilder/ui-ux-pro-max-skill` | 143,110 | MIT | UI/UX Agent Skill | **ABSORB_METHOD** | Potential design Skill content for Artifact/Distribution; no platform adoption. |
| 73 | `iptv-org/iptv` | 142,858 | Unlicense | Media playlist collection | **NO_ACTION** | No current Ordivon capability need. |
| 74 | `ytdl-org/youtube-dl` | 141,434 | Unlicense | Media acquisition | **NO_ACTION** | yt-dlp is the stronger maintained successor for this capability. |
| 75 | `ripienaar/free-for-dev` | 140,832 | — | Provider/cost discovery | **DISCOVERY_SOURCE** | Useful discovery of free SaaS/PaaS/IaaS tiers; verify current terms before decisions. |
| 76 | `microsoft/PowerToys` | 140,312 | MIT | Windows workstation utilities | **ON_DEMAND** | Useful local productivity utilities; not Ordivon Core. |
| 77 | `Graphify-Labs/graphify` | 139,593 | Apache-2.0 | Relational context graph | **ALREADY_COVERED** | Batch 1 completed; on-demand structural multi-hop context provider. |
| 78 | `golang/go` | 139,473 | BSD-3-Clause | Language/toolchain | **ON_DEMAND** | Use when selected provider/project is Go-based; not Ordivon architecture. |
| 79 | `garrytan/gstack` | 138,358 | MIT | Engineering/product Skills pack | **ABSORB_METHOD** | Mine CEO/design/review/QA/release Skills; use content selectively instead of adopting a new platform. |
| 80 | `harry0703/MoneyPrinterTurbo` | 136,661 | MIT | AI short-video application | **ON_DEMAND** | Media product reference/provider only for a concrete automated short-video workload; ComfyUI remains lower-level media graph. |
| 81 | `labuladong/fucking-algorithm` | 136,004 | — | Education | **NO_ACTION** | Algorithm learning resource only. |
| 82 | `excalidraw/excalidraw` | 134,893 | MIT | Diagram/whiteboard product | **ON_DEMAND** | Useful Artifact/design surface when hand-drawn collaborative diagrams are requested. |
| 83 | `ggml-org/llama.cpp` | 132,911 | MIT | Local model inference engine | **DEEP_STUDY** | Important low-level local inference substrate; study against Ollama and Transformers roles. |
| 84 | `openai/codex` | 132,189 | Apache-2.0 | Coding Agent harness | **ALREADY_COVERED** | Batch 1 completed; current packaged engineering Agent provider. |
| 85 | `krahets/hello-algo` | 131,800 | NOASSERTION | Education | **NO_ACTION** | Algorithm learning resource only. |
| 86 | `Chalarangelo/30-seconds-of-code` | 129,379 | CC-BY-4.0 | Programming reference | **REFERENCE_ONLY** | Small coding/reference snippets; not authority. |
| 87 | `kubernetes/kubernetes` | 128,555 | Apache-2.0 | Container orchestration | **ON_DEMAND** | Activate only when real cluster/HA/scheduling scale exists; current workstation does not justify it. |
| 88 | `rustdesk/rustdesk` | 127,647 | AGPL-3.0 | Remote desktop | **ON_DEMAND** | Potential remote-support/endpoint tool; enable only with explicit security/operations need. |
| 89 | `shadcn-ui/ui` | 127,010 | MIT | Web UI component system | **ON_DEMAND** | Strong application-level UI component source if chosen web stack is compatible. |
| 90 | `react/react-native` | 126,839 | MIT | Mobile application framework | **ON_DEMAND** | Activate for a concrete React Native mobile workload. |
| 91 | `VoltAgent/awesome-design-md` | 124,729 | MIT | Design instructions / Agent context | **ABSORB_METHOD** | DESIGN.md is a useful agent-readable design-system representation to absorb into Artifact/Distribution practice. |
| 92 | `Hack-with-Github/Awesome-Hacking` | 124,134 | CC0-1.0 | Security discovery catalog | **DISCOVERY_SOURCE** | Useful security-tool discovery list; treat links as untrusted until independently validated. |
| 93 | `electron/electron` | 123,659 | MIT | Desktop application framework | **ON_DEMAND** | Use for a concrete JS/HTML desktop app; not base dependency. |
| 94 | `nodejs/node` | 123,126 | NOASSERTION | Language/runtime substrate | **ALREADY_SUBSTRATE** | Common toolchain/runtime already used by many providers; not an Ordivon semantic layer. |
| 95 | `microsoft/generative-ai-for-beginners` | 122,534 | MIT | Education | **NO_ACTION** | Learning curriculum only. |
| 96 | `rust-lang/rust` | 120,876 | Apache-2.0 | Language/toolchain | **ON_DEMAND** | Use when provider/project implementation naturally requires Rust. |
| 97 | `browser-use/browser-use` | 119,616 | MIT | Agentic browser control | **ALREADY_COVERED** | Batch 1 completed and locally installed/verified. |
| 98 | `2dust/v2rayN` | 119,590 | GPL-3.0 | Network proxy client | **ON_DEMAND** | Use only if Network workload needs this Windows/Linux proxy client. |
| 99 | `justjavac/free-programming-books-zh_CN` | 119,454 | GPL-3.0 | Education / knowledge | **REFERENCE_ONLY** | Human learning/reference corpus. |
| 100 | `godotengine/godot` | 119,312 | MIT | Game engine | **ALREADY_COVERED** | Current Game capability already uses/evaluates Godot; no new generic study required. |

## 5. Career-specific consequence

The global threshold is intentionally broad and misses high-value domain projects below 100k stars. Career Engineering therefore maintains a separate dated donor ranking in meta/next/evidence/career/github-career-provider-ranking-20261031.json. High-star current Career leaders such as Career-Ops, AI-Job-Search and Reactive Resume are evaluated there with maintenance and interface evidence rather than being excluded by the global 100k cutoff.

## 6. Refresh boundary

This R2 document is a dated observation. Future refreshes should create a new snapshot or mechanically regenerated current projection rather than editing R1 history. Provider adoption still requires exact upstream identity, interface/consumer fit, license review and owner-local verification.
