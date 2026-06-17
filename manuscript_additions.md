# Manuscript Fixes — Paper–Prototype Gaps

Three targeted edits to align the paper text with what the prototype actually does.
Apply in order.

---

## Fix 1 — Abstract: LLM framing (most important)

**Location:** Abstract, second sentence.

**Current:**
> "...proposes a neuro-symbolic framework for trustworthy retail robots that combines
> LLM-based dialogue with symbolic reasoning over verified interaction state, explicit
> customer mental models, and PDDL-style planning constraints."

**Replace with:**
> "...proposes a neuro-symbolic framework for trustworthy retail robots designed to
> combine LLM-based dialogue with symbolic reasoning over verified interaction state,
> explicit customer mental models, and PDDL-style planning constraints. We instantiate
> a prototype in which the LLM layer is approximated by rule-based extraction and
> template-based generation, enabling isolated evaluation of the symbolic planning
> layer."

*(The existing "We instantiate a prototype that compares…" sentence later in the
abstract can then be shortened or removed to avoid repetition.)*

---

## Fix 2 — Section 3: LLM framing in framework description

**Location:** Section 3 (Neuro-Symbolic Retail Robot Framework), paragraph that
starts with "The LLM interprets user utterances…"

**Current:**
> "The LLM interprets user utterances and realizes natural-language responses, but it
> does not independently decide which recommendation to make. Instead, candidate
> actions are checked against a symbolic state and planner before verbalization."

**Replace with:**
> "In the full framework, the LLM interprets user utterances and realizes
> natural-language responses, but it does not independently decide which
> recommendation to make — candidate actions are checked against a symbolic state and
> planner before verbalization. In the prototype described in Section 4, the LLM layer
> is approximated by a rule-based extraction module and template-based response
> generation, enabling isolated evaluation of the symbolic planning layer without
> requiring a live LLM call."

---

## Fix 3 — Section 3: $J_t$ cross-turn tracking (minor)

**Location:** Section 3, sentence beginning "$J_t$ denotes the verified user journey
state…"

**Append one sentence directly after:**
> "In the current prototype, $J_t$ is seeded per interaction; cross-turn persistence
> of viewed and rejected items is supported by the contestability engine but is not
> tracked in the single-turn simulation."

---

## Fix 4 — Section 3: $\arg\max$ vs. BFS (minor)

**Location:** Section 3, immediately after the line
"$Grounded(a, J_t) \wedge Transparent(a, M_t) \wedge NonExploitative(a, M_t, E_t)$."

**Append one sentence:**
> "In the prototype, $U(a \mid S_t)$ is operationalized as PDDL precondition
> admissibility, and $a_t^*$ is the first action returned by a priority-ordered
> breadth-first search over the grounded domain."
