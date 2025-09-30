import os
import sys
import subprocess
import fnmatch

# --- Config ---
REPO_ROOT = "/mnt"  # base used for relative paths & ignore file location
DIRECTORY_PATH = "/mnt/technical_reference_manual"
PERSONAL_DICT = ".aspell.en.pws"
IGNORE_FILE = os.path.join(REPO_ROOT, ".aspell.ignore")


def to_rel_from_repo(path: str) -> str:
    """Return a POSIX-style path relative to REPO_ROOT."""
    rel = os.path.relpath(path, REPO_ROOT)
    return rel.replace("\\", "/")  # normalize just in case


def load_ignore_lists(ignore_path):
    """
    Load ignore config.
    Lines starting with # or blank are ignored.
    - If a line looks like a path/pattern (contains '/' or glob chars *?), treat as a file pattern.
    - Otherwise treat as a word to ignore.
    """
    ignore_words = set()
    ignore_file_patterns = []

    if not os.path.exists(ignore_path):
        return ignore_words, ignore_file_patterns

    with open(ignore_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # normalize path-like entries to POSIX style (no leading ./)
            if "/" in line or "*" in line or "?" in line or line.endswith(".md"):
                pat = line.lstrip("./").replace("\\", "/")
                ignore_file_patterns.append(pat)
            else:
                ignore_words.add(line)
    return ignore_words, ignore_file_patterns


def file_is_ignored(file_path: str, patterns) -> bool:
    """Return True if file_path matches any ignore pattern (match against repo-relative path and basename)."""
    rel = to_rel_from_repo(file_path)
    base = os.path.basename(file_path)
    for pat in patterns:
        # try matching against relative path and filename
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(base, pat):
            return True
    return False


def spellcheck(file_path, ignore_words):
    """
    Checks a file for spelling errors using aspell, ignoring code blocks fenced with triple backticks
    and words from the ignore file.
    """
    temp_file = "/tmp/input.txt"
    trimmed_file_path = to_rel_from_repo(file_path)
    print(f"Spell checking file: {trimmed_file_path}")

    misspelled_count = 0
    in_code_block = False

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()

                # toggle fenced code blocks
                if stripped.startswith("```"):
                    in_code_block = not in_code_block
                    continue

                if in_code_block:
                    continue

                # write the single line for aspell
                with open(temp_file, "w", encoding="utf-8") as temp:
                    temp.write(line)

                try:
                    command = [
                        "aspell",
                        "list",
                        "--encoding=utf-8",
                        "--mode=markdown",
                        f"--home-dir={REPO_ROOT}",
                        f"--personal={PERSONAL_DICT}",
                    ]

                    with open(temp_file, "r", encoding="utf-8") as temp_input:
                        result = subprocess.run(
                            command,
                            stdin=temp_input,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                        )

                    if result.returncode != 0:
                        raise RuntimeError(f"Error running aspell: {result.stderr}")

                    misspelled_words = [w for w in result.stdout.splitlines() if w]

                    for word in misspelled_words:
                        if word not in ignore_words:
                            misspelled_count += 1
                            print(f"{trimmed_file_path}:{line_number}:misspelled word: {word}")
                            print(f"    line: {line.strip()}")

                except Exception as e:
                    print(f"Error processing line {line_number} in {file_path}: {e}")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"Error: {str(e)}")

    return misspelled_count


def main():
    total_misspelled = 0

    # Load ignore config
    ignore_words, ignore_file_patterns = load_ignore_lists(IGNORE_FILE)

    for root, dirs, files in os.walk(DIRECTORY_PATH):
        for name in files:
            if not name.endswith(".md"):
                continue
            file_path = os.path.join(root, name)

            # skip files matched by ignore patterns
            if file_is_ignored(file_path, ignore_file_patterns):
                print(f"Skipping (ignored): {to_rel_from_repo(file_path)}")
                continue

            total_misspelled += spellcheck(file_path, ignore_words)

    print(f"Total misspelled words: {total_misspelled}")
    if total_misspelled > 0:
        print(
            f"  Correct the spelling errors or add an exception to the aspell dictionary: {PERSONAL_DICT} "
            f"or add words/patterns to {IGNORE_FILE} and try again."
        )
        print("  Use `make spellcheck` for an interactive aspell session.")
        sys.exit(1)


if __name__ == "__main__":
    main()

