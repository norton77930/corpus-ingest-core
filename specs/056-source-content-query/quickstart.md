# Quickstart / acceptance

Use a prepared explicit identity. Call query_source_content(podcast_id="x-natewiki", episode_ref="2106893534980685927") to inspect. Copy returned source_version into expected_source_version for action="read", optionally start_seconds=1050,end_seconds=1230. Follow each next_cursor with identical scope/version until exhausted. For literal search use action="search",query="verification". A missing cache is irrelevant.

Hermes prompts: 「根據這支已準備的影片，說明他們如何驗證 agent，附時間戳。」or 「整理整集學習筆記，標示值得回聽的段落；未讀完請標示範圍。」Supply known identifiers when the conversation does not already contain them.

Owned pilot: set CORPUS_INGEST_DATA_DIR to .pytest-tmp/54m/data in a dedicated subprocess using repository venv; inspect/read/search existing medium transcript. Check input hashes before/after. Do not copy into default corpus, rebuild cache, rerun ASR or call providers. Actual environment variable name must follow local_env_names.py (the compatibility name is allowed only when supported).

Operator Hermes acceptance: mount this repo MCP and source-content-qa Skill, then exercise evidence, full/partial notes and language-mismatch prompts. Record actual tool trace, version/pages and output separately. SDK/synthetic tests do not substitute for this host check.

Learning-note format: edit [learning-notes-template.md](../../.agents/skills/source-content-qa/references/learning-notes-template.md) to maintain the default explanation depth and fields. The Skill reads it for note requests; source issues, reasoning and examples form the main text. AI explanations/examples are labelled, and project application is a separate optional field omitted by default. A one-time format request does not modify the saved template. Reload an already loaded Skill/reference, and synchronize both files when Hermes uses a separate copied Skill folder. Existing notes are not rewritten automatically.
