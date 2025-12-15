#!/usr/bin/env python3
import shutil
from pathlib import Path

# This file lives in documentation/mkdocs/
MKDOCS_DIR = Path(__file__).resolve().parent
DOCS_DIR = MKDOCS_DIR / "docs"
GENERATED_DIR = DOCS_DIR / "generated"

# Repo root = documentation/.. (one level up from documentation/)
REPO_ROOT = MKDOCS_DIR.parent.parent

# Canonical top-level index
SOURCE_INDEX = MKDOCS_DIR.parent / "index.md"      # documentation/index.md
DEST_INDEX = DOCS_DIR / "index.md"                 # mkdocs/docs/index.md

# Where to scan for README.md docs
SEARCH_ROOTS = [
    REPO_ROOT                                  # whole repo
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


def should_skip(path: Path) -> bool:
    """Return True if this path is inside a directory we want to ignore."""
    return any(part in IGNORE_DIR_NAMES for part in path.parts)


def main() -> None:
    # Ensure docs directory exists (Makefile usually does this, but be robust)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Copy canonical index into mkdocs/docs/index.md if it exists
    if SOURCE_INDEX.exists():
        DEST_INDEX.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_INDEX, DEST_INDEX)
        print(f"Copied {SOURCE_INDEX} -> {DEST_INDEX}")
    else:
        print(f"Warning: {SOURCE_INDEX} not found, skipping index.md copy")

    # Clean generated area but leave manually-written docs alone
    if GENERATED_DIR.exists():
        shutil.rmtree(GENERATED_DIR)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # Collect README.md files into docs/generated/...
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue

        for readme in root.rglob("README.md"):
            if should_skip(readme):
                continue

            # Compute path relative to repo root
            rel = readme.relative_to(REPO_ROOT)
            # Put it under docs/generated/... preserving structure
            out_path = GENERATED_DIR / rel
            out_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(readme, out_path)
            print(f"Copied {readme} -> {out_path}")


if __name__ == "__main__":
    main()
