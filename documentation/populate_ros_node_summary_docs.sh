#!/bin/bash

BASE_DIR="../ros2_workspace/src"
SUMMARY_README="technical_reference_manual/generated/ROS_NODES_SUMMARY.md"
mkdir -p "technical_reference_manual/generated"


echo "# ROS Nodes Summary" > "$SUMMARY_README"
echo "This document summarizes all of the ROS nodes in ADORe, always review each README.md for the complete documentation for a given node." >> "$SUMMARY_README"
echo "all ROS nodes are located in \`ros2_workspace/src\`" >> "$SUMMARY_README"
echo "" >> "$SUMMARY_README"

extract_summary() {
  local readme="$1"
  local summary=""
  
  if [[ -f "$readme" && -s "$readme" ]]; then
    summary=$(awk '
      /^#/ && found_first {exit}
      /^#/ && !found_first {found_first=1}
      {content = content $0 "\n"}
      END {
        gsub(/\n+$/, "", content)
        gsub(/\n/, " ", content)
        gsub(/[[:space:]]+/, " ", content)
        gsub(/^[[:space:]]*/, "", content)
        print content
      }
    ' "$readme")
  fi
  
  echo "$summary"
}

find "$BASE_DIR" -type f -iname "README.md" | while read -r readme; do
  node_dir=$(dirname "$readme")
  pkg_xml="$node_dir/package.xml"
  
  if [[ -f "$pkg_xml" ]]; then
    package_name=$(grep -oPm1 "(?<=<name>)[^<]+" "$pkg_xml")
    node_name=$(basename "$node_dir")
    relative_path=$(realpath --relative-to="$BASE_DIR" "$node_dir")
    summary=$(extract_summary "$readme")
    
    echo "## Package: $package_name" >> "$SUMMARY_README"
    echo "- Node: $node_name" >> "$SUMMARY_README"
    echo "- Location: $relative_path" >> "$SUMMARY_README"
    if [[ -n "$summary" ]]; then
      echo "- Summary: $summary" >> "$SUMMARY_README"
    fi
    echo "" >> "$SUMMARY_README"
  fi
done

echo "Summary generated in $SUMMARY_README"
