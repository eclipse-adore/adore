#!/usr/bin/env bash

set -euo pipefail

echoerr (){ printf "%s" "$@" >&2;}
exiterr (){ printf "%s\n" "$@" >&2; exit 1;}

SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SOURCE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/../../lib")"
BASE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/../..")"
IGNORE_FILE="$(realpath "${BASE_DIRECTORY}/.cmakeignore")"

cd "${SOURCE_DIRECTORY}"
#find . -exec sh -c "path=$(echo \"$0\" | sed \"s|^\./||\"); result=$(python \"${SCRIPT_DIRECTORY}/ignore.py\" \"$path\" \"$1\"); echo \"$path: $result\"" {} "$IGNORE_FILE" \;

while read -r file; do
    file=${file#$BASE_DIRECTORY/}
    echo -n "PATH: ${file} IGNORED: "
    python3 "${SCRIPT_DIRECTORY}/ignore.py" "${file}" "$IGNORE_FILE" && echo "false" || echo "true"
done < <(find ${SOURCE_DIRECTORY} -type f -or -type d)


