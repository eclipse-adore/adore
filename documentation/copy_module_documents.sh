#!/usr/bin/env bash

SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SOURCE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/..")"

GENERATED_DIRECTORY="technical_reference_manual/generated/"
mkdir -p "${GENERATED_DIRECTORY}"


cp "${SOURCE_DIRECTORY}/CODE_OF_CONDUCT.md" "${GENERATED_DIRECTORY}"
cp "${SOURCE_DIRECTORY}/CONTRIBUTING.md" "${GENERATED_DIRECTORY}"

cp -r "${SOURCE_DIRECTORY}/ros2_workspace/src/ros2_messages/adore_ros2_msgs" "${GENERATED_DIRECTORY}"

mkdir -p "${GENERATED_DIRECTORY}"
cp -r "${SOURCE_DIRECTORY}/libraries" "${GENERATED_DIRECTORY}"

mkdir -p "${GENERATED_DIRECTORY}/api"
cp -r "${SOURCE_DIRECTORY}/tools/adore_api" "${GENERATED_DIRECTORY}/api"


cp -r "${SOURCE_DIRECTORY}/tools/adore_cli" "${GENERATED_DIRECTORY}"

mkdir -p "${GENERATED_DIRECTORY}/visualization"
cp -r "${SOURCE_DIRECTORY}/tools/lichtblick" "${GENERATED_DIRECTORY}/visualization"
rm -rf "${GENERATED_DIRECTORY}/visualization/lichtblick/lichtblick"

find "${GENERATED_DIRECTORY}" -type f ! -name '*.md' -delete
