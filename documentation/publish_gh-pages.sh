#!/usr/bin/env bash

#set -euo pipefail

exiterr (){ printf "$@\n"; exit 1;}

trap cleanup EXIT

source publish.env

function cleanup {
  #rm -rf "${CLONE_DIRECTORY}"
  echo "Deleted temp working directory ${CLONE_DIRECTORY}"
}

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

SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DOCS_DIRECTORY="${SCRIPT_DIRECTORY}/docs"

printf "Creating temporary workspace directory...\n"
CLONE_DIRECTORY="$(mktemp -d)"

git_url="${PUBLISH_REMOTE}"

if [[ $PROHIBITED_REMOTES == *"$git_url"* ]]; then
    exiterr "ERROR: Prohibited to publish to origin: ${git_url}, create a fork or change the origin and try again."
fi

read -p "Should the remote publish branch: ${PUBLISH_BRANCH} be deleted? (y/n): " answer
if [[ $answer == [Yy]* ]]; then
    git push ${PUBLISH_REMOTE} --delete "${PUBLISH_BRANCH}" || true
    git branch -d "${PUBLISH_BRANCH}" || true
fi

cd "${CLONE_DIRECTORY}"
printf "Cloning adore to: ${CLONE_DIRECTORY}/adore\n"
git clone --depth 1 --single-branch -b "${DOCUMENTATION_SOURCE_BRANCH}" "${git_url}"

cd ${CLONE_DIRECTORY}/adore
git checkout --orphan "${PUBLISH_BRANCH}"

# Build documentation block
{
    cd ${CLONE_DIRECTORY}/adore/documentation
    
    echo "Building documentation in ${PWD}..."
    
    # Justfile logic: docs_build_mkdocs
    mkdir -p mkdocs/docs
    rm -rf mkdocs/docs/generated mkdocs/site
    
    cp -r technical_reference_manual mkdocs/docs/technical_reference_manual
    
    echo "Generaring docs with gen_docs.py..."
    python3 mkdocs/gen_docs.py
    
    echo "Running mkdocs build..."
    (cd mkdocs && mkdocs build)

    # Justfile logic: docs_build
    rm -rf docs
    mkdir -p docs
    cp -r mkdocs/site docs/mkdocs
    cp -r mkdocs/img docs/mkdocs
    cp -r mkdocs/stylesheets docs/mkdocs
    cp -r mkdocs/overrides docs/mkdocs
} || exiterr "Documentation build failed"

cd ${CLONE_DIRECTORY}/adore
git reset
pwd
git status

if [[ "${PUBLISH_DIRECTORY}" == "." ]]; then
    cp -r ${CLONE_DIRECTORY}/adore/documentation/docs/* .
    git add . --force
else
    # Ensure parent directory exists if nested
    mkdir -p $(dirname "${PUBLISH_DIRECTORY}")
    
    # If PUBLISH_DIRECTORY exists, we might want to clear it or just overwrite.
    # The original script did mv, which implies the target should probably be replaced or filled.
    # Since we are in a fresh orphan branch or clean state (mostly), we can just move.
    rm -rf "${PUBLISH_DIRECTORY}"
    mv ${CLONE_DIRECTORY}/adore/documentation/docs "${PUBLISH_DIRECTORY}"
    git add "${PUBLISH_DIRECTORY}" --force
fi

git commit -am "${PUBLISH_COMMIT_MESSAGE}"

git remote add publish "${PUBLISH_REMOTE}"
git push --force --set-upstream publish "${PUBLISH_BRANCH}" | true
git push publish "${PUBLISH_BRANCH}"
