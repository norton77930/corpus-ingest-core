"""Regenerate the committed synthetic sample corpus under ``examples/sample-corpus/``.

Everything this script produces is fiction. The podcast, both episodes, the two
hosts, and every company, price and statistic in the transcripts were written
for a software demo. No real show, transcript, or audio file is reproduced here,
and nothing in the corpus is investment advice.

Why a generator instead of checked-in JSON: a hand-written artifact drifts from
the real schema the moment the pipeline changes, and a drifted fixture is worse
than none because an agent learns the wrong shape from it. So only the *first*
stage is authored by hand -- the transcript segments, which are the pipeline's
upstream input -- and every downstream artifact is produced by calling the same
core functions the real pipeline calls: ``summarize_episode``,
``extract_mentions``, ``rebuild_cache``.

The transcript artifacts themselves are serialized by the transcriber's own
writer (``transcriber._write_transcript_outputs``) rather than by a copy of it
living here. Reaching past the underscore is deliberate: the alternative is a
second implementation of the TXT/SRT/JSON schema in this file, which is exactly
the drift the corpus exists to avoid. If that writer's signature changes, this
script must fail loudly, and it will.

There is no audio. The corpus starts at the transcript stage, so ``data/audio/``
stays empty and no ``.mp3`` or ``.wav`` is ever committed. The transcript JSON
still records where audio *would* live, which is what the real pipeline writes.

Run it from anywhere::

    python examples/generate_sample_corpus.py

It chdirs to the repository root and points ``CORPUS_INGEST_DATA_DIR`` and
``CORPUS_INGEST_CONFIG`` at ``examples/sample-corpus/`` using relative paths, so
the artifacts never record an absolute path from the machine that built them and
the repository's own ``data/`` is never touched. Re-running deletes and rebuilds
the tree; see ``examples/README.md`` for the two fields that legitimately differ
between runs.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CORPUS_DIR = Path("examples") / "sample-corpus"
SAMPLE_DATA_DIR = SAMPLE_CORPUS_DIR / "data"
SAMPLE_CONFIG_PATH = SAMPLE_CORPUS_DIR / "podcasts.yaml"

PODCAST_ID = "sample"
TRANSCRIPTION_MODEL = "synthetic"
TRANSCRIPTION_LANGUAGE = "en"
TRANSCRIPTION_DEVICE = "none"
TRANSCRIPTION_COMPUTE_TYPE = "none"


@dataclass(frozen=True)
class SyntheticEpisode:
    """One hand-written fictional episode: the only authored stage in the corpus."""

    episode_ref: str
    title: str
    lines: tuple[tuple[float, float, str], ...]


SAMPLE_001 = SyntheticEpisode(
    episode_ref="SAMPLE-001",
    title="Harbour Robotics and the GPU hour",
    lines=(
        (
            0.0,
            9.0,
            "Welcome to The Synthetic Signal. Everything in this feed is invented: the companies, the numbers, the hosts, and this warning.",
        ),
        (
            9.0,
            21.0,
            "I am Ada Kestrel, and across the desk is Milo Vance. Neither of us exists, and none of this is investment advice.",
        ),
        (
            21.0,
            37.5,
            "Today we are talking about Harbour Robotics, a fictional company that builds picking arms for fictional warehouses.",
        ),
        (
            37.5,
            56.0,
            "Harbour Robotics published an invented quarterly note last week, claiming its arms now run their models entirely on-device.",
        ),
        (
            56.0,
            76.5,
            "On-device means no round trip to a rented server, and that changes what a GPU hour is worth to a company like Harbour Robotics.",
        ),
        (
            76.5,
            99.0,
            "Let us put an imaginary number on it. In this made-up market a rented GPU hour costs forty-one dollars.",
        ),
        (
            99.0,
            123.5,
            "Harbour Robotics says it burned eleven thousand GPU hours last quarter training its grasp model.",
        ),
        (
            123.5,
            150.0,
            "That is an invented four hundred and fifty-one thousand dollars, which is an invented rounding error for an invented company.",
        ),
        (
            150.0,
            178.5,
            "The interesting part is not the bill. It is that they moved the AI workload off rented capacity and onto hardware they own.",
        ),
        (
            178.5,
            209.0,
            "Northwind Logistics, another company we made up, went the other way and rents every hour it uses.",
        ),
        (
            209.0,
            241.5,
            "Northwind Logistics runs roughly six hundred fictional trucks and leases all of its AI capacity by the hour.",
        ),
        (
            241.5,
            276.0,
            "Which approach is better? We do not know. This show does not exist, so we are not going to pretend to know.",
        ),
        (
            276.0,
            312.5,
            "What we can do is leave a timestamp on every sentence, so you can check what was actually said instead of what you remember.",
        ),
        (312.5, 351.0, "After the break: Meridian Grid, a fictional utility that nobody should model anything on."),
        (
            351.0,
            391.5,
            "Meridian Grid announced an invented tariff change that lifts the price of overnight power by nine percent.",
        ),
        (391.5, 434.0, "For Harbour Robotics that matters, because in this story their charging fleet runs overnight."),
        (
            434.0,
            478.5,
            "It is a second-order effect, and it only shows up if you can search a transcript instead of trusting your memory of it.",
        ),
        (478.5, 525.0, "Milo, if you had to summarise the fictional quarter in one line, what would it be?"),
        (
            525.0,
            573.5,
            "Harbour Robotics bought certainty, Northwind Logistics bought flexibility, and Meridian Grid quietly repriced both of them.",
        ),
        (573.5, 624.0, "None of which happened. We are a test fixture with a microphone."),
        (
            624.0,
            676.0,
            "That is the whole point of this sample corpus: search it, cite it, and remember that every word was written for a demo.",
        ),
        (
            676.0,
            722.5,
            "Next episode we will invent a CPI print and pretend to care about it. Thanks for listening to nobody.",
        ),
    ),
)

SAMPLE_002 = SyntheticEpisode(
    episode_ref="SAMPLE-002",
    title="Northwind Logistics and the CPI print",
    lines=(
        (0.0, 10.5, "This is episode two of The Synthetic Signal, and like episode one it is completely fabricated."),
        (
            10.5,
            24.0,
            "Ada Kestrel here with Milo Vance. Every company, price and statistic in this episode was invented for a software demo.",
        ),
        (
            24.0,
            42.5,
            "Northwind Logistics reported an invented eleven percent drop in spot freight rates this quarter.",
        ),
        (
            42.5,
            64.0,
            "Spot rates are what you pay when you did not book ahead, which in this made-up market is most of the time.",
        ),
        (64.0, 88.5, "The invented CPI print for the quarter came in at two point four percent."),
        (88.5, 114.0, "Milo, does a fictional CPI print tell you anything at all about fictional freight?"),
        (114.0, 142.5, "Not directly. Fuel is a much bigger input than the CPI basket we invented would suggest."),
        (
            142.5,
            173.0,
            "Our made-up GDP figure grew one point one percent, which in this fantasy counts as a soft landing.",
        ),
        (
            173.0,
            205.5,
            "Harbour Robotics turns up here too, because Northwind Logistics is a fictional customer of theirs.",
        ),
        (205.5, 239.0, "They bought two hundred imaginary picking arms and claim a thirty percent throughput gain."),
        (239.0, 274.5, "A claim like that is exactly the kind of thing you want a timestamp attached to."),
        (274.5, 312.0, "Meridian Grid, our invented utility, raised overnight power prices again in this storyline."),
        (
            312.0,
            352.5,
            "That pushes Northwind Logistics towards daytime charging, which collides with their invented delivery windows.",
        ),
        (352.5, 395.0, "The AI scheduling system they lease is supposed to solve exactly that, in this fiction."),
        (
            395.0,
            440.5,
            "It costs them a fictional nineteen dollars per GPU hour, billed monthly, and it is not clear it earns that back.",
        ),
        (
            440.5,
            488.0,
            "That is the show. None of it is real, none of it is advice, and all of it carries a timestamp you can check.",
        ),
    ),
)

EPISODES: tuple[SyntheticEpisode, ...] = (SAMPLE_001, SAMPLE_002)


def main() -> int:
    _prepare_environment()

    # Imported only after the environment is set: storage.DATA_DIR and
    # config.DEFAULT_CONFIG_PATH are both read at import time, so an earlier
    # import would bind the repository's own data/ and config/podcasts.yaml.
    from corpus_ingest_core import cache, entity_extractor, storage, summarizer, validator

    _reset_corpus(storage)
    storage.ensure_data_directories()

    for episode in EPISODES:
        paths = _write_transcript(episode)
        print(f"[transcript] {episode.episode_ref}: {len(episode.lines)} segments -> {paths.json_path}")

        validation = validator.validate_transcript(PODCAST_ID, episode.episode_ref)
        if validation.status != "valid":
            print(
                f"transcript for {episode.episode_ref} is {validation.status}: {'; '.join(validation.problems)}",
                file=sys.stderr,
            )
            return 1

        summary = summarizer.summarize_episode(PODCAST_ID, episode.episode_ref, force=True)
        print(f"[summary]    {episode.episode_ref}: {summary.summary_path}")

        mentions = entity_extractor.extract_mentions(PODCAST_ID, episode.episode_ref, force=True)
        print(f"[mentions]   {episode.episode_ref}: {mentions.mention_count} mentions -> {mentions.mentions_json_path}")

    rebuilt = cache.rebuild_cache(podcast_id=PODCAST_ID, force=True)
    print(
        f"[cache]      {rebuilt.indexed_episode_count} episodes indexed, "
        f"{rebuilt.skipped_episode_count} skipped -> {rebuilt.db_path}"
    )
    for problem in rebuilt.problems:
        print(f"[cache] problem: {problem}", file=sys.stderr)
    if rebuilt.problems:
        return 1

    print(f"\nSample corpus regenerated under {SAMPLE_DATA_DIR.as_posix()} (all content is fictional).")
    return 0


def _prepare_environment() -> None:
    """Bind the corpus roots to relative paths, before any core import."""

    os.chdir(REPO_ROOT)
    # Relative on purpose. An absolute value here would be baked into the
    # committed transcript JSON and SQLite cache as a path from whichever
    # machine ran the generator.
    os.environ["CORPUS_INGEST_DATA_DIR"] = SAMPLE_DATA_DIR.as_posix()
    os.environ["CORPUS_INGEST_CONFIG"] = SAMPLE_CONFIG_PATH.as_posix()
    sys.path.insert(0, str(REPO_ROOT / "src"))


def _reset_corpus(storage) -> None:
    """Delete the generated tree so a re-run is a clean overwrite, not a merge."""

    if storage.DATA_DIR.exists():
        shutil.rmtree(storage.DATA_DIR)


def _write_transcript(episode: SyntheticEpisode):
    from corpus_ingest_core import storage, transcriber
    from corpus_ingest_core.models import AudioAsset

    paths = storage.transcript_asset_paths(PODCAST_ID, episode.episode_ref, episode.title)
    # The audio path is recorded but never created: this corpus starts at the
    # transcript stage. size_bytes stays None because the file does not exist,
    # which is exactly what the real writer records for a missing source.
    audio_asset = AudioAsset(
        podcast_id=PODCAST_ID,
        episode_ref=episode.episode_ref,
        title=episode.title,
        source_url="synthetic:no-audio",
        local_path=storage.audio_asset_path(PODCAST_ID, episode.episode_ref, episode.title, ".mp3"),
    )
    transcriber._write_transcript_outputs(
        paths=paths,
        audio_asset=audio_asset,
        model_name=TRANSCRIPTION_MODEL,
        language=TRANSCRIPTION_LANGUAGE,
        device=TRANSCRIPTION_DEVICE,
        compute_type=TRANSCRIPTION_COMPUTE_TYPE,
        vad_filter=False,
        segments=[
            {"id": index, "start": start, "end": end, "text": text}
            for index, (start, end, text) in enumerate(episode.lines, start=1)
        ],
        completed=True,
    )
    return paths


if __name__ == "__main__":
    raise SystemExit(main())
