# Plan: offline-only closure

1. Seal credential feasibility, eligibility, runtime observation, G2-owned rollback, activation evaluation, and receipt projections in an observation module.
2. Reuse Spec030's closed vocabulary in a G2 plan. Model exact acknowledgement and a zero-side-effect boundary that returns before the fixed marker helper or caller-supplied driver while current gates remain blocked.
3. Add a scratch-only fixture and static probe contract. The probe records blocked feasibility, never a loader pass.
4. Add one offline CLI, a static final verifier, and a non-executed future runner. The final verifier has no runtime executor import/call.

Future live lease, driver, metadata inspection, and rollback execution are not implemented by this offline closure. The persistent marker helper uses a fixed internal path and remains unreachable while the credential/review gates block; it is never a caller-controlled path.
