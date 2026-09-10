# Chronos

Chronos is a local-first Markdown version-history experiment. Its core idea is to keep document history inside the Markdown file itself, so the visible text and its Chronos history remain portable as one file.

## Public snapshot status

This repository intentionally separates two parts:

- `backend/` — working Python history core with tests.
- `frontend-prototype/` — a standalone React/Tiptap editor UI prototype. It is **not currently wired to the Python history core** and does not perform real filesystem persistence.

The public snapshot does not claim that the editor prototype and history engine form one finished application.

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
- strict Base64 validation and explicit malformed-payload errors.
- preservation of the user-authored Markdown text around Chronos metadata, including leading/trailing whitespace, empty documents, repeated trailing newlines, and LF/CRLF line endings.
- line-delimited JSON command interface on stdin/stdout.

The storage tests explicitly exercise the content-preservation invariant when Chronos metadata is added and replaced. Chronos operates on UTF-8 text; the claim is exact preservation of the Markdown text supplied to the storage layer, not arbitrary non-UTF-8 byte preservation.

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

## Editor UI prototype

`frontend-prototype/` demonstrates the intended editing surface separately from the history engine. It includes a file-list concept, a Tiptap rich-text editing surface, dirty/saved state, and an explicit integration-boundary indicator.

```bash
cd frontend-prototype
npm install
npm run build
npm run dev
```

The prototype intentionally keeps its sample documents in React state. Real file I/O and history-core integration are outside this public prototype.

## Verification

GitHub Actions checks both independent parts:

- Python: install the backend package and run `pytest`.
- TypeScript: install the editor-prototype dependencies and run the production build.

## Trade-offs

Embedding history in the document improves single-file portability, but increases file size and leaves machine-readable comments in the Markdown source. Chronos is an experiment in that trade-off, not a replacement for Git.

## License

Source-visible, all rights reserved. See [LICENSE](LICENSE). Third-party dependencies remain subject to their own licenses.