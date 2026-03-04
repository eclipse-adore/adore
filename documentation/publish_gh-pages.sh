#!/usr/bin/env bash

set -euo pipefail

# Determine script directory for robust sourcing and path finding
SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Load configuration
if [ -f "${SCRIPT_DIRECTORY}/publish.env" ]; then
    source "${SCRIPT_DIRECTORY}/publish.env"
else
    echo "Error: publish.env not found in ${SCRIPT_DIRECTORY}"
    exit 1
fi

exiterr (){ printf "$@\n"; exit 1;}

CLONE_DIRECTORY=""

function cleanup {
  if [ -d "${CLONE_DIRECTORY}" ]; then
    rm -rf "${CLONE_DIRECTORY}"
    echo "Deleted temp working directory ${CLONE_DIRECTORY}"
  fi
}
trap cleanup EXIT

check_params() {
    echo "Please verify the following parameters:"
    echo "---------------------------------------"
    echo "PROHIBITED_REMOTES: $PROHIBITED_REMOTES"
    echo "DOCUMENTATION_SOURCE_BRANCH: $DOCUMENTATION_SOURCE_BRANCH (the branch which the documentaiton will originate from)"
    echo "PUBLISH_BRANCH: $PUBLISH_BRANCH (The branch that the generated docs directory will publish to)"
    echo "PUBLISH_DIRECTORY: $PUBLISH_DIRECTORY (The directory where docs will be published: 'docs' or '.' for root)"
    echo "PUBLISH_REMOTE: $PUBLISH_REMOTE (The repository uri where the documentaiton/gh-pages will be published)"
    echo "PUBLISH_COMMIT_MESSAGE: $PUBLISH_COMMIT_MESSAGE"
    echo "---------------------------------------"

    read -p "Are these values correct? (yes/no): " response
    if [[ "$response" != "yes" ]]; then
        echo "Exiting: Modify the 'publish.env' file and try again."
        exit 1
    fi
}

check_params

DOCS_SOURCE_DIRECTORY="${SCRIPT_DIRECTORY}/docs"

# Verify pre-built documentation exists
if [ ! -d "${DOCS_SOURCE_DIRECTORY}" ]; then
    exiterr "Error: Documentation directory '${DOCS_SOURCE_DIRECTORY}' not found.\nPlease run 'just docs' or 'just docs_all' to build the documentation before publishing."
fi

# The build process puts the site in documentation/docs/mkdocs.
# We want to publish the contents of that folder directly to the publish directory so the URL is clean.
if [ -d "${DOCS_SOURCE_DIRECTORY}/mkdocs" ]; then
    echo "Found 'mkdocs' subdirectory in docs. Using it as source."
    DOCS_SOURCE_DIRECTORY="${DOCS_SOURCE_DIRECTORY}/mkdocs"
fi

printf "Creating temporary workspace directory...\n"
CLONE_DIRECTORY="$(mktemp -d)"

git_url="${PUBLISH_REMOTE}"

if [[ $PROHIBITED_REMOTES == *"$git_url"* ]]; then
    exiterr "ERROR: Prohibited to publish to origin: ${git_url}, create a fork or change the origin and try again."
fi

read -p "Should the remote publish branch: ${PUBLISH_BRANCH} be deleted? (y/n): " answer
if [[ $answer == [Yy]* ]]; then
    echo "Deleting remote branch ${PUBLISH_BRANCH}..."
    git push "${PUBLISH_REMOTE}" --delete "${PUBLISH_BRANCH}" || true
fi

printf "Cloning adore to: ${CLONE_DIRECTORY}/adore\n"
# Clone depth 1 to save bandwidth, we only need to push back to it
git clone --depth 1 "${git_url}" "${CLONE_DIRECTORY}/adore"

cd "${CLONE_DIRECTORY}/adore"

echo "Preparing branch ${PUBLISH_BRANCH}..."
# Create orphan branch to start fresh each time (state of the art for gh-pages usually involves history, but this script seems to favor fresh state)
# If we wanted to keep history, we would fetch origin/$PUBLISH_BRANCH and checkout.
# Using orphan as it aligns with the 'start from scratch' / 'cleaning' approach of the original script.
git checkout --orphan "${PUBLISH_BRANCH}"
git rm -rf . > /dev/null 2>&1

# Prepare target directory
if [[ "${PUBLISH_DIRECTORY}" == "." ]]; then
    echo "Copying documentation to root..."
    cp -r "${DOCS_SOURCE_DIRECTORY}/"* .
else
    echo "Copying documentation to ${PUBLISH_DIRECTORY}..."
    mkdir -p "${PUBLISH_DIRECTORY}"
    cp -r "${DOCS_SOURCE_DIRECTORY}/"* "${PUBLISH_DIRECTORY}/"
fi

# Add .nojekyll to ensure folders starting with _ are not ignored
touch .nojekyll

git add .
git status

if git diff --staged --quiet; then
    echo "No changes to commit."
else
    git commit -m "${PUBLISH_COMMIT_MESSAGE}"
    echo "Pushing to ${PUBLISH_REMOTE} branch ${PUBLISH_BRANCH}..."
    git push --force origin "${PUBLISH_BRANCH}"
fi

echo "Documentation published successfully."
