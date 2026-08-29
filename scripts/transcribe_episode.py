from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core.transcriber import DEFAULT_TRANSCRIPTION_MODEL, transcribe_episode


def main() -> None:
    parser = argparse.ArgumentParser(description="轉錄單一 podcast episode。")
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    parser.add_argument("--model")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument(
        "--compute-type",
        choices=["int8", "float16", "float32"],
        default="int8",
    )
    parser.add_argument("--vad-filter", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--audio-path", type=Path)
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("必須提供 --podcast 與 --episode，或 positional podcast_id episode_ref。")

    model_name = args.model or DEFAULT_TRANSCRIPTION_MODEL
    print(
        f"Loading faster-whisper model when needed: {model_name}, "
        f"device={args.device}, compute_type={args.compute_type}",
        file=sys.stderr,
    )
    if args.audio_path is not None:
        print(f"Transcribing audio: {args.audio_path}", file=sys.stderr)
    else:
        print(f"Resolving episode audio: {podcast_id}/{episode_ref}", file=sys.stderr)

    result = transcribe_episode(
        podcast_id,
        episode_ref,
        model=args.model,
        device=args.device,
        compute_type=args.compute_type,
        vad_filter=args.vad_filter,
        force=args.force,
        audio_path=args.audio_path,
        progress_callback=_print_progress,
    )
    if result.already_exists:
        print("Transcript outputs already exist; skipped. Use --force to rerun.", file=sys.stderr)
    else:
        print("Writing transcript outputs complete.", file=sys.stderr)
    print("Done.", file=sys.stderr)
    print(json.dumps(_asset_to_dict(result), ensure_ascii=False, indent=2))


def _asset_to_dict(asset):
    return {
        "podcast_id": asset.podcast_id,
        "episode_ref": asset.episode_ref,
        "title": asset.title,
        "model": asset.model,
        "language": asset.language,
        "device": asset.device,
        "compute_type": asset.compute_type,
        "vad_filter": asset.vad_filter,
        "audio_path": str(asset.audio_path),
        "text_path": str(asset.text_path),
        "srt_path": str(asset.srt_path),
        "json_path": str(asset.json_path),
        "segment_count": asset.segment_count,
        "transcribed": asset.transcribed,
        "already_exists": asset.already_exists,
    }


def _print_progress(segment_count: int, last_segment_end_seconds: float | None) -> None:
    last_end = (
        "unknown"
        if last_segment_end_seconds is None
        else f"{last_segment_end_seconds:.2f}s"
    )
    print(
        f"Transcribed segments: {segment_count}, last_end={last_end}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
