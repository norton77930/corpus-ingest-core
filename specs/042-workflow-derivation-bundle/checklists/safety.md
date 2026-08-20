# Safety Checklist: Workflow Derivation Bundle

**Purpose**: Safety and data-boundary checks before implementation
**Created**: 2026-08-20
**Feature**: [spec.md](../spec.md)

## Research Boundary Checks

- [x] CHK001 Lecture claims stay in the 038 files; 05/06 do not quote speaker timestamps the lecture does not have
- [x] CHK002 Reconstructed prompt catalogues and operator-application mappings are labelled, not presented as speaker quotes
- [x] CHK003 External/market status is unused and not described as market fact

## LLM, Secret, and Investment Safety

- [x] CHK004 LLM input is lecture + operator context only; transcript is forbidden; exact `api_cost_ack` required
- [x] CHK005 `.env`, API keys, tokens, and provider secrets are not printed, committed, or returned
- [x] CHK006 no buy/sell/hold, target price, guaranteed return, or personalized investment advice

## Family Separation

- [x] CHK007 `study_guide` availability does not depend on 05/06
- [x] CHK008 `workflow_derivation` available only when both 05 and 06 are readable
- [x] CHK009 finance/gooaye episodes are refused; lecture bytes unchanged
