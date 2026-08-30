from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import PodcastIngestCoreError, run_x_video_ingest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把一支 X 影片取得成 corpus 音訊與逐字稿；預設為 dry-run。")
    parser.add_argument("--url", required=True, help="X 貼文網址")
    parser.add_argument("--confirm", action="store_true", help="實際下載並轉錄")
    parser.add_argument("--title", help="覆寫來源 metadata 的標題")
    parser.add_argument("--model", help="faster-whisper 模型名稱")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8", dest="compute_type")
    parser.add_argument("--force", action="store_true", help="覆蓋既有逐字稿")
    parser.add_argument(
        "--work-dir",
        dest="work_dir",
        help="影片暫存目錄；預設用系統暫存並在結束後刪除。影片不會寫進 data/。",
    )
    args = parser.parse_args(argv)

    try:
        result = run_x_video_ingest(
            args.url,
            confirm=args.confirm,
            title=args.title,
            model=args.model,
            device=args.device,
            compute_type=args.compute_type,
            force=args.force,
            work_dir=args.work_dir,
        )
    except (PodcastIngestCoreError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
