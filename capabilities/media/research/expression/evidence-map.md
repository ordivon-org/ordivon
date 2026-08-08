# Expression evidence map

This document is a working synthesis, not a literature dump. It records findings that can change creative decisions and the boundary around each finding.

## A. Relatively strong transferable priors

### Processing fluency

Reber, Schwarz, and Winkielman's processing-fluency account links easier perceptual/cognitive processing with more positive aesthetic response. Symmetry, figure-ground contrast, repetition, prototypicality, and priming can all alter fluency.

**Use:** clarity, grouping, legibility, familiar structure, and coherent repetition are usually positive priors when the work benefits from immediate comprehension.

**Boundary:** fluency predicts pleasure better than it predicts interest, profundity, memorability, or artistic value. Making everything maximally easy can erase challenge and character.

Evidence class: `robust_empirical` / `theory_backed`.

### Unity in variety

Controlled product and website studies show that unity and variety can each contribute positively to aesthetic appreciation. Variety becomes easier to appreciate when sufficient unity makes the whole intelligible.

**Use:** establish a coherent grammar, then allow meaningful differentiation inside it. Do not confuse consistency with repetition of one component.

**Boundary:** the concrete manipulations in experiments — such as symmetry and colorfulness — are not universal implementations of unity and variety.

Evidence class: `bounded_empirical`, supported across product and Web domains.

### Familiarity / prototypicality and novelty

Web first-impression experiments show visual complexity and prototypicality influence aesthetic judgments extremely quickly. MAYA-style research and the Unified Model of Aesthetics support a broader tension between familiarity/acceptability and novelty/advancement.

**Use:** preserve enough recognizable structure that an audience can enter the work; spend novelty where identity or discovery matters.

**Boundary:** low complexity and high prototypicality are particularly useful for fast interface impressions, not a law that art should look generic.

Evidence class: `bounded_empirical` / `theory_backed`.

### Manageable prediction and surprise

Music studies using information-theoretic expectation models report preferences for intermediate predictive complexity and interactions between uncertainty and surprise. Related aesthetic-learning work treats expectation, prediction error, and successful model updating as important sources of aesthetic reward.

**Use:** rhythm and repetition establish expectations; departures have force because a pattern exists to violate. Surprise should be legible enough to be integrated unless confusion is intentional.

**Boundary:** optimal surprise is listener-, style-, and context-dependent; musical findings do not provide a numeric recipe for visual design.

Evidence class: `bounded_empirical`, with a useful cross-medium theoretical prior.

### Context and learned expectation matter

Color preference, color-emotion association, musical liking, and aesthetic expertise all show mixtures of shared structure and cultural/individual/contextual variation.

**Use:** encode audience, genre, platform, expertise, and comparison context explicitly when they materially affect expression.

**Boundary:** avoid universal mappings such as “red = danger” or “blue = trust” without context. Shared tendencies are not one-to-one semantics.

Evidence class: `robust_empirical` for context dependence; specific mappings are `bounded_empirical`.

## B. Narrative and temporal priors

### Narrative is information under a perspective

Classical and postclassical narratology distinguish story events from their telling and provide reusable concepts such as narration, focalization, temporal organization, space, character, dialogue, and genre. Focalization is especially useful as a reminder that a work never presents all available information; it selects what is knowable from a perspective.

**Use:** every production should be able to answer: what happened, who/what filters access to it, what is withheld, when is it revealed, and why is this ordering useful?

**Boundary:** narratological categories are analytic tools, not empirical laws or mandatory plot templates.

Evidence class: `theory_backed` / `craft_prior`.

### Event continuity matters more than pixel continuity

Film event-segmentation research shows that viewers can bridge substantial visual and spatiotemporal discontinuity when action remains continuous, while action discontinuities strongly mark event boundaries.

**Use:** cuts, scroll transitions, animation changes, and scene changes should preserve or deliberately break the viewer's event model. “Smooth” need not mean visually similar frame-to-frame.

**Boundary:** evidence comes from narrative-film comprehension; transfer to interactive and short-form media must be tested.

Evidence class: `bounded_empirical`.

### Transportation is distinct from mere clarity

Narrative-transportation research models absorption as a combination of attention, imagery, and affect, and finds that greater transportation can change evaluation and story-consistent beliefs.

**Use:** narrative work may optimize sustained world/model engagement rather than local visual pleasantness. Coherence, perspective, causality, emotional stakes, and information release can be evaluated as a system.

**Boundary:** transportation is not automatically desirable; persuasive effects make truth/provenance constraints more important, not less.

Evidence class: `bounded_empirical` / `theory_backed`.

## C. Distinguish aesthetic outcomes

A recurring problem in aesthetic research is collapsing several responses into “liking.” The laboratory keeps at least these outcomes separate:

- **beauty** — sensed formal/aesthetic excellence;
- **pleasure** — positive hedonic response;
- **interest** — desire to continue resolving or exploring the work;
- **appeal** — approach motivation / desire to engage;
- **clarity** — ease of constructing the intended model;
- **presence** — felt force, atmosphere, or expressive intensity;
- **identity** — distinctiveness without relying on labels;
- **memorability** — persistence after exposure;
- **transportation** — absorption into a narrative/world;
- **trust / credibility** — belief that the presentation is reliable or appropriate.

Silvia-style appraisal work is especially useful here: novelty plus comprehensibility can support interest, while comprehensibility without much novelty more readily supports pleasure; novelty without coping/understanding can become confusion.

## D. Color is a system, not a dictionary

Recent systematic review across many countries and decades reports substantial regularity in color-emotion correspondences, while controlled cross-cultural work also finds meaningful cultural differences.

**Use:** hue, lightness, saturation, contrast, proportion, neighboring colors, semantics, and cultural context should be considered together. Color can carry hierarchy, atmosphere, identity, and semantic convention.

**Do not:** encode a fixed universal lookup table from color to emotion.

Evidence class: `robust_empirical` for systematic associations plus context dependence; individual mappings remain bounded.

## E. Current Agent / computational-aesthetics boundary

The 2026 Visual Aesthetic Benchmark reports that direct comparative judgments from experts are more reliable than rankings derived from absolute scores and that frontier multimodal systems remain far below expert agreement on its strict set-comparison task. AesEval-Bench likewise reports gaps in graphic-design aesthetic assessment, while newer work such as Venus shows that targeted aesthetic-guidance training can improve actionable critique and cropping.

**Use now:** Agents can retrieve references, generate alternatives, inspect implementation, identify likely composition failures, explain candidate trade-offs, and scale pre-screening.

**Do not claim yet:** that an uncalibrated general VLM is an autonomous expert taste authority.

The direction is nevertheless important: targeted comparative and guidance data appear learnable. The laboratory should preserve high-quality critique/evidence pairs so stronger future Agents can inherit a better aesthetic prior instead of restarting from generic taste.

Evidence class: `bounded_empirical`, rapidly changing.

## F. What counts as a mature creative prior versus a trend

A durable prior explains *why* an artifact may work and survives more than one style cycle. Examples: hierarchy, grouping, continuity, contrast, expectation, focalization, rhythm, unity/variety.

A trend is a current surface solution: glassmorphism, bento grids, one fashion of kinetic typography, a grading look, a social-video caption style, a particular AI-image texture.

Trends are useful reference material. They should never be serialized into the laboratory as timeless laws.

## Sources retained in the first foundation

- Reber, R., Schwarz, N., & Winkielman, P. (2004). *Processing Fluency and Aesthetic Pleasure*. Personality and Social Psychology Review. DOI `10.1207/s15327957pspr0804_3`.
- Leder, H., Belke, B., Oeberst, A., & Augustin, D. (2004). *A model of aesthetic appreciation and aesthetic judgments*. British Journal of Psychology. DOI `10.1348/0007126042369811`.
- Tuch, A. N. et al. (2012). *The role of visual complexity and prototypicality regarding first impression of websites*. IJHCS. DOI `10.1016/j.ijhcs.2012.06.003`.
- Post, R. A. G., Blijlevens, J., & Hekkert, P. (2016). *To preserve unity while almost allowing for chaos*. Acta Psychologica. DOI `10.1016/j.actpsy.2015.11.013`.
- Post, R. A. G. et al. (2017). *Unity in Variety in website aesthetics*. IJHCS. DOI `10.1016/j.ijhcs.2017.02.003`.
- Berghman, M. & Hekkert, P. (2017). *Towards a unified model of aesthetic pleasure in design*. New Ideas in Psychology. DOI `10.1016/j.newideapsych.2017.03.004`.
- Herman, D. (ed.) (2007). *The Cambridge Companion to Narrative*, especially story/plot/narration, time/space, focalization and genre.
- Green, M. C. & Brock, T. C. (2000). *The Role of Transportation in the Persuasiveness of Public Narratives*. JPSP. DOI `10.1037/0022-3514.79.5.701`.
- Magliano, J. P. & Zacks, J. M. (2011). *The Impact of Continuity Editing in Narrative Film on Event Segmentation*. Cognitive Science. DOI `10.1111/j.1551-6709.2011.01202.x`.
- *Predictability and Uncertainty in the Pleasure of Music: A Reward for Learning?* (2019), empirical information-theoretic tests of musical expectation and liking.
- Jonauskaite and colleagues / later systematic work on cross-cultural color-emotion associations, including the 2025 systematic review of 128 years of evidence.
- Feng, Y. et al. (2026). *Visual Aesthetic Benchmark: Can Frontier Models Judge Beauty?* arXiv `2605.12684`.
- An, A. et al. (2026). *Can Vision Language Models Assess Graphic Design Aesthetics?* arXiv `2603.01083`.
- Du, T. et al. (2026). *Venus: Benchmarking and Empowering Multimodal Large Language Models for Aesthetic Guidance and Cropping*. arXiv `2602.23980`.

This list should grow only when a source changes a hypothesis, experiment, medium profile, or known boundary.
