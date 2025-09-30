#!/usr/bin/env bash
# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0
#
# SPDX-License-Identifier: EPL-2.0
# ********************************************************************************


set -euo pipefail

echoerr (){ printf "%s" "$@" >&2;}
exiterr (){ printf "%s\n" "$@" >&2; exit 1;}

usage() {
    echo "Usage: $0 [PACKAGE_NAME]"
    echo "  PACKAGE_NAME: Optional. If specified, only build this package and its local dependencies"
    echo "  If not specified, build all packages in the workspace"
    exit 1
}

SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_DIRECTORY=$(realpath "${SCRIPT_DIRECTORY}/../../.log")
export ROSDEP_PATH=${LOG_DIRECTORY}/.ros/rosdep
export ROSDEP_DB_PATH=${LOG_DIRECTORY}/.ros/rosdep

[[ -z "$ROS_DISTRO" ]] && exiterr "ERROR: ROS_DISTRO not set."
[[ -z "$OS_CODE_NAME" ]] && exiterr "ERROR: OS_CODE_NAME not set."

TARGET_PACKAGE="${1:-}"
if [[ "$TARGET_PACKAGE" == "-h" ]] || [[ "$TARGET_PACKAGE" == "--help" ]]; then
    usage
fi

ros2_workspace="$(realpath "${SCRIPT_DIRECTORY}/..")"

declare -A package_info
declare -A local_packages

parse_package_xml() {
    local package_xml="$1"
    local package_dir="$(dirname "$package_xml")"
    local package_name="$(basename "$package_dir")"
    
    local name version description maintainer_name maintainer_email
    local build_depends exec_depends
    
    name=$(xmllint --xpath "string(//package/name)" "$package_xml" 2>/dev/null || echo "$package_name")
    version=$(xmllint --xpath "string(//package/version)" "$package_xml" 2>/dev/null || echo "0.0.0")
    description=$(xmllint --xpath "string(//package/description)" "$package_xml" 2>/dev/null || echo "ROS 2 package")
    
    maintainer_name=$(xmllint --xpath "string(//package/maintainer)" "$package_xml" 2>/dev/null || echo "Unknown")
    maintainer_email=$(xmllint --xpath "string(//package/maintainer/@email)" "$package_xml" 2>/dev/null || echo "unknown@example.com")
    
    build_depends=$(xmllint --xpath "//package/build_depend/text()" "$package_xml" 2>/dev/null | tr '\n' ' ' || echo "")
    exec_depends=$(xmllint --xpath "//package/exec_depend/text()" "$package_xml" 2>/dev/null | tr '\n' ' ' || echo "")
    
    package_info["${name}:name"]="$name"
    package_info["${name}:version"]="$version" 
    package_info["${name}:description"]="$description"
    package_info["${name}:maintainer_name"]="$maintainer_name"
    package_info["${name}:maintainer_email"]="$maintainer_email"
    package_info["${name}:build_depends"]="$build_depends"
    package_info["${name}:exec_depends"]="$exec_depends"
    package_info["${name}:directory"]="$(realpath "$package_dir")"
    
    local_packages["$name"]="$(realpath "$package_dir")"
}

get_local_dependencies() {
    local package_name="$1"
    local all_deps="${package_info[${package_name}:build_depends]} ${package_info[${package_name}:exec_depends]}"
    local local_deps=""
    
    for dep in $all_deps; do
        if [[ -n "${local_packages[$dep]:-}" ]]; then
            local_deps="$local_deps $dep"
        fi
    done
    
    echo "$local_deps"
}

get_all_dependencies() {
    local package_name="$1"
    local -A visited
    local -a deps_list
    
    collect_deps() {
        local pkg="$1"
        [[ "${visited[$pkg]:-}" == "1" ]] && return
        visited["$pkg"]=1
        
        local direct_deps=$(get_local_dependencies "$pkg")
        for dep in $direct_deps; do
            collect_deps "$dep"
            deps_list+=("$dep")
        done
    }
    
    collect_deps "$package_name"
    deps_list+=("$package_name")
    
    printf '%s\n' "${deps_list[@]}" | sort -u
}

topological_sort() {
    local packages_to_sort=("$@")
    local -A visited in_stack
    local -a result
    
    visit() {
        local node="$1"
        [[ "${in_stack[$node]:-}" == "1" ]] && exiterr "Circular dependency detected involving $node"
        [[ "${visited[$node]:-}" == "1" ]] && return
        
        in_stack["$node"]=1
        
        local deps=$(get_local_dependencies "$node")
        for dep in $deps; do
            for pkg in "${packages_to_sort[@]}"; do
                if [[ "$dep" == "$pkg" ]]; then
                    visit "$dep"
                    break
                fi
            done
        done
        
        in_stack["$node"]=0
        visited["$node"]=1
        result+=("$node")
    }
    
    for package in "${packages_to_sort[@]}"; do
        visit "$package"
    done
    
    printf '%s\n' "${result[@]}"
}

setup_local_rosdep() {
    mkdir -p "${ROSDEP_PATH}/sources.list.d"

    if [[ ! -f "${ROSDEP_PATH}/sources.list.d/20-default.list" ]]; then
        wget -q https://raw.githubusercontent.com/ros/rosdistro/master/rosdep/sources.list.d/20-default.list -P "${ROSDEP_PATH}/sources.list.d"
    fi

    export ROSDEP_SOURCE_PATH="${ROSDEP_PATH}/sources.list.d"
    export ROSDEP_DATABASE_PATH="${ROSDEP_PATH}/db"

    rosdep update --rosdistro=${ROS_DISTRO} >/dev/null 2>&1 || true
}

build_package() {
    local package_name="$1"
    cd "$ros2_workspace"
    colcon build --parallel-workers $(nproc) --packages-select "$package_name"
}

resolve_system_dependencies() {
    local package_name="$1"
    local all_deps="${package_info[${package_name}:build_depends]} ${package_info[${package_name}:exec_depends]}"
    local system_deps=""
    
    for dep in $all_deps; do
        if [[ -z "${local_packages[$dep]:-}" ]]; then
            local resolved=$(rosdep resolve "$dep" --rosdistro="$ROS_DISTRO" --os="ubuntu:$OS_CODE_NAME" 2>/dev/null || echo "")
            [[ -n "$resolved" ]] && system_deps="$system_deps, $resolved"
        fi
    done
    
    echo "$system_deps"
}

generate_debian_control_file() {
    local package_directory="$1"
    local package_name="$(basename "$package_directory")"
    local debian_package_name="ros-$ROS_DISTRO-$(echo "$package_name" | sed 's/_/-/g')"
    
    cd "$package_directory"
    
    [[ ! -f "LICENSE" ]] && touch "LICENSE"
    
    mkdir -p debian
    
    local system_deps=$(resolve_system_dependencies "$package_name")
    local local_deps=$(get_local_dependencies "$package_name")
    local debian_deps="$system_deps"
    
    for local_dep in $local_deps; do
        local local_debian_name="ros-$ROS_DISTRO-$(echo "$local_dep" | sed 's/_/-/g')"
        debian_deps="$debian_deps, $local_debian_name"
    done
    
    cat > debian/control << EOF
Source: $debian_package_name
Section: misc
Priority: optional
Maintainer: ${package_info[${package_name}:maintainer_name]} <${package_info[${package_name}:maintainer_email]}>
Build-Depends: debhelper (>= 9), cmake, python3, python3-setuptools$debian_deps
Standards-Version: 3.9.6

Package: $debian_package_name
Architecture: any
Depends: \${shlibs:Depends}, \${misc:Depends}$debian_deps
Description: ${package_info[${package_name}:description]}
 ROS 2 package for $ROS_DISTRO distribution.
EOF

    cat > debian/changelog << EOF
$debian_package_name (${package_info[${package_name}:version]}-1) unstable; urgency=low

  * Release version ${package_info[${package_name}:version]}

 -- ${package_info[${package_name}:maintainer_name]} <${package_info[${package_name}:maintainer_email]}>  $(date -R)
EOF

    echo "10" > debian/compat

    cat > debian/rules << 'EOF'
#!/usr/bin/make -f

%:
	dh $@

override_dh_auto_configure:
	colcon build --merge-install --install-base debian/tmp

override_dh_auto_build:
	colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release

override_dh_auto_install:
	colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release --install-base debian/tmp
	dh_install

override_dh_auto_test:
	echo "No test step needed for this package."
EOF

    chmod +x debian/rules
}

generate_debian_package() {
    local package_directory="$1"
    local package_name="$(basename "$package_directory")"
    local debian_package_name="ros-$ROS_DISTRO-$(echo "$package_name" | sed 's/_/-/g')"
    local build_dir="$ros2_workspace/build"
    local package_build_dir="$build_dir/debian_packages/$package_name"
    
    mkdir -p "$package_build_dir"
    
    cd "$package_directory"
    generate_debian_control_file "$package_directory"
    
    [[ ! -f "debian/rules" ]] && exiterr "debian/rules file not found"

    bloom-generate rosdebian --os-name ubuntu --os-version "$OS_CODE_NAME" --ros-distro "$ROS_DISTRO" >/dev/null 2>&1 || true
    fakeroot debian/rules binary
    
    local parent_dir="$(dirname "$package_directory")"
    
    echo "Moving generated debian packages to build directory..."
    
    shopt -s nullglob
    local files=("$parent_dir"/*.deb "$parent_dir"/*.ddeb "$parent_dir"/*.changes "$parent_dir"/*.buildinfo)
    local dirs=("$parent_dir"/.obj-*/)
    shopt -u nullglob
    
    for file in "${files[@]}"; do
        [[ -f "$file" ]] && mv "$file" "$package_build_dir/"
    done
    
    for dir in "${dirs[@]}"; do
        [[ -d "$dir" ]] && mv "$dir" "$package_build_dir/"
    done
    
    shopt -s nullglob
    local deb_files=("$package_build_dir"/*.deb)
    shopt -u nullglob
    
    [[ ${#deb_files[@]} -eq 0 ]] && exiterr "No .deb package found"
    
    echo "Generated packages for $package_name:"
    for file in "$package_build_dir"/*; do
        [[ -f "$file" ]] && echo "  $(basename "$file")"
    done
    
    rm -rf debian
    [[ -f "LICENSE" ]] && [[ ! -s "LICENSE" ]] && rm -f "LICENSE"
}

setup_local_rosdep

cd "$ros2_workspace"

for package_xml in $(find src -name "package.xml"); do
    parse_package_xml "$package_xml"
done

if [[ -n "$TARGET_PACKAGE" ]]; then
    if [[ -z "${local_packages[$TARGET_PACKAGE]:-}" ]]; then
        exiterr "Package '$TARGET_PACKAGE' not found in workspace"
    fi
    
    echo "Building single package: $TARGET_PACKAGE with its dependencies"
    packages_to_build=($(get_all_dependencies "$TARGET_PACKAGE"))
else
    echo "Building all packages in workspace"
    packages_to_build=("${!local_packages[@]}")
fi

build_order=($(topological_sort "${packages_to_build[@]}"))

echo "Build order: ${build_order[*]}"

for package_name in "${build_order[@]}"; do
    package_directory="${local_packages[$package_name]}"
    
    echo "Processing: $package_name"
    echo "  Directory: $package_directory"
    echo "  Version: ${package_info[${package_name}:version]}"
    echo "  Dependencies: $(get_local_dependencies "$package_name")"
    
    build_package "$package_name"
    generate_debian_package "$package_directory"
done

echo "All debian packages are available in: $ros2_workspace/build/debian_packages/"
