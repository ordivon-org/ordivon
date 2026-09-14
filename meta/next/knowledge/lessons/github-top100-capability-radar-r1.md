# GitHub Global Top-100 Capability Radar R1

Status: **COMPLETE SNAPSHOT + ORDIVON TRIAGE**
Snapshot: **2026-09-14**

## 1. Source and ranking method

- Primary ranking source: GitHub Search API, query `stars:>100000`, sorted by `stars desc`, `per_page=100`.
- GitHub reported **100 rows returned from 127 repositories above 100k stars** at capture time.
- Star counts are a volatile discovery signal, not an acceptance criterion.
- A third-party top-100 ranking was used only as a cross-check. Where search-index snippets disagreed with GitHub API data, direct GitHub API repository/search counts were treated as authoritative for this snapshot.

## 2. Decision vocabulary

| Decision | Meaning |
|---|---|
| `DEEP_STUDY` | New/high-value candidate worth a full one-sentence + prototype-gate teardown. |
| `TARGETED_COMPARE` | Likely overlaps an existing natural authority; compare only against that authority for a concrete delta. |
| `ABSORB_METHOD` | Mine methods/Skills/templates; do not add a new platform. |
| `ALREADY_COVERED` | Already studied/accepted in Ordivon Next; no new generic work. |
| `ALREADY_SUBSTRATE` | Existing language/OS/runtime substrate; not an Ordivon semantic subsystem. |
| `ON_DEMAND` | Legitimate mature provider, but activate only for a real workload. |
| `DISCOVERY_SOURCE` | Use to find projects/providers; never treat the list itself as authority. |
| `REFERENCE_ONLY` | Useful human/technical reference; no provider/platform adoption. |
| `NO_ACTION` | No current Ordivon value beyond incidental learning. |
| `AVOID` | Do not adopt as dependency/default due to compliance, trust, or capability mismatch. |

## 3. Summary counts

- **DEEP_STUDY: 9**
- **TARGETED_COMPARE: 4**
- **ABSORB_METHOD: 8**
- **ALREADY_COVERED: 13**
- **ALREADY_SUBSTRATE: 2**
- **ON_DEMAND: 21**
- **DISCOVERY_SOURCE: 10**
- **REFERENCE_ONLY: 14**
- **NO_ACTION: 17**
- **AVOID: 2**

## 4. Highest-value next studies

### Agent / Harness landscape

- **OpenClaw** — broad agent runtime/platform, skills, sessions, plugin and messaging gateway.
- **ECC** — cross-harness Skills/agents/memory/security/eval/continuous-learning discipline.
- **Hermes Agent** — personal/general Agent platform with tools, memory, messaging, scheduling and MCP.
- **DeepSeek Harness** — everything-is-plugin / Cordis architecture with reversible registrations and append-only session events.
- **OpenCode** — open coding-Agent harness; compare permissions, tools, sessions, plugins and ergonomics against Codex.
- **Claude Code** — major coding-Agent reference; compare plugin/hooks/MCP/subagent/SDK surfaces against Codex/OpenCode.

### Local / open-model substrate

- **Transformers** — model-definition interoperability layer across training/inference ecosystems.
- **llama.cpp** — low-level efficient local inference engine.
- **Ollama** — higher-level local model lifecycle/server/API and Agent integration surface.

These three should be studied as **one vertical stack**, not three competing products.

## 5. Targeted comparisons, not broad new systems

- **Langflow** — compare only against Dify + LangGraph/MCP for visual flow-to-API/MCP advantages.
- **Open WebUI** — compare only as a lightweight user-facing model/RAG interface, especially if local model serving is activated.
- **LangChain** — inspect only unresolved provider abstraction/middleware value after LangGraph/Haystack/LlamaIndex studies.
- **CC Switch** — compare as workstation-level configuration manager for multiple coding agents/providers/MCP/Skills; useful only if it reduces real configuration drift.

## 6. Methods/Skills worth mining without platform adoption

- `mattpocock/skills`
- `andrej-karpathy-skills`
- `agency-agents`
- `ponytail`
- `gstack`
- `ui-ux-pro-max-skill`
- `awesome-design-md`
- Airbnb JavaScript conventions where relevant

The common rule: **extract reusable instructions/methods into standards-compatible Skills or project guidance; do not import another global agent runtime.**

## 7. Full Top-100 classification

| # | Repository | Stars | License | Domain | Decision | Ordivon judgement |
|---:|---|---:|---|---|---|---|
| 1 | `codecrafters-io/build-your-own-x` | 547,094 | — | Knowledge / learning | **REFERENCE_ONLY** | Useful for prototype understanding; conflicts with build-last if treated as implementation strategy. |
| 2 | `sindresorhus/awesome` | 505,841 | CC0-1.0 | Discovery catalog | **DISCOVERY_SOURCE** | Broad discovery index; useful for finding mature projects, not an authority itself. |
| 3 | `public-apis/public-apis` | 479,828 | MIT | Discovery catalog / APIs | **DISCOVERY_SOURCE** | Useful API discovery source before writing adapters. |
| 4 | `freeCodeCamp/freeCodeCamp` | 455,416 | BSD-3-Clause | Education | **NO_ACTION** | Learning platform; no Ordivon capability gap. |
| 5 | `EbookFoundation/free-programming-books` | 396,726 | CC-BY-4.0 | Education / knowledge | **REFERENCE_ONLY** | Human learning/reference corpus; not an execution provider. |
| 6 | `openclaw/openclaw` | 389,638 | NOASSERTION | Agent harness / personal agent platform | **DEEP_STUDY** | High-value full agent runtime, skills, sessions, plugins and messaging surface; compare with Runtime/Codex/Hermes. |
| 7 | `donnemartin/system-design-primer` | 369,850 | NOASSERTION | Engineering knowledge | **REFERENCE_ONLY** | Useful systems-design reference, but not authoritative architecture or provider. |
| 8 | `nilbuild/developer-roadmap` | 367,124 | NOASSERTION | Education | **NO_ACTION** | Career learning roadmap, not a capability provider. |
| 9 | `jwasham/coding-interview-university` | 360,860 | CC-BY-SA-4.0 | Education | **NO_ACTION** | Interview curriculum; unrelated to Ordivon architecture. |
| 10 | `vinta/awesome-python` | 320,505 | NOASSERTION | Discovery catalog | **DISCOVERY_SOURCE** | Useful Python provider/library discovery source. |
| 11 | `awesome-selfhosted/awesome-selfhosted` | 319,102 | NOASSERTION | Discovery catalog / self-hosting | **DISCOVERY_SOURCE** | Useful source for mature self-hostable products before custom building. |
| 12 | `obra/superpowers` | 286,322 | MIT | Engineering methodology / Skills | **ALREADY_COVERED** | Batch 1 completed; retain selected engineering discipline, no new platform. |
| 13 | `practical-tutorials/project-based-learning` | 283,227 | MIT | Education | **NO_ACTION** | Tutorial catalog; no capability gap. |
| 14 | `996icu/996.ICU` | 277,024 | NOASSERTION | Community / social | **NO_ACTION** | Not an Ordivon technical/provider capability. |
| 15 | `mattpocock/skills` | 261,486 | MIT | Agent Skills content | **ABSORB_METHOD** | Mine high-quality reusable engineering Skills; Agent Skills primitive already understood. |
| 16 | `affaan-m/ECC` | 257,893 | MIT | Agent harness methodology / memory / eval | **DEEP_STUDY** | Combines skills, agents, memory, security, eval and learning across harnesses; potentially useful composition lessons. |
| 17 | `react/react` | 250,424 | MIT | Web UI framework | **ON_DEMAND** | Valid Distribution provider when a React workload requires it; not global Ordivon dependency. |
| 18 | `torvalds/linux` | 248,860 | NOASSERTION | OS substrate | **ALREADY_SUBSTRATE** | Underlying workstation/server substrate, not an Ordivon-owned capability layer. |
| 19 | `NousResearch/hermes-agent` | 245,246 | MIT | General/personal Agent platform | **DEEP_STUDY** | Rich tools, Skills, memory, messaging gateway, scheduling and provider runtime; compare to OpenClaw/Codex/Runtime. |
| 20 | `trimstray/the-book-of-secret-knowledge` | 243,623 | MIT | Knowledge / ops/security reference | **DISCOVERY_SOURCE** | Useful curated operational/security reference; treat as non-authoritative discovery. |
| 21 | `TheAlgorithms/Python` | 224,554 | MIT | Algorithms knowledge | **REFERENCE_ONLY** | Algorithm reference/learning; use authoritative literature/stdlib first. |
| 22 | `deepseek-ai/deepseek-harness` | 222,974 | MIT | Agent harness / plugin runtime | **DEEP_STUDY** | Everything-is-plugin + reversible registrations + append-only session events are architecturally relevant. |
| 23 | `multica-ai/andrej-karpathy-skills` | 212,832 | — | Agent instructions / Skills | **ABSORB_METHOD** | Extract concise coding-agent behavior lessons; do not create a new framework. |
| 24 | `vuejs/vue` | 212,798 | MIT | Web UI framework | **NO_ACTION** | Vue 2 is legacy for new work; use current framework only if a concrete existing app requires it. |
| 25 | `ossu/computer-science` | 208,997 | MIT | Education | **NO_ACTION** | Curriculum, not Ordivon capability. |
| 26 | `anomalyco/opencode` | 207,196 | MIT | Coding Agent harness | **DEEP_STUDY** | Strong open coding-Agent alternative; compare tool/permission/session/plugin semantics with Codex/Claude Code. |
| 27 | `n8n-io/n8n` | 204,218 | NOASSERTION | Integration automation | **ALREADY_COVERED** | Batch 1 completed; natural authority for API/SaaS integration graphs. |
| 28 | `tensorflow/tensorflow` | 200,064 | Apache-2.0 | ML training/inference framework | **ON_DEMAND** | Mature ML provider if a concrete training/inference workload requires TensorFlow. |
| 29 | `DigitalPlatDev/FreeDomain` | 199,279 | AGPL-3.0 | Distribution / DNS reference | **REFERENCE_ONLY** | Potential domain/DNS learning resource; not a production authority. |
| 30 | `trekhleb/javascript-algorithms` | 196,706 | MIT | Algorithms knowledge | **REFERENCE_ONLY** | Educational algorithms reference only. |
| 31 | `ultraworkers/claw-code` | 195,221 | MIT | Agent experiment / autonomous project | **REFERENCE_ONLY** | Interesting autonomy case study, not a general provider candidate. |
| 32 | `microsoft/vscode` | 192,476 | MIT | Developer environment | **ON_DEMAND** | Mature IDE surface; use as developer tool, not Ordivon Core. |
| 33 | `yt-dlp/yt-dlp` | 190,981 | Unlicense | Media acquisition | **ON_DEMAND** | Strong media-download/acquisition provider when rights and workload permit. |
| 34 | `massgravel/Microsoft-Activation-Scripts` | 190,495 | GPL-3.0 | License activation tooling | **AVOID** | Not required; creates licensing/compliance risk and no Ordivon capability need. |
| 35 | `ohmyzsh/ohmyzsh` | 189,708 | MIT | Shell UX | **NO_ACTION** | Personal shell configuration framework; no system capability gap. |
| 36 | `Significant-Gravitas/AutoGPT` | 187,315 | NOASSERTION | Agent/application platform | **NO_ACTION** | Broad Agent platform category already covered by stronger current providers/product layers. |
| 37 | `jackfrued/Python-100-Days` | 186,411 | — | Education | **NO_ACTION** | Learning course only. |
| 38 | `CyC2018/CS-Notes` | 186,047 | — | Education / reference | **REFERENCE_ONLY** | Useful human reference, not provider. |
| 39 | `getify/You-Dont-Know-JS` | 184,880 | NOASSERTION | Language knowledge | **REFERENCE_ONLY** | JavaScript reference only. |
| 40 | `avelino/awesome-go` | 184,077 | MIT | Discovery catalog | **DISCOVERY_SOURCE** | Useful Go ecosystem discovery source. |
| 41 | `microsoft/markitdown` | 183,706 | MIT | Document normalization | **ALREADY_COVERED** | Batch 1 completed; lightweight heterogeneous-file normalization candidate. |
| 42 | `ollama/ollama` | 180,853 | MIT | Local/open model serving | **DEEP_STUDY** | Missing model-serving layer: simple local model lifecycle/API and integration surface. |
| 43 | `firecrawl/firecrawl` | 180,095 | AGPL-3.0 | Web acquisition | **ALREADY_COVERED** | Batch 1 completed; web search/scrape/crawl context provider. |
| 44 | `flutter/flutter` | 178,936 | BSD-3-Clause | Mobile/cross-platform app framework | **ON_DEMAND** | Activate only if a concrete mobile/cross-platform app favors Flutter. |
| 45 | `521xueweihan/HelloGitHub` | 176,437 | — | Discovery catalog | **DISCOVERY_SOURCE** | Useful project discovery feed; not authority. |
| 46 | `anthropics/skills` | 176,172 | — | Agent Skills standard/content | **ALREADY_COVERED** | Agent Skills kernel already studied and adopted. |
| 47 | `github/gitignore` | 175,762 | CC0-1.0 | Engineering templates | **REFERENCE_ONLY** | Useful template source; consume directly where needed. |
| 48 | `twbs/bootstrap` | 174,792 | MIT | Web UI framework | **ON_DEMAND** | Mature UI toolkit but only application-specific; not default Distribution stack. |
| 49 | `f/prompts.chat` | 170,280 | NOASSERTION | Prompt catalog | **REFERENCE_ONLY** | Prompt examples only; prompts require task-specific validation and ownership. |
| 50 | `huggingface/transformers` | 165,668 | Apache-2.0 | Model-definition / ML ecosystem | **DEEP_STUDY** | Important open-model definition pivot across training and inference ecosystems; study with Ollama/llama.cpp. |
| 51 | `AUTOMATIC1111/stable-diffusion-webui` | 164,933 | AGPL-3.0 | Generative media UI | **ALREADY_COVERED** | Media generation surface substantially overlaps selected ComfyUI direction; no new base dependency. |
| 52 | `jlevy/the-art-of-command-line` | 162,378 | — | Shell knowledge | **REFERENCE_ONLY** | Useful command-line reference. |
| 53 | `Snailclimb/JavaGuide` | 158,510 | Apache-2.0 | Education / Java reference | **NO_ACTION** | Use only for human Java learning; not provider. |
| 54 | `langgenius/dify` | 155,644 | NOASSERTION | AI application platform | **ALREADY_COVERED** | Batch 2 completed; on-demand product shell with licensing boundary. |
| 55 | `langflow-ai/langflow` | 154,761 | MIT | Visual AI workflow/product layer | **TARGETED_COMPARE** | Likely overlaps Dify/LangGraph/MCP; compare only for flow-to-API/MCP and extensibility advantages. |
| 56 | `msitarzewski/agency-agents` | 152,189 | MIT | Agent role/Skill content | **ABSORB_METHOD** | Mine role cards/process patterns; no new Agent runtime required. |
| 57 | `open-webui/open-webui` | 151,926 | NOASSERTION | AI chat/product surface | **TARGETED_COMPARE** | Potential lightweight front-end for local/OpenAI-compatible models; compare with Dify/custom Distribution when needed. |
| 58 | `Genymobile/scrcpy` | 149,572 | Apache-2.0 | Android device control | **ON_DEMAND** | Useful for Android testing/device automation if a mobile workload appears. |
| 59 | `airbnb/javascript` | 148,227 | MIT | Coding conventions | **ABSORB_METHOD** | Reference conventions where useful; prefer automated formatter/linter and project-native rules. |
| 60 | `langchain-ai/langchain` | 146,266 | MIT | Agent/LLM application framework | **TARGETED_COMPARE** | Most primitives already covered; inspect provider abstraction/middleware only for unresolved gaps. |
| 61 | `anthropics/claude-code` | 144,957 | — | Coding Agent harness | **DEEP_STUDY** | Major coding-Agent reference with plugins, hooks, MCP and subagents; direct comparison with Codex/OpenCode. |
| 62 | `clash-verge-rev/clash-verge-rev` | 144,296 | GPL-3.0 | Network/VPN client | **ON_DEMAND** | Network provider candidate only if current VPN/network composition needs this client. |
| 63 | `x1xhlol/system-prompts-and-models-of-ai-tools` | 143,606 | GPL-3.0 | Prompt leak/archive | **AVOID** | Untrusted/leaked prompt corpus; not a mature authority or dependency. |
| 64 | `yangshun/tech-interview-handbook` | 142,606 | MIT | Education | **NO_ACTION** | Interview preparation content. |
| 65 | `vercel/next.js` | 142,281 | MIT | Web application framework | **ON_DEMAND** | Application-specific Distribution candidate; existing Astro-first direction remains unless workload proves otherwise. |
| 66 | `ytdl-org/youtube-dl` | 141,219 | Unlicense | Media acquisition | **NO_ACTION** | yt-dlp is the stronger maintained successor for this capability. |
| 67 | `golang/go` | 138,803 | BSD-3-Clause | Language/toolchain | **ON_DEMAND** | Use when selected provider/project is Go-based; not Ordivon architecture. |
| 68 | `microsoft/PowerToys` | 138,618 | MIT | Windows workstation utilities | **ON_DEMAND** | Useful local productivity utilities; not Ordivon Core. |
| 69 | `iptv-org/iptv` | 138,587 | Unlicense | Media playlist collection | **NO_ACTION** | No current Ordivon capability need. |
| 70 | `Shubhamsaboo/awesome-llm-apps` | 138,016 | Apache-2.0 | AI application cookbook | **DISCOVERY_SOURCE** | Useful runnable examples for agent/RAG/MCP patterns; not platform authority. |
| 71 | `DietrichGebert/ponytail` | 137,591 | MIT | Engineering Skill / anti-overengineering | **ABSORB_METHOD** | Strong YAGNI/minimalism discipline aligned with build-last; absorb as optional Skill/method. |
| 72 | `ripienaar/free-for-dev` | 137,306 | — | Provider/cost discovery | **DISCOVERY_SOURCE** | Useful discovery of free SaaS/PaaS/IaaS tiers; verify current terms before decisions. |
| 73 | `github/spec-kit` | 136,512 | MIT | Engineering methodology | **ALREADY_COVERED** | Batch 1 completed; extracted specification-to-plan method. |
| 74 | `labuladong/fucking-algorithm` | 135,877 | — | Education | **NO_ACTION** | Algorithm learning resource only. |
| 75 | `Comfy-Org/ComfyUI` | 132,975 | GPL-3.0 | Generative media workflow | **ALREADY_COVERED** | Batch 1 completed; on-demand media inference graph provider. |
| 76 | `garrytan/gstack` | 132,919 | MIT | Engineering/product Skills pack | **ABSORB_METHOD** | Mine CEO/design/review/QA/release Skills; use content selectively instead of adopting a new platform. |
| 77 | `farion1231/cc-switch` | 132,719 | MIT | Agent workstation configuration manager | **TARGETED_COMPARE** | Potentially useful for multi-harness/provider/MCP/Skill configuration; compare against existing config management before adoption. |
| 78 | `excalidraw/excalidraw` | 131,794 | MIT | Diagram/whiteboard product | **ON_DEMAND** | Useful Artifact/design surface when hand-drawn collaborative diagrams are requested. |
| 79 | `krahets/hello-algo` | 130,069 | NOASSERTION | Education | **NO_ACTION** | Algorithm learning resource only. |
| 80 | `Chalarangelo/30-seconds-of-code` | 129,071 | CC-BY-4.0 | Programming reference | **REFERENCE_ONLY** | Small coding/reference snippets; not authority. |
| 81 | `ggml-org/llama.cpp` | 128,144 | MIT | Local model inference engine | **DEEP_STUDY** | Important low-level local inference substrate; study against Ollama and Transformers roles. |
| 82 | `kubernetes/kubernetes` | 127,691 | Apache-2.0 | Container orchestration | **ON_DEMAND** | Activate only when real cluster/HA/scheduling scale exists; current workstation does not justify it. |
| 83 | `nextlevelbuilder/ui-ux-pro-max-skill` | 127,441 | MIT | UI/UX Agent Skill | **ABSORB_METHOD** | Potential design Skill content for Artifact/Distribution; no platform adoption. |
| 84 | `react/react-native` | 126,588 | MIT | Mobile application framework | **ON_DEMAND** | Activate for a concrete React Native mobile workload. |
| 85 | `openai/codex` | 123,927 | Apache-2.0 | Coding Agent harness | **ALREADY_COVERED** | Batch 1 completed; current packaged engineering Agent provider. |
| 86 | `shadcn-ui/ui` | 123,706 | MIT | Web UI component system | **ON_DEMAND** | Strong application-level UI component source if chosen web stack is compatible. |
| 87 | `rustdesk/rustdesk` | 123,389 | AGPL-3.0 | Remote desktop | **ON_DEMAND** | Potential remote-support/endpoint tool; enable only with explicit security/operations need. |
| 88 | `harry0703/MoneyPrinterTurbo` | 123,343 | MIT | AI short-video application | **ON_DEMAND** | Media product reference/provider only for a concrete automated short-video workload; ComfyUI remains lower-level media graph. |
| 89 | `electron/electron` | 123,036 | MIT | Desktop application framework | **ON_DEMAND** | Use for a concrete JS/HTML desktop app; not base dependency. |
| 90 | `nodejs/node` | 121,909 | NOASSERTION | Language/runtime substrate | **ALREADY_SUBSTRATE** | Common toolchain/runtime already used by many providers; not an Ordivon semantic layer. |
| 91 | `Hack-with-Github/Awesome-Hacking` | 120,337 | CC0-1.0 | Security discovery catalog | **DISCOVERY_SOURCE** | Useful security-tool discovery list; treat links as untrusted until independently validated. |
| 92 | `microsoft/generative-ai-for-beginners` | 119,681 | MIT | Education | **NO_ACTION** | Learning curriculum only. |
| 93 | `justjavac/free-programming-books-zh_CN` | 118,875 | GPL-3.0 | Education / knowledge | **REFERENCE_ONLY** | Human learning/reference corpus. |
| 94 | `rust-lang/rust` | 118,819 | Apache-2.0 | Language/toolchain | **ON_DEMAND** | Use when provider/project implementation naturally requires Rust. |
| 95 | `godotengine/godot` | 117,076 | MIT | Game engine | **ALREADY_COVERED** | Current Game capability already uses/evaluates Godot; no new generic study required. |
| 96 | `Graphify-Labs/graphify` | 116,515 | Apache-2.0 | Relational context graph | **ALREADY_COVERED** | Batch 1 completed; on-demand structural multi-hop context provider. |
| 97 | `2dust/v2rayN` | 116,111 | GPL-3.0 | Network proxy client | **ON_DEMAND** | Use only if Network workload needs this Windows/Linux proxy client. |
| 98 | `VoltAgent/awesome-design-md` | 115,749 | MIT | Design instructions / Agent context | **ABSORB_METHOD** | DESIGN.md is a useful agent-readable design-system representation to absorb into Artifact/Distribution practice. |
| 99 | `mrdoob/three.js` | 115,501 | MIT | Web 3D rendering | **ON_DEMAND** | Useful for web 3D/game/visualization deliverables, not a base capability. |
| 100 | `browser-use/browser-use` | 114,542 | MIT | Agentic browser control | **ALREADY_COVERED** | Batch 1 completed and locally installed/verified. |

## 8. Category-level conclusions

### A. AI/Agent projects are overrepresented, but most collapse into a few authorities

The top 100 contains many Agent-related repositories, but they mostly map to:

```text
coding/general Agent harness
Skills/method packs
model serving
AI application product surface
observability/eval
context/RAG
```

Therefore star count does **not** justify installing every Agent framework. The goal of the next study wave is to compare representatives and eliminate duplicate semantics.

### B. Learning repositories dominate stars but do not imply infrastructure requirements

A large fraction of the top 100 are books, roadmaps, interview material, algorithms or curated lists. They are useful as human knowledge/discovery sources, not runtime dependencies.

### C. Framework popularity is workload-specific

React, Flutter, Next.js, React Native, Electron, Three.js, Kubernetes, TensorFlow and similar projects are major mature technologies, but they belong to domain/product choices. They must not become permanent Ordivon dependencies merely because they are globally popular.

### D. Curated lists are discovery inputs, not authorities

`awesome`, `awesome-python`, `awesome-selfhosted`, `public-apis`, `free-for-dev`, `Awesome-Hacking`, `HelloGitHub` and similar repositories are valuable **search priors**. Every candidate found through them still requires direct upstream/license/security verification.

### E. Existing two-batch work already covers a meaningful slice of the global top 100

The top 100 directly contains providers already studied in depth: Superpowers, n8n, MarkItDown, Firecrawl, Agent Skills, Dify, Spec Kit, ComfyUI, Codex, Graphify and Browser Use. This validates that the prior mining batches hit globally important projects without simply following star rank.

## 9. Proposed next execution order

Do not study the remaining candidates one-by-one in global rank order. Use four compact waves:

1. **Harness Wave:** OpenClaw → Hermes Agent → DeepSeek Harness → OpenCode → Claude Code, with ECC mined across them.
2. **Local Model Wave:** Transformers → llama.cpp → Ollama as model definition → inference engine → local serving/product layer.
3. **Product Compare Wave:** Langflow vs Dify; Open WebUI as user-facing local-model/product surface; LangChain only for residual abstraction gaps.
4. **Skill/Method Sweep:** Skills/Karpathy/Ponytail/gstack/UI-UX/DESIGN.md/agency-agents, extracting only evidence-backed reusable methods.

CC Switch should be tested after the Harness Wave, because its value depends on how many harnesses Ordivon actually retains.

## 10. Final decision

**TOP-100 RADAR PASS.**

The global star ranking does not reveal a need for dozens of new Ordivon subsystems. It does reveal a concentrated next research frontier around **Agent harness architecture and local/open-model substrate**, plus several high-quality Skill/method sources. Everything else is either already covered, workload-gated, reference/discovery material, or unrelated to current Ordivon goals.
