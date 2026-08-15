"""Definition-only offline probe; it neither loads nor registers a plugin."""
from __future__ import annotations

TERMINAL_STATUS = "BLOCKED_CREDENTIAL_SEAM"
OFFICIAL_LOADER_PROVED = False


def evaluate_offline_probe() -> tuple[str, bool]:
    """Return the only honest offline result for the unproved loader seam."""
    return TERMINAL_STATUS, OFFICIAL_LOADER_PROVED
