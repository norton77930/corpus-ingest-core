# Data Model: Semantic Summary Profiles

No artifact schema changes. No new file on disk, no new path, no new
`corpus_index` family. Everything below is in-process data plus one config key.

## `SummaryProfile` — the new frozen record

```python
@dataclass(frozen=True)
class SummaryProfile:
    name: str                     # "finance" | "learning-notes"
    chunk_system: str             # system message for summarize_chunk
    chunk_sections: str           # the "請包含：..." line of the chunk user prompt
    chunk_constraints: str        # the "限制：..." line of the chunk user prompt
    final_system: str             # system message for summarize_final
    final_sections: str           # the "請將...合併成整集摘要..." instruction line
    final_constraints: str        # the "限制：..." line of the final user prompt
    limitation_lines: tuple[str, ...]   # body rendered under "## 摘要限制"
    extractive_prompt_lines: tuple[str, ...]  # body of "## 待 LLM 深度摘要 Prompt"
```

Frozen, hashable, no methods that touch IO. The module imports `dataclasses` and
the repo's `errors` module and nothing else — that is what lets the registry be
tested without a provider, a network stub, or an `api_cost_ack`.

## Registry

```python
FINANCE = "finance"
LEARNING_NOTES = "learning-notes"
DEFAULT_SUMMARY_PROFILE = FINANCE
UNSET = object()                                   # "the key is absent", not "the key is empty"
SUMMARY_PROFILES: Mapping[str, SummaryProfile]     # exactly two entries in v1

def resolve_summary_profile(name: object = UNSET) -> SummaryProfile: ...
```

`resolve_summary_profile()` — called with nothing, or with `UNSET` — returns
`finance`. `None` does **not**: YAML's `summary_profile:` means the operator
wrote the key and left it empty, which is a different act from not writing it,
and conflating the two is a silent path back to the finance default. An unknown name raises
`UnknownSummaryProfileError` naming the invalid value and listing the known ones.
The lookup never falls back silently — a silent fallback to finance is the exact
failure mode Design Decision 6 exists to prevent.

## Profile content

### `finance` — reproduced byte-for-byte from today's source

| Field | Current source | Value |
| --- | --- | --- |
| `chunk_system` | `llm_provider.py:107-111` | 你是 podcast 逐字稿摘要器。只根據使用者提供的逐字稿片段摘要，所有重點盡量附 timestamp evidence，不要產生投資建議。 |
| `chunk_sections` | `llm_provider.py:215` | 請包含：主要內容、提到的人物 / 公司 / 股票 / 產業 / 地點 / 書籍 / 電影 / 餐廳、可引用片段、不確定事項。 |
| `chunk_constraints` | `llm_provider.py:216` | 限制：不要產生投資建議；所有判斷都要能回到逐字稿 timestamp。 |
| `final_system` | `llm_provider.py:130-134` | 你是 podcast 語意摘要器。根據 chunk summaries 整理整集摘要，不得產生投資建議，所有市場觀點、公司、人物與事件都要盡量附 timestamp evidence。 |
| `final_sections` | `llm_provider.py:235` | 請將以下 chunk summaries 合併成整集摘要，使用 Markdown，包含本集主題、市場觀點、台股觀點、美股觀點、總經觀點、提到的公司 / 股票 / 產業、人物 / 書 / 電影 / 音樂 / 餐廳 / 地點、生活閒聊、廣告 / 業配段落、時間軸摘要、可驗證引用、不確定事項。 |
| `final_constraints` | `llm_provider.py:236` | 限制：不要產生投資建議；所有重要判斷都要盡量附 timestamp evidence。 |
| `limitation_lines` | `semantic_summarizer.py:438-439` | 本摘要由 LLM 根據逐字稿產生。所有重點應盡量附 timestamp evidence。 / 本摘要不構成投資建議。 |
| `extractive_prompt_lines` | `summarizer.py:255-268` | 請根據本集逐字稿整理：1. 本集主題 … 7. 可驗證時間戳引用 + 限制兩行 |

These strings are moved, not rewritten. The regression test hardcodes them
independently so that a future edit to the registry cannot drift 股癌's output
without a test failing.

### `learning-notes` — the new shape

| Field | Value |
| --- | --- |
| `chunk_system` | 你是教學影片逐字稿摘要器。只根據使用者提供的逐字稿片段摘要，所有重點盡量附 timestamp evidence，不要補充逐字稿沒有的內容。 |
| `chunk_sections` | 請包含：主要內容、提到的觀念 / 方法 / 工具 / 名詞 / 人物 / 產品 / 書籍、可引用片段、不確定事項。 |
| `chunk_constraints` | 限制：不要補充逐字稿沒有的內容；所有判斷都要能回到逐字稿 timestamp。 |
| `final_system` | 你是教學影片語意摘要器。根據 chunk summaries 整理成一份可自學的學習筆記，所有觀念、步驟與範例都要盡量附 timestamp evidence，逐字稿沒說的一律放進不確定事項。 |
| `final_sections` | 請將以下 chunk summaries 合併成一份學習筆記，使用 Markdown，依序包含本片主題與適合誰看、核心觀念（每個觀念含「是什麼 / 為什麼重要 / 影片中怎麼說」）、可操作步驟與實際用法、常見錯誤用法 vs 正確用法、值得記住的名詞與工具、可直接複用的 prompt 或範例片段、時間軸摘要、可驗證引用、不確定事項。 |
| `final_constraints` | 限制：不要補充逐字稿沒有的內容；所有重要判斷都要盡量附 timestamp evidence；無法從逐字稿確認的一律寫進不確定事項。 |
| `limitation_lines` | 本摘要由 LLM 根據逐字稿產生。所有重點應盡量附 timestamp evidence。 / 本摘要僅整理影片內容，結論請回到 timestamp 驗證。 |
| `extractive_prompt_lines` | 請根據本片逐字稿整理：1. 本片主題 2. 核心觀念 3. 可操作步驟 4. 常見錯誤 5. 值得記住的名詞與工具 6. 可驗證時間戳引用 + 限制兩行 |

Note what both profiles share and why: 可引用片段, 不確定事項, and
"回到逐字稿 timestamp" appear in both. Those are Constitution Principle I and V
(evidence traceability, evidence-versus-inference separation), not finance
conventions, and FR-015 makes dropping them a spec violation rather than a
stylistic choice.

The `learning-notes` constraint replaces 不要產生投資建議 with
不要補充逐字稿沒有的內容. The failure mode being guarded against is different for
each shape — a finance summary invents a recommendation, a teaching summary
invents a step the speaker never described — and both are the same underlying
rule: do not exceed the evidence.

## `PodcastProfile` — the one additive change

```python
@dataclass(frozen=True)
class PodcastProfile:
    podcast_id: str
    display_name: str
    rss_url: str | None
    language: str
    default_episode_prefix: str | None
    source_type: str = "rss"                 # Spec 036
    summary_profile: str = "finance"         # Spec 037
```

Field order matters: `summary_profile` is appended after `source_type` so every
positional construction in existing code and tests keeps working.

`config._parse_profile` deliberately does **not** use the existing
`_optional_text` helper. That helper returns `None` for any non-string, so
routing `summary_profile: 123` through it would turn a typo into a silent
`finance` default — the exact failure this field exists to prevent. Instead the
raw value is passed straight to `resolve_summary_profile`, with `UNSET` as the
`dict.get` default so that an absent key is distinguishable from an explicit
null. That non-string trap is live today for `source_type` (`config.py:87`),
which is why the raw value is validated rather than the `_optional_text` output.

### `config/podcasts.yaml` after this change

```yaml
podcasts:
  gooaye:
    display_name: Gooaye 股癌
    rss_url: https://feeds.soundon.fm/podcasts/954689a5-3096-43a4-a80b-7810b219cef3.xml
    language: zh
    default_episode_prefix: EP
    # no summary_profile key -> finance, byte-identical to today
  x-raytar:
    display_name: "@Raytar (X)"
    source_type: x-video
    language: en
    summary_profile: learning-notes
```

## `create_provider` — the one signature change

```python
def create_provider(
    provider: str,
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "OPENAI_API_KEY",
    reasoning_effort: str | None = None,
    read_timeout_seconds: int = 120,
    api_cost_ack: str = "",
    summary_profile: str = DEFAULT_SUMMARY_PROFILE,   # new, keyword-only
) -> SemanticSummaryProvider: ...
```

Keyword-only with a default, appended last. `require_exact_api_cost_ack` stays
the first statement in the body — the profile is resolved **after** the ack
check, so an unknown profile name can never precede, mask, or substitute for an
ack failure. `tests/test_llm_provider_factory_boundary.py:78` pins `api_cost_ack`
as keyword-only with an empty default and stays green unmodified.

## The frozen envelope

Unchanged for every profile, because four downstream readers depend on it:

```text
# {display_name} - {episode_ref} 語意摘要

## Metadata
- Podcast / Podcast ID / Episode / Title / Transcript status / Segment count
- Last segment end / Summary mode: semantic-llm / Provider / Model / Chunk count

## 摘要限制
<-- profile.limitation_lines is the ONLY part that varies -->

[## Validation Warnings]
<final summary body>

## Chunk Summaries
### Chunk 1 ...
```

| Reader | Depends on |
| --- | --- |
| `semantic_review_artifact.py:143` | literal `## Chunk Summaries` |
| `semantic_review_artifact.py:151` | `Summary mode: semantic-llm`, `Provider:`, `Model:`, `Transcript status:` |
| `stock_lens_synthesis.py:494` | `re.split(r"(?im)^##\s+Chunk Summaries\s*$", ...)` |
| `verified_research_lineage.py:820` | `summary_mode == "semantic-llm"` |

`SUMMARY_MODE` stays `"semantic-llm"` for both profiles. The profile is a prompt
selector, not a new summary mode; changing the mode string would invalidate
every existing lineage record for no gain.

## Not modelled here

Deliberately absent, each for a reason recorded in `spec.md`:

- No per-run or per-episode profile override — one canonical summary path, one
  shape (spec Out of Scope; also confirmed by the `semantic_summarize_episode`
  signature pin at `tests/test_contracts.py:30`).
- No profile field on any artifact. The summary does not record which profile
  produced it. Adding it would be an unvalidated additive key of the kind
  Spec 036 Assumption 2 warned about, and nothing consumes it. If a consumer
  ever needs it, that is a spec, not a field snuck in here.
- No third profile, no profile inheritance, no composition.
