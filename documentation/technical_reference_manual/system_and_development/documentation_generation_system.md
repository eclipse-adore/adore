# Documentation Generation

ADORe provides tools to generate all of the documentation described in the main [Documentation](documentation.md) page.

The documentation system produces a static site that combines:

* the landing/overview pages,
* the technical reference manual,
* the generated code reference under `generated/` (libraries, nodes, interfaces, vendor packages, tools, …).

The final site is written to `documentation/docs/` and is suitable for publishing via GitHub Pages.

## Building the documentation

You can build the docs either from the repository root (CI-style, via Docker) or directly inside the `documentation/` directory.

### Option A: from the repository root (recommended)

From the repo root:

```bash
make docs
```

This will:

1. build the CI Docker image (if needed),
2. run the documentation build inside that container,
3. produce the static site in:

   ```text
   documentation/docs/
   ```

This is the same pipeline used by CI, so it’s the best way to ensure reproducible builds.

### Option B: from the `documentation/` directory

If you have the tooling installed locally (MkDocs, Python, etc.), you can build without Docker:

```bash
cd adore/documentation
make build
```

This will:

* run the MkDocs generation step (including `mkdocs/gen_docs.py`, which populates `mkdocs/docs/generated/**` from the colcon workspace and related modules),
* copy the technical reference manual into `mkdocs/docs/technical_reference_manual`,
* run `mkdocs build` to produce `mkdocs/site`,
* assemble the final site into `docs/` (landing page + MkDocs output).

After this, `docs/` is equivalent to what `make docs` produces via Docker.

## Serving a local copy

To build and serve the documentation locally:

```bash
cd adore/documentation
make serve
```

This will:

1. run `make build` to refresh `docs/`,
2. start a simple HTTP server serving `docs/` on port `8000`.

Then open:

[http://localhost:8000](http://localhost:8000)

in your browser to view the documentation.

If you just want to serve an already-built copy without rebuilding:

```bash
cd adore/documentation/docs
python3 -m http.server 8000
```

## Spell checking

The documentation system uses **aspell** to lint the Markdown files.

Interactive spell-check session:

```bash
cd adore/documentation
make spellcheck
```

Non-interactive lint/spellcheck of all Markdown documents:

```bash
cd adore/documentation
make lint
```

Both targets use:

* a small Docker image containing aspell,
* a custom dictionary file: `.aspell.en.pws`.

You can add words to the dictionary either by editing `.aspell.en.pws` directly or by accepting them during an interactive spell-check session.

## Publishing to GitHub Pages (gh-pages)

To publish the documentation to GitHub Pages:

1. Fork the ADORe repository to your personal GitHub account or organisation.

2. Clone the fork locally.

3. In `adore/documentation`, edit the `publish.env` file to specify:

   * the branch to build documentation from,
   * the target remote for the `gh-pages` branch.

   You do **not** need to check out the source branch you are publishing from; the branch is defined in `publish.env`.

4. Run the publish target:

   ```bash
   cd adore/documentation
   make publish
   ```

   This pushes a branch called `gh-pages` containing only a `docs/` folder to the configured remote.

5. In GitHub, configure Pages to use that branch:

   * Go to `https://github.com/<username-or-organization>/adore/settings/pages`,
   * Select the `gh-pages` branch,
   * Set the folder to `docs/`.

6. Optionally, create a pull/merge request against the main ADORe repo to make this documentation active there.
   Before submitting, run:

   ```bash
   cd adore/documentation
   make lint
   ```

   to ensure the Markdown passes the spellcheck/lint step.
