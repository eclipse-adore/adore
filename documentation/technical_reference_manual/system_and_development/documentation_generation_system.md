# Documentation Generation
ADORe provides tools to generate all of the documentation detailed in the 
[documentation](documentaiton.md) readme.

## Usage: Documentation Generation
1. cd to the adore documentation directory:
    ```bash
    cd adore/documentation
    ```
2. Call the build target:
    ```bash
    make build
    ```

## Usage: Serving local copy
You can build and serve the documentation locally by running the provide `make
serve` target. Navigate to the documentation directory and run the following:
```bash
cd adore/documentation
make serve
```

Once built the documents will be available at
[http://localhost 🔗](http://localhost) 

> **ℹ️INFO:**
> This will build and serve the documentation locally using a docker nginx image

## Usage: Spell Checking
The documentation system uses aspell to "lint" the markdown files
To do an interactive spell checking session use the provided make target:
```
make spellcheck
```
To non-interactively lint/spellcheck all markdown documents run:
```
make lint
```

The spell checker (aspell) and lint targets use a custom dictionary: `.aspell.en.pws`

Words can be added to the dictionary to provide exceptions by directly editing this file
or by running an interactive spell checking session as explained previously.


## Usage: Publication (to gh-pages)
Steps to publish documentation to gh-pages:

1. Fork the ADORe repo to your personal GitHub 

2. Clone the repo locally

3. Modify the `publish.env` file to specify an originating branch 
> **ℹ️INFO:**
> You do not need to check out the branch you wish the documentation originate from.
> The source branch of the gh-pages/documentation is defined in `publish.env`

4. Run the publication Make target:
```
make publish
```

This will push a branch called `gh-pages` containing only a `docs` folder
to the `origin` remote

5. Configure GitHub to use the branch as a "GitHub Pages"
You have to enable `gh-pages` on the `docs` directory in order for the publication
to be active. Visit `https://github.com/<username/orginization>/adore/settings/pages` to
configure gh-pages.

6. Optionally, create a pull/merge request to make this documentation active on the 
primary ADORe repo. Make sure to lint the markdown with `make lint` before 
submitting a pull/merge request.

