## What this changes

<!-- One or two sentences. What behaviour is different after this PR? -->

## Why

<!-- The problem this solves. If it fixes an issue, link it. -->

## Verification

Paste the actual output, not a claim that you ran it.

```
python -m pytest
python -m ruff check src tests scripts
python -m mypy
python -m compileall src scripts
```

- [ ] `python -m pytest` is **fully green**. There is no `--ignore` list and no
      expected-failure set; if something is red, say which and why.
- [ ] I ran the targeted guard tests for this change type. See
      [`docs/verification-matrix.md`](../blob/main/docs/verification-matrix.md).
- [ ] If this adds an MCP tool: it is appended **last**, Tools 1-N keep their
      slots, and `tests/test_mcp_tool_registry_contract.py` was updated
      deliberately.

## Product boundaries

[`CONTRIBUTING.md`](../blob/main/CONTRIBUTING.md) lists the rules that are not
up for discussion. Confirm this PR does not cross one:

- [ ] No investment advice, target price, or guaranteed return in any output.
- [ ] No live market data API.
- [ ] The deterministic and LLM paths stay separate; neither substitutes for
      the other.
- [ ] Any tool that writes, downloads, or spends money still defaults to
      `confirm=false` and returns a plan instead of acting.
- [ ] Nothing from `data/` or `.env` appears in the diff.

<!-- If this PR does cross one, delete the checkboxes and explain instead.
     That is a real conversation to have; silently crossing one is not. -->
