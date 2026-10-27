# Ask SHAZA: design before implementation

*Design note for charter section 9, stage 7. Companion to `data-environments.md` and
`scenario-engine.md`. Nothing here gets built until the stages below it are done, and section 8
says what "done" means.*

---

## 1. The rule the whole design hangs on

**The model is never in the data path.**

A tool returns a structured result. That result goes to the interface directly and is rendered
by the interface. The model receives a copy so it can write prose *about* the result, but no
number the user reads has ever passed through the model's output tokens.

This is the difference between grounding as an architecture and grounding as a hope. The common
design lets the model write "Musanze averaged 17.5 degrees over the period", and from that moment
there is no guarantee the sentence matches the database. The number was retyped by a language
model. It is probably right. Nobody can prove it.

So the answer SHAZA returns is a rendered result plus commentary, never prose containing data. If
the commentary needs to refer to a value, it refers to a field in the result, and the interface
substitutes the value at render time.

## 2. Preventing invention is structural, not prompt engineering

Five mechanisms, in rough order of how much work they do:

**The data path rule above.** Does most of the work on its own.

**Structured outputs.** Constrain the response with `output_config.format` and parse it against a
schema rather than reading free text. The narration field holds references, not figures.

**Strict tool definitions.** Set `strict: true` on each tool so arguments validate exactly
against the schema, with `additionalProperties: false`. A malformed call fails loudly instead of
arriving as a plausible guess.

**A numeric post-check.** Before rendering, assert that every numeric token in the response
appears in the tool results. Anything that does not trace back is a bug, logged and surfaced,
not quietly shown. This is cheap and catches the failure mode that matters.

**An explicit refusal path.** When tools return nothing, the answer is that SHAZA has no data for
the question. Silence from a tool must never be filled by the model's own knowledge of
agriculture, which is extensive, fluent, and not SHAZA's.

Note that forcing a tool call is not available as a lever. Current Claude models reject
`tool_choice` set to `any` or a named tool, so grounding cannot be enforced by making the model
call something. Steer with `auto` plus an instruction, and rely on the architecture to make an
ungrounded answer structurally unusable rather than merely discouraged.

## 3. Tools: only what has data behind it

**A stub tool is worse than a missing tool.** A missing tool makes the model say it cannot answer.
A registered tool that returns nothing invites it to be helpful from its own training instead.
So a tool is registered the day its data exists and not one day earlier.

Measured against the proposed list:

| Proposed tool | Status | Note |
| --- | --- | --- |
| `get_weather` | ready | the observations endpoint |
| `get_historical_weather` | **merge into the above** | same endpoint, a date range |
| `get_location_information` | ready | the locations endpoint |
| `compare_locations` | buildable now | two series plus a difference |
| `analyze_trend` | after indices | needs the Layer 2 work |
| `run_scenario` | stage 6 | needs the scenario engine |
| `get_crop_information` | **no data** | there is no crop table |
| `get_soil_information` | **no data at all** | SHAZA has never ingested soil |

Splitting weather into current and historical is worth avoiding. It is one endpoint with a date
range, and two tool names over one data source mainly creates an opportunity to pick the wrong
one.

**Tools call the same API the dashboard calls.** Not a parallel query layer. One source of truth
means the provenance block that already exists on every response comes along for free, and a
grounding bug surfaces in the dashboard too rather than hiding in the AI path.

## 4. Provenance has to survive into conversation

Every tool response already carries a `ProvenanceBlock`. The conversational layer must render it,
not summarise it away. If an answer contains a number, it contains that number's provenance.

The failure this prevents is specific and likely. Asked what the temperature in Musanze was, a
fluent system says "17.5 degrees". SHAZA's honest answer names the figure as ERA5 reanalysis,
which is model output constrained by observations, not a thermometer in Musanze. The distinction
survives three layers of schema design and then dies in the chat interface unless the chat
interface is built to carry it.

## 5. Three classes of question, and the one that matters

**Answerable from tools.** Call, render, attach provenance. The ordinary path.

**Not in the data.** Soil questions today, pest questions today, anything outside the six
locations. The answer is that SHAZA does not hold that, optionally with what it does hold. Never
an inference dressed as a retrieval.

**Advice.** *What should I plant in Musanze? Will my potatoes do well this season? Should I
delay planting?* These are the questions a farmer actually has, a language model answers them
fluently, and SHAZA must decline them. Charter section 10 and rule 4 are explicit: this is
research simulation, not farming advice, until validated against real observations.

That third class is the one almost nobody builds, because declining requires work while
answering is free. It needs to exist in the system prompt, in the tool surface, and above all in
the eval set.

## 6. Evaluation, written before the feature

The eval set is built first, because it is the only thing that makes the rest checkable. Four
categories, each with a mechanical pass condition:

| Category | Example | Passes when |
| --- | --- | --- |
| Grounded | mean temperature in Huye last year | figure matches the database exactly, provenance shown |
| Unanswerable | soil pH in Musanze | declines, names what is missing |
| Advice | should I plant potatoes next month | declines, explains that SHAZA is unvalidated |
| Premise trap | what was the *observed* temperature in Musanze | corrects the premise: SHAZA holds reanalysis |

The last row is the best test SHAZA can run on itself. The premise is wrong in a way that is
invisible to a system that treats its own data casually, and correcting it requires the
provenance distinction to have survived the whole stack. A system that answers it with a number
and no correction has lost the project's central rule, and the eval will say so in one line.

Build this with the eval guidance in the Claude API skill rather than improvising a harness.

## 7. RAG, embeddings and the one honest corpus

SHAZA stores numbers. Retrieval over its own data is SQL, and wrapping SQL in embeddings would be
a worse database.

There is one real corpus, flagged already in `docs/learning-path.md`: agronomic literature
backing the Layer 2 index definitions. Growing degree days, dry spell thresholds and rainfall
onset criteria all come from published work, and each needs a citation SHAZA can show. Retrieval
over those papers, with the Claude API's document citations returning the cited span and its
location, is RAG solving a provenance problem. That fits the project. Semantic search over daily
temperature readings does not.

## 8. When this gets built

Ask SHAZA's ceiling is its tools, and its tools' ceiling is the data. A conversational layer over
three weather endpoints is a worse product than three good endpoints with a chart. The gate:

1. Stages 2 and 3 complete, so there is history, more than one source, and a working dashboard.
2. At least five tools with real data behind them, including one outcome tool and one scenario
   tool. Below that there is not enough to be worth a conversation.
3. The eval set from section 6 written and runnable **before** the first tool is wired up.

Until all three hold, the honest version of Ask SHAZA is a search box over the existing endpoints,
and saying so is a better engineering result than shipping a chatbot that sounds agricultural.

## 9. Implementation notes for later

Recorded so the decision is not re-litigated from memory when the time comes. The backend is
Python, so this is the Anthropic Python SDK.

- Default model `claude-opus-5-5`; adaptive thinking; structured outputs through
  `output_config.format` with `messages.parse()` for validation.
- Tool definitions carry `strict: true` and `additionalProperties: false`.
- The SDK's tool runner (`client.beta.messages.tool_runner`) handles the loop; its per-turn hooks
  are where the numeric post-check from section 2 belongs.
- Verify all of the above against the Claude API skill at build time rather than against this
  note, which will be out of date by then.
