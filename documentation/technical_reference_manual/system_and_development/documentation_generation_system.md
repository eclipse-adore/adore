# Documentation build pipeline

This project uses a MkDocs-based documentation site under `documentation/`.  
This page explains **where the docs come from**, **which commands to run**, and **what is generated automatically**.

---

## Overview

There are three main parts to the documentation system:

1. A **MkDocs project** in `documentation/mkdocs/` (theme, navigation, static assets, etc.).
2. A set of **hand-written docs**:
   - `documentation/index.md` (canonical top-level index)
   - `documentation/technical_reference_manual/` (main manual)
3. A **generation script**, `documentation/mkdocs/gen_docs.py`, which:
   - Copies the canonical index into the MkDocs project.
   - Collects `README.md` files from the repository.
   - Drops them into `documentation/mkdocs/docs/generated/` in a structured way.

Everything is orchestrated via `just` recipes defined in the `Justfile` at the repo root.

---

## Quick commands

From the repo root:

- **Full docs build in CI-style container**

  ```bash
  just docs
  ```

This calls `.docker/scripts/run_docs.sh`, which builds the documentation inside the CI Docker image. Use this if you want a **clean, reproducible build** that matches CI.

* **Build docs using your local environment**

  ```bash
  just docs_build
  ```

  This runs the MkDocs pipeline directly under `documentation/` (no container). You need a working Python + MkDocs environment on your host.

* **Clean everything and rebuild**

  ```bash
  just docs_all
  ```

  Equivalent to:

  ```bash
  just docs_clean
  just docs_build
  ```

* **Serve the built docs locally**

  ```bash
  just docs_serve
  ```

  This runs a simple HTTP server in `documentation/docs` on port `8000`.
  Open `http://localhost:8000/` in your browser (the MkDocs site is under the `mkdocs/` subdirectory).

* **Clean generated / build artifacts**

  ```bash
  just docs_clean
  ```

* **Spellcheck & lint docs** (optional, requires Docker):

  ```bash
  just docs_spellcheck
  just docs_lint
  ```

  These use an `aspell` Docker image against the technical reference manual.

* **Watch docs and rebuild on changes** (requires `inotifywait`):

  ```bash
  just docs_watch
  ```

---

## What `docs_build` actually does

The main work happens in two layered recipes:

### 1. `docs_build_mkdocs`

In the `Justfile`:

```make
# Build mkdocs site into documentation/mkdocs/site
docs_build_mkdocs:
    cd "$DOCS_ROOT" && \
    mkdir -p mkdocs/docs && \
    rm -rf mkdocs/docs/generated mkdocs/site && \
    cp -r technical_reference_manual mkdocs/docs/technical_reference_manual && \
    python3 mkdocs/gen_docs.py && \
    cd mkdocs && mkdocs build
```

Step by step:

1. `cd "$DOCS_ROOT"`
   `DOCS_ROOT` is defined as `${WORKSPACE_ROOT}/documentation`, i.e. the `documentation/` directory in the repo root.

2. `mkdir -p mkdocs/docs`
   Ensure the MkDocs `docs/` directory exists.

3. `rm -rf mkdocs/docs/generated mkdocs/site`

   * Remove the previous **generated** docs subtree.
   * Remove the previous MkDocs **site** output.

4. `cp -r technical_reference_manual mkdocs/docs/technical_reference_manual`
   Copy the hand-written technical reference manual into the MkDocs `docs/` tree.
   Inside the MkDocs project, it appears under `docs/technical_reference_manual/`.

5. `python3 mkdocs/gen_docs.py`
   Run the documentation generation script (details below).
   This:

   * Copies `documentation/index.md` → `documentation/mkdocs/docs/index.md`.
   * Scans the entire repo for `README.md` files and copies them to `mkdocs/docs/generated/...`.

6. `cd mkdocs && mkdocs build`
   Run MkDocs, which:

   * Reads `mkdocs.yml` and the Markdown files in `mkdocs/docs/`.
   * Produces a static HTML site under `mkdocs/site/`.

### 2. `docs_build`

After `docs_build_mkdocs` completes:

```make
# Build docs/ tree from mkdocs output (gh-pages-ready)
docs_build: docs_build_mkdocs
    cd "$DOCS_ROOT" && \
    rm -rf docs && \
    mkdir -p docs && \
    cp -r mkdocs/site docs/mkdocs &&\
    cp -r mkdocs/img docs/mkdocs
```

This:

1. Removes any previous `documentation/docs/` directory.
2. Creates a fresh `documentation/docs/`.
3. Copies the built MkDocs site (`mkdocs/site/`) to `documentation/docs/mkdocs`.
4. Copies static images from `mkdocs/img` into `documentation/docs/mkdocs`.

The final, self-contained documentation tree is thus at:

```text
documentation/docs/mkdocs/
```

This is what `just docs_serve` serves, and it can also be used directly for publishing (e.g. to `gh-pages`).

---

## How `gen_docs.py` works

`gen_docs.py` lives in `documentation/mkdocs/` and is responsible for **gathering Markdown sources from the repo** into the MkDocs project.

Key paths:

* `MKDOCS_DIR = Path(__file__).resolve().parent`
  → `documentation/mkdocs/`

* `DOCS_DIR = MKDOCS_DIR / "docs"`
  → `documentation/mkdocs/docs/` (MkDocs content root)

* `GENERATED_DIR = DOCS_DIR / "generated"`
  → `documentation/mkdocs/docs/generated/`

* `REPO_ROOT = MKDOCS_DIR.parent.parent`
  → repo root (two levels up from `documentation/mkdocs/`)

* `SOURCE_INDEX = MKDOCS_DIR.parent / "index.md"`
  → `documentation/index.md` (canonical top-level index)

* `DEST_INDEX = DOCS_DIR / "index.md"`
  → `documentation/mkdocs/docs/index.md` (MkDocs landing page)

### 1. Ensuring `docs/` exists

```python
DOCS_DIR.mkdir(parents=True, exist_ok=True)
```

If `documentation/mkdocs/docs/` does not exist, it is created. This makes the script robust even if called before any other build step.

### 2. Copying the canonical index

```python
if SOURCE_INDEX.exists():
    DEST_INDEX.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_INDEX, DEST_INDEX)
```

* If `documentation/index.md` exists, it is copied to `documentation/mkdocs/docs/index.md`.
* This means **the canonical top-level documentation page lives in `documentation/`, not inside `mkdocs/`**.
* MkDocs sees this as the root `index.md` of the doc site.

If `documentation/index.md` is missing, the script logs a warning and skips this step.

### 3. Cleaning the `generated/` subtree

```python
if GENERATED_DIR.exists():
    shutil.rmtree(GENERATED_DIR)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
```

The `generated/` directory is **completely recreated** on each run:

* Anything under `documentation/mkdocs/docs/generated/` is considered **generated content** and will be removed.
* Do **not** hand-edit files there; changes will be overwritten on the next build.

### 4. Collecting `README.md` files

The script scans the repo for `README.md` files, with some directories excluded:

```python
SEARCH_ROOTS = [
    REPO_ROOT
]

IGNORE_DIR_NAMES = {
    ".git",
    ".github",
    ".gitlab",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    "build",
    "install",
    "log",
    "documentation",
    ".docker",
    ".venv",
}
```

The helper:

```python
def should_skip(path: Path) -> bool:
    return any(part in IGNORE_DIR_NAMES for part in path.parts)
```

* Any path whose **components** (directory names) include one of the ignore names is skipped.
* This prevents:

  * Git internals, IDE configs, Python caches, build and install artifacts, etc.
  * The `documentation/` tree itself (so we don’t recursively ingest docs into themselves).
  * The `.docker/` and `.venv/` directories.

The main loop:

```python
for root in SEARCH_ROOTS:
    if not root.exists():
        continue

    for readme in root.rglob("README.md"):
        if should_skip(readme):
            continue

        rel = readme.relative_to(REPO_ROOT)
        out_path = GENERATED_DIR / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(readme, out_path)
```

For each `README.md`:

1. It computes its path relative to the repo root (e.g. `src/nodes/foo/README.md`).
2. It copies the file to `documentation/mkdocs/docs/generated/src/nodes/foo/README.md`, preserving the directory structure under `generated/`.

**Result:**

* Every `README.md` in the repo (outside ignored directories) appears under `generated/` in the MkDocs docs tree.
* This makes it easy to surface local package docs in the website without duplicating content.

---

## What you should (and shouldn’t) edit

* **Edit by hand:**

  * `documentation/index.md` → top-level landing page.
  * `documentation/technical_reference_manual/**/*.md` → main manual.
  * Any other manually created `.md` files under `documentation/mkdocs/docs/` (except `generated/`).

* **Do not edit by hand:**

  * Anything under `documentation/mkdocs/docs/generated/` → regenerated from `README.md` files.
  * Anything under `documentation/docs/` → derived build artifacts.

* **To update package-level docs:**

  * Edit the relevant `README.md` in the package directory.
  * Rebuild docs: `just docs_build` (or `just docs`).

---

## Publishing and CI

* `just docs` is the recommended entry point for CI-style docs builds. It runs `.docker/scripts/run_docs.sh`, which uses the CI Docker image for a controlled environment.
* `just docs_publish_gh_pages` (wrapped by `just docs_publish`) calls `documentation/publish_gh-pages.sh` to push the built site to the `gh-pages` branch.
* Docs are also included in the broader CI flow via `just ci`, which runs tests and documentation together.

---

## Summary

* **MkDocs** drives the HTML site under `documentation/mkdocs/`.
* **Hand-written docs** live in `documentation/index.md` and `documentation/technical_reference_manual/`.
* **Generated docs** are created by `gen_docs.py` from repository `README.md` files and placed in `documentation/mkdocs/docs/generated/`.
* The main commands you will use are:

  ```bash
  just docs_build   # local build
  just docs_serve   # local preview on http://localhost:8000/
  just docs_all     # clean + build
  just docs         # build docs inside CI Docker image
  ```


