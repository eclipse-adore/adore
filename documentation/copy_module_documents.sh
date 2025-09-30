#!/usr/bin/env bash

SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SOURCE_DIRECTORY="$(realpath "${SCRIPT_DIRECTORY}/..")"

GENERATED_DIRECTORY="technical_reference_manual/generated/"
mkdir -p "${GENERATED_DIRECTORY}"


cp "${SOURCE_DIRECTORY}/CODE_OF_CONDUCT.md" "${GENERATED_DIRECTORY}"
cp "${SOURCE_DIRECTORY}/CONTRIBUTING.md" "${GENERATED_DIRECTORY}"
cp "${SOURCE_DIRECTORY}/NOTICE.md" "${GENERATED_DIRECTORY}"

cp -r "${SOURCE_DIRECTORY}/ros2_workspace/src/ros2_messages/adore_ros2_msgs" "${GENERATED_DIRECTORY}"


cp -r "${SOURCE_DIRECTORY}/ros2_workspace/src/interfaces/carla_bridge" "${GENERATED_DIRECTORY}"
cp -r "${SOURCE_DIRECTORY}/ros2_workspace/src/interfaces/sumo_bridge" "${GENERATED_DIRECTORY}"


mkdir -p "${GENERATED_DIRECTORY}"
cp -r "${SOURCE_DIRECTORY}/libraries" "${GENERATED_DIRECTORY}"

mkdir -p "${GENERATED_DIRECTORY}/api"
cp -r "${SOURCE_DIRECTORY}/tools/adore_api" "${GENERATED_DIRECTORY}/api"

mkdir -p "${GENERATED_DIRECTORY}/configuring_adore"
cp "${SOURCE_DIRECTORY}/adore.env" "${GENERATED_DIRECTORY}/configuring_adore/"
cp -r "${SOURCE_DIRECTORY}/configuring_adore.md" "${GENERATED_DIRECTORY}/configuring_adore/"


cp -r "${SOURCE_DIRECTORY}/tools/adore_cli" "${GENERATED_DIRECTORY}"


cp -r "${SOURCE_DIRECTORY}/vendor/adore_model_checker" "${GENERATED_DIRECTORY}"

mkdir -p "${GENERATED_DIRECTORY}/visualization"
cp -r "${SOURCE_DIRECTORY}/tools/lichtblick" "${GENERATED_DIRECTORY}/visualization"
rm -rf "${GENERATED_DIRECTORY}/visualization/lichtblick/lichtblick"

cp -r "${SOURCE_DIRECTORY}/THIRD-PARTY.md" "${GENERATED_DIRECTORY}"
cp -r "${SOURCE_DIRECTORY}/NOTICES.md" "${GENERATED_DIRECTORY}"


find "${GENERATED_DIRECTORY}" -type f ! \( -name '*.md' -o -name '*.yaml' -o -name '*.yml' -o -name '*.env' \) -delete

