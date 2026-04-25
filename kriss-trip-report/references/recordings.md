# Recording And Transcript Workflow

Use this reference when the source materials include meeting recordings, audio files, or ZIP archives of recordings.

## Basic Rule

Recordings are supporting source material, but report facts must come from a reliable transcript or from written meeting materials. Do not draft technical conclusions directly from untranscribed audio.

## Accepted Inputs

The skill can inventory and prepare:

- Audio files: `.m4a`, `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`
- Recording ZIP archives containing audio files
- Transcript files: `.txt`, `.md`, `.srt`, `.vtt`
- ZIP archives containing both audio and transcript files

## Preparation

Run `scripts/prepare_recordings.py` when recordings or recording ZIPs are provided.

Inventory only:

```powershell
python scripts\prepare_recordings.py recordings.zip --output-dir run\recordings
```

Extract/copy files into a workspace:

```powershell
python scripts\prepare_recordings.py recordings.zip --output-dir run\recordings --extract
```

Outputs:

- `recording-index.md`: human-readable recording/transcript table and drafting cautions.
- `recording-manifest.json`: structured recording/transcript manifest.
- `audio/`: extracted/copied recordings when `--extract` is used.
- `transcripts/`: extracted/copied transcripts when `--extract` is used.

## Transcript Matching

The preparation script links recordings and transcripts by same or similar filename stem.

Recommended naming:

```text
meeting-day1-session1.m4a
meeting-day1-session1.txt
meeting-day1-session2.m4a
meeting-day1-session2.srt
```

If a recording has no matching transcript, the index marks it as not usable for report facts until transcribed.

## Transcription Boundary

Transcription conversion is handled outside this skill. When audio needs to be transcribed, use a separate transcription skill or approved speech-to-text tool, then provide the transcript files back to this workflow.

After external transcription, rerun `prepare_recordings.py` on the audio workspace and transcript folder so the manifest links recordings to transcript files:

```powershell
python scripts\prepare_recordings.py run\recordings\audio run\recordings\transcripts --output-dir run\recordings-linked
```

Only linked transcript files should be used as report sources.

## Drafting From Transcripts

When a transcript is available:

- Map transcript excerpts to agenda items by date, session number, slide title, speaker, or explicit agenda wording.
- Use transcript content to supplement written agenda, minutes, and presentation material.
- Prefer official agenda/minutes/presentation files when transcript text conflicts with written sources, unless the transcript clearly records a later decision or correction.
- Do not quote long transcript passages in the report. Summarize in Korean bullet style.
- Do not include uncertainty markers such as `녹취록 확인 필요` in the final report body.

When no transcript is available:

- Include the recording in the dossier/inventory only.
- Do not use the recording as a factual basis for the report body.
- Ask for a transcript or use a separate transcription skill/tool, then rerun `prepare_recordings.py` to link the generated transcript files.

## Final Report Treatment

In `수집자료`, list recordings only when they were actually used or supplied as meeting/report source material. A concise category such as `회의 녹음자료 및 전사본` is sufficient. Do not list each audio filename unless requested.

Do not put recordings under `출입국 입증 자료`; travel evidence is limited to airline tickets, boarding passes, immigration certificates, and similar travel proof documents.
