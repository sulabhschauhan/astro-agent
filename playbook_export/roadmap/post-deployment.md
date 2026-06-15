# Post-Deployment Roadmap

Items deferred until after hosting + the new (non-Streamlit) UI is built.
Not scoped for implementation yet — captured here so they aren't
rediscovered from scratch later.

## 1. LLM model upgrade evaluation

Current: GPT-4o-mini (primary reasoning + classification), GPT-4o (vision).

Question: would a frontier-tier model (GPT-5.4/5.5 as of mid-2026) at the
final answer-generation step improve synthesis quality when reconciling
AstroSage PDF + palm description + multiple RAG chunks into one coherent
Parashara-voice reading?

Context: the established finding ("answer quality bottleneck was missing
personal data, not model capability") was validated with GPT-4o-mini — it
doesn't rule out a frontier-tier jump specifically at the synthesis step.
Classification/query-rewriting (Session 14, 37/37 passing) should NOT be
upgraded — narrow tasks where mini-tier is sufficient and was already
validated.

Cost: GPT-4o-mini ~$0.15/$0.60 per 1M tokens vs GPT-5.4-mini ~$0.75/$4.50
(5-7x) vs GPT-5.5 ~$5/$30 (30-50x), per 1M tokens (June 2026 pricing).

Plan: test via Phase C eval harness — A/B same context bundle through
current vs upgraded model at the answer-generation step only, scored against
the AstroSage-reference baseline. Not a blanket swap.

Also note: GPT-4o/GPT-4o-mini are now "legacy" in OpenAI's lineup — may
become a forced migration independent of this evaluation.

## 2. Premium UI agent gap

.claude/ui_ux.md (current) is a functional-correctness agent: loading
states, error messages, form state, word limits — all Streamlit-specific.
It has no visual-design/brand dimension (typography, color, spacing, visual
hierarchy, motion, aesthetic direction) and would pass a functionally-correct
but visually generic UI.

Plan: once the new frontend stack is chosen, either expand ui_ux.md with a
visual-design dimension, or add a dedicated "Visual Design" agent (new agent
— requires explicit approval per .cursorrules). Content should be scoped
against the actual chosen stack and concrete premium-UI reference points,
not written in the abstract now.

Surgical: new file only, no existing files touched.
