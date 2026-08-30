from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import GooayeLensConfigError, load_gooaye_lens_model


def main() -> None:
    parser = argparse.ArgumentParser(description="檢查本機 Gooaye Lens model config 並輸出 JSON metadata。")
    parser.add_argument("--path", default="config/gooaye_lens.yaml")
    args = parser.parse_args()

    try:
        model = load_gooaye_lens_model(args.path)
    except GooayeLensConfigError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    print(json.dumps(_model_to_dict(model), ensure_ascii=False, indent=2))


def _model_to_dict(model):
    return {
        "version": model.version,
        "name": model.name,
        "description": model.description,
        "dimension_count": len(model.dimensions),
        "dimensions": [asdict(dimension) for dimension in model.dimensions],
        "safety_rules": model.safety_rules,
    }


if __name__ == "__main__":
    main()
