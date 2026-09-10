# Chronos

Chronos is a local-first Markdown version-history experiment. Its core idea is to keep document history inside the Markdown file itself, so the visible text and its Chronos history remain portable as one file.

## Public snapshot status

This repository intentionally separates two parts:

- `backend/` — working Python history core with tests.
- `frontend-prototype/` — a desktop-editor prototype kept as a separate design artifact. It is **not currently wired to the Python history core**.

The public snapshot does not claim that the desktop editor and history engine form one finished application.

## History core

The Python core stores a compressed history payload in HTML comments at the end of a Markdown file. The visible Markdown remains readable by ordinary tools.

Supported operations:

- `save_version` — append a new logical version when the visible content changes.
- `get_history` — list stored versions.
- `get_content` — reconstruct a selected version from the base text and patches.

Implementation highlights:

- `diff-match-patch` for incremental text history.
- 7z payload compression with an in-memory extraction limit.
- locator + chunk tags for embedded payload addressing.
- atomic replacement through a temporary file and `os.replace`.
- explicit errors for missing or malformed payloads.
- line-delimited JSON command interface on stdin/stdout.

### Development

Requires Python 3.12 or later.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
python -m chronos
```

Example command:

```json
{"command":"save_version","params":{"file_path":"/tmp/example.md","content":"# Hello"}}
```

The command process returns one JSON response per input line.

## Desktop editor prototype

`frontend-prototype/` demonstrates the intended desktop editing experience separately from the history engine. It is useful as UI/desktop application work, but the current public snapshot treats it as a prototype rather than claiming end-to-end Chronos integration.

## Trade-offs

Embedding history in the document improves single-file portability, but increases file size and leaves machine-readable comments in the Markdown source. Chronos is an experiment in that trade-off, not a replacement for Git.

## License

Source-visible, all rights reserved. See [LICENSE](LICENSE). Third-party dependencies remain subject to their own licenses.