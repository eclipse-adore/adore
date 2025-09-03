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

#!/usr/bin/env python3
"""
eclipse_header_check.py - Eclipse copyright header checker with detailed reporting and ignore file support
Supports C++, Python, and Shell script files

Scans the source directory for c++, python and shell scripts and checks if the 
source files have license documentation headers.

"""
import os
import re
import argparse
import sys
import fnmatch
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple

class EclipseHeaderChecker:
    def __init__(self, ignore_file: Optional[Path] = None):
        self.current_year = datetime.now().year
        
        # Your specific Eclipse patterns (now case-insensitive and comment-agnostic)
        self.eclipse_patterns = [
            re.compile(r'copyright.*contributors to the eclipse foundation', re.IGNORECASE),
            re.compile(r'eclipse public license', re.IGNORECASE),
            re.compile(r'epl-2\.0', re.IGNORECASE),
            re.compile(r'www\.eclipse\.org', re.IGNORECASE),
            re.compile(r'spdx-license-identifier:\s*epl-2\.0', re.IGNORECASE),
            re.compile(r'see the notice file', re.IGNORECASE),
        ]
        
        # Extended file extensions
        self.file_extensions = {
            '.cpp', '.hpp', '.h', '.cc', '.cxx', '.hxx', '.c',  # C/C++
            '.py',  # Python
            '.sh', '.bash'  # Shell scripts
        }
        
        # Comment styles by file extension
        self.comment_styles = {
            '.cpp': 'cpp', '.hpp': 'cpp', '.h': 'cpp', '.cc': 'cpp', 
            '.cxx': 'cpp', '.hxx': 'cpp', '.c': 'cpp',
            '.py': 'python',
            '.sh': 'shell', '.bash': 'shell'
        }
        
        # Header templates for different comment styles
        self.header_templates = {
            'cpp': """/********************************************************************************
 * Copyright (c) {year} Contributors to the Eclipse Foundation
 *
 * See the NOTICE file(s) distributed with this work for additional
 * information regarding copyright ownership.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * https://www.eclipse.org/legal/epl-2.0
 *
 * SPDX-License-Identifier: EPL-2.0
 ********************************************************************************/

""",
            'python': """# ********************************************************************************
# Copyright (c) {year} Contributors to the Eclipse Foundation
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

""",
            'shell': """# ********************************************************************************
# Copyright (c) {year} Contributors to the Eclipse Foundation
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

"""
        }
        
        # Load ignore patterns
        self.ignore_patterns = self._load_ignore_patterns(ignore_file)
        
    def _get_comment_style(self, file_path: Path) -> str:
        """Get comment style for file based on extension"""
        ext = file_path.suffix.lower()
        return self.comment_styles.get(ext, 'cpp')  # Default to C++ style
        
    def _load_ignore_patterns(self, ignore_file: Optional[Path]) -> List[str]:
        """Load ignore patterns from file"""
        patterns = []
        
        if ignore_file and ignore_file.exists():
            try:
                with open(ignore_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        
                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue
                            
                        patterns.append(line)
                        
                print(f"📋 Loaded {len(patterns)} ignore patterns from {ignore_file}")
                if patterns:
                    print("   Ignore patterns:")
                    for pattern in patterns:
                        print(f"     • {pattern}")
                
            except Exception as e:
                print(f"⚠️  Warning: Could not read ignore file {ignore_file}: {e}")
                
        return patterns
    
    def _should_ignore_file(self, file_path: Path, base_path: Path) -> Tuple[bool, Optional[str]]:
        """Check if file should be ignored based on patterns"""
        if not self.ignore_patterns:
            return False, None
            
        # Get relative path for pattern matching
        try:
            relative_path = file_path.relative_to(base_path)
        except ValueError:
            # File is outside base_path, don't ignore
            return False, None
            
        relative_str = str(relative_path)
        absolute_str = str(file_path)
        
        for pattern in self.ignore_patterns:
            # Handle different pattern types
            if self._matches_pattern(relative_str, pattern) or self._matches_pattern(absolute_str, pattern):
                return True, pattern
                
        return False, None
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches ignore pattern"""
        # Convert path separators to forward slashes for consistent matching
        path = path.replace('\\', '/')
        pattern = pattern.replace('\\', '/')
        
        # Handle different pattern types
        if pattern.startswith('/'):
            # Absolute pattern from root
            pattern = pattern[1:]
            return fnmatch.fnmatch(path, pattern) or path.startswith(pattern)
        elif '/' in pattern:
            # Pattern with directory structure
            return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, f"*/{pattern}")
        else:
            # Simple filename or directory pattern
            parts = path.split('/')
            return any(fnmatch.fnmatch(part, pattern) for part in parts) or fnmatch.fnmatch(path, f"*/{pattern}") or fnmatch.fnmatch(path, pattern)
    
    def _extract_shebang(self, content: str) -> Tuple[Optional[str], str]:
        """Extract shebang line if present. Returns (shebang, remaining_content)"""
        lines = content.split('\n', 1)
        if lines[0].startswith('#!'):
            shebang = lines[0] + '\n'
            remaining = lines[1] if len(lines) > 1 else ''
            return shebang, remaining
        return None, content
    
    def _detect_existing_headers(self, content: str, comment_style: str) -> List[Tuple[int, int, str]]:
        """Detect existing header comment blocks. Returns list of (start_pos, end_pos, header_text)"""
        headers = []
        
        if comment_style == 'cpp':
            return self._detect_cpp_headers(content)
        else:
            return self._detect_hash_headers(content)
    
    def _detect_cpp_headers(self, content: str) -> List[Tuple[int, int, str]]:
        """Detect C++ style /* */ headers"""
        headers = []
        lines = content.split('\n')
        i = 0
        
        # Skip initial whitespace and single-line comments
        while i < len(lines) and (not lines[i].strip() or lines[i].strip().startswith('//')):
            i += 1
        
        # Look for block comments at the beginning of the file
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for start of block comment
            if line.startswith('/*'):
                header_lines = []
                start_line = i
                header_lines.append(lines[i])
                i += 1
                
                # Find the end of this block comment
                while i < len(lines):
                    header_lines.append(lines[i])
                    if '*/' in lines[i]:
                        end_line = i
                        header_text = '\n'.join(header_lines)
                        
                        # Check if this looks like a header
                        if self._looks_like_header(header_text):
                            # Calculate character positions
                            start_pos = sum(len(lines[j]) + 1 for j in range(start_line))
                            end_pos = start_pos + len(header_text)
                            headers.append((start_pos, end_pos, header_text))
                        
                        i += 1
                        break
                    i += 1
                
                # Skip whitespace after header
                while i < len(lines) and not lines[i].strip():
                    i += 1
            else:
                # If we hit non-comment content, stop looking for headers
                break
        
        return headers
    
    def _detect_hash_headers(self, content: str) -> List[Tuple[int, int, str]]:
        """Detect # style headers (Python/Shell)"""
        headers = []
        lines = content.split('\n')
        i = 0
        
        # Skip shebang if present
        if lines and lines[0].startswith('#!'):
            i = 1
        
        # Skip initial whitespace
        while i < len(lines) and not lines[i].strip():
            i += 1
        
        # Look for consecutive comment lines that form a header
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this line starts a potential header block
            if line.startswith('#') and not line.startswith('#!'):
                header_lines = []
                start_line = i
                
                # Collect consecutive comment lines
                while i < len(lines):
                    current_line = lines[i].strip()
                    if current_line.startswith('#') or not current_line:  # Allow empty lines in header
                        header_lines.append(lines[i])
                        i += 1
                    else:
                        break
                
                # Remove trailing empty lines from header
                while header_lines and not header_lines[-1].strip():
                    header_lines.pop()
                
                if header_lines:
                    header_text = '\n'.join(header_lines)
                    
                    # Check if this looks like a header
                    if self._looks_like_header(header_text):
                        # Calculate character positions
                        start_pos = sum(len(lines[j]) + 1 for j in range(start_line))
                        end_pos = start_pos + len(header_text)
                        headers.append((start_pos, end_pos, header_text))
                
                # Skip whitespace after header
                while i < len(lines) and not lines[i].strip():
                    i += 1
            else:
                # If we hit non-comment content, stop looking for headers
                break
        
        return headers
    
    def _looks_like_header(self, text: str) -> bool:
        """Determine if a comment block looks like a copyright/license header"""
        text_lower = text.lower()
        
        # Look for common header keywords
        header_keywords = [
            'copyright', 'license', 'licensed', 'spdx', 'apache', 'mit', 'gpl', 'bsd',
            'eclipse', 'contributors', 'authors', 'notice', 'terms', 'conditions',
            'permission', 'granted', 'software', 'foundation', 'all rights reserved'
        ]
        
        # If it contains multiple header keywords, it's likely a header
        keyword_count = sum(1 for keyword in header_keywords if keyword in text_lower)
        return keyword_count >= 2
    
    def _remove_headers_from_content(self, content: str, comment_style: str) -> Tuple[str, List[str], Optional[str]]:
        """Remove existing headers from content. Returns (cleaned_content, removed_headers, shebang)"""
        # Extract shebang for shell scripts
        shebang = None
        if comment_style == 'shell':
            shebang, content = self._extract_shebang(content)
        
        headers = self._detect_existing_headers(content, comment_style)
        
        if not headers:
            return content, [], shebang
        
        # Remove headers from end to start to maintain positions
        cleaned_content = content
        removed_headers = []
        
        for start_pos, end_pos, header_text in reversed(headers):
            removed_headers.insert(0, header_text)
            # Remove the header and any trailing whitespace
            before = cleaned_content[:start_pos]
            after = cleaned_content[end_pos:]
            
            # Remove extra newlines that might be left
            after = after.lstrip('\n')
            cleaned_content = before + after
        
        # Clean up any remaining leading whitespace
        cleaned_content = cleaned_content.lstrip()
        
        return cleaned_content, removed_headers, shebang
    
    def check_file_header(self, file_path: Path, verbose: bool = False) -> Tuple[bool, str, Dict]:
        """Check if file has proper Eclipse header and return detailed info"""
        details = {
            'has_copyright': False,
            'has_eclipse_foundation': False,
            'has_epl_license': False,
            'has_spdx': False,
            'has_notice_reference': False,
            'header_lines': 0,
            'file_size': 0,
            'first_lines': [],
            'existing_headers': [],
            'multiple_headers': False,
            'comment_style': self._get_comment_style(file_path),
            'has_shebang': False
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                details['file_size'] = len(content)
                
                # Check for shebang
                if content.startswith('#!'):
                    details['has_shebang'] = True
                
                # Detect existing headers
                existing_headers = self._detect_existing_headers(content, details['comment_style'])
                details['existing_headers'] = [header_text for _, _, header_text in existing_headers]
                details['multiple_headers'] = len(existing_headers) > 1
                
                # Read first 30 lines for header check
                lines = content.split('\n')
                header_lines = lines[:30]
                details['header_lines'] = len(header_lines)
                
                # Store first 5 lines for display
                details['first_lines'] = [line.rstrip() for line in lines[:5]]
                
                header_content = '\n'.join(header_lines)
                
                # Check individual components
                if re.search(r'copyright', header_content, re.IGNORECASE):
                    details['has_copyright'] = True
                
                if re.search(r'contributors to the eclipse foundation', header_content, re.IGNORECASE):
                    details['has_eclipse_foundation'] = True
                
                if re.search(r'eclipse public license', header_content, re.IGNORECASE):
                    details['has_epl_license'] = True
                
                if re.search(r'spdx-license-identifier:\s*epl-2\.0', header_content, re.IGNORECASE):
                    details['has_spdx'] = True
                
                if re.search(r'see the notice file', header_content, re.IGNORECASE):
                    details['has_notice_reference'] = True
                
                # Check if all required components are present
                required_components = [
                    details['has_copyright'],
                    details['has_eclipse_foundation'],
                    details['has_epl_license'],
                    details['has_spdx']
                ]
                
                has_valid_header = all(required_components)
                
                if has_valid_header and not details['multiple_headers']:
                    return True, "Valid Eclipse header found", details
                elif has_valid_header and details['multiple_headers']:
                    return False, "Valid Eclipse header found but multiple headers detected", details
                elif details['multiple_headers']:
                    return False, "Multiple headers detected", details
                else:
                    missing = []
                    if not details['has_copyright']:
                        missing.append("copyright")
                    if not details['has_eclipse_foundation']:
                        missing.append("Eclipse Foundation reference")
                    if not details['has_epl_license']:
                        missing.append("Eclipse Public License")
                    if not details['has_spdx']:
                        missing.append("SPDX-License-Identifier")
                    
                    return False, f"Missing: {', '.join(missing)}", details
                
        except Exception as e:
            return False, f"Error reading file: {e}", details
    
    def add_or_replace_header_in_file(self, file_path: Path, year: int = None) -> Tuple[bool, str]:
        """Add or replace Eclipse header in file"""
        try:
            if year is None:
                year = self.current_year
                
            comment_style = self._get_comment_style(file_path)
            
            # Read existing content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove existing headers
            cleaned_content, removed_headers, shebang = self._remove_headers_from_content(content, comment_style)
            
            # Generate new header
            header = self.header_templates[comment_style].format(year=year)
            
            # Reconstruct file content
            final_content = ""
            if shebang:
                final_content += shebang
            final_content += header + cleaned_content
            
            # Write the final content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            # Return success with details about what was done
            if removed_headers:
                if len(removed_headers) == 1:
                    return True, "Replaced existing header"
                else:
                    return True, f"Replaced {len(removed_headers)} existing headers"
            else:
                return True, "Added new header"
            
        except Exception as e:
            return False, f"Error modifying file: {e}"
    
    def find_files(self, directory: Path, recursive: bool = True) -> Tuple[List[Path], List[Tuple[Path, str]]]:
        """Find all supported files in directory, returning (included_files, ignored_files)"""
        included_files = []
        ignored_files = []
        
        if recursive:
            for ext in self.file_extensions:
                for file_path in directory.rglob(f'*{ext}'):
                    should_ignore, pattern = self._should_ignore_file(file_path, directory)
                    if should_ignore:
                        ignored_files.append((file_path, pattern))
                    else:
                        included_files.append(file_path)
        else:
            for ext in self.file_extensions:
                for file_path in directory.glob(f'*{ext}'):
                    should_ignore, pattern = self._should_ignore_file(file_path, directory)
                    if should_ignore:
                        ignored_files.append((file_path, pattern))
                    else:
                        included_files.append(file_path)
        
        return sorted(included_files), ignored_files
    
    def print_file_report(self, file_path: Path, base_path: Path, has_header: bool, 
                         message: str, details: Dict, verbose: bool = False):
        """Print detailed report for a single file"""
        relative_path = file_path.relative_to(base_path)
        status = "✅" if has_header else "❌"
        
        print(f"\n{status} {relative_path}")
        print(f"   Size: {details['file_size']} bytes")
        print(f"   Type: {details['comment_style']} style")
        if details['has_shebang']:
            print(f"   Shebang: Yes")
        print(f"   Status: {message}")
        
        # Show existing headers info
        if details['existing_headers']:
            print(f"   Existing Headers: {len(details['existing_headers'])}")
            if details['multiple_headers']:
                print(f"   ⚠️  Multiple headers detected!")
        
        if verbose or not has_header:
            print(f"   Header Analysis:")
            print(f"     Copyright: {'✅' if details['has_copyright'] else '❌'}")
            print(f"     Eclipse Foundation: {'✅' if details['has_eclipse_foundation'] else '❌'}")
            print(f"     EPL License: {'✅' if details['has_epl_license'] else '❌'}")
            print(f"     SPDX Identifier: {'✅' if details['has_spdx'] else '❌'}")
            print(f"     NOTICE Reference: {'✅' if details['has_notice_reference'] else '❌'}")
        
        if not has_header and details['first_lines']:
            print(f"   First few lines:")
            for i, line in enumerate(details['first_lines'], 1):
                if line.strip():
                    print(f"     {i:2}: {line[:80]}")
                else:
                    print(f"     {i:2}: (empty)")
        
        # Show existing headers if multiple or if verbose
        if details['existing_headers'] and (verbose or details['multiple_headers']):
            print(f"   Existing header(s) preview:")
            for i, header in enumerate(details['existing_headers'], 1):
                # Show first line of each header
                first_line = header.split('\n')[0] if header else "(empty)"
                print(f"     Header {i}: {first_line[:60]}...")
    
    def print_ignored_files_report(self, ignored_files: List[Tuple[Path, str]], base_path: Path):
        """Print report of ignored files"""
        if not ignored_files:
            return
            
        print(f"\n🚫 Ignored Files ({len(ignored_files)}):")
        print("-" * 40)
        
        # Group by pattern
        by_pattern = {}
        for file_path, pattern in ignored_files:
            if pattern not in by_pattern:
                by_pattern[pattern] = []
            by_pattern[pattern].append(file_path)
        
        for pattern, files in by_pattern.items():
            print(f"   Pattern: '{pattern}' ({len(files)} files)")
            for file_path in sorted(files):
                print(f"     • {file_path.relative_to(base_path)}")
    
    def scan_directory(self, directory: Path, fix: bool = False, verbose: bool = False) -> Dict:
        """Scan directory for header compliance with detailed reporting"""
        
        print(f"🔍 Scanning directory: {directory.absolute()}")
        print(f"📁 Looking for extensions: {', '.join(sorted(self.file_extensions))}")
        if self.ignore_patterns:
            print(f"🚫 Using {len(self.ignore_patterns)} ignore patterns")
        print("=" * 80)
        
        files, ignored_files = self.find_files(directory)
        
        # Categorize files by type
        cpp_files = [f for f in files if f.suffix.lower() in {'.cpp', '.hpp', '.h', '.cc', '.cxx', '.hxx', '.c'}]
        py_files = [f for f in files if f.suffix.lower() == '.py']
        shell_files = [f for f in files if f.suffix.lower() in {'.sh', '.bash'}]
        
        results = {
            'total': len(files),
            'ignored': len(ignored_files),
            'cpp_files': len(cpp_files),
            'py_files': len(py_files),
            'shell_files': len(shell_files),
            'valid': 0,
            'missing': 0,
            'multiple_headers': 0,
            'fixed': 0,
            'replaced': 0,
            'errors': 0,
            'missing_files': [],
            'multiple_header_files': [],
            'error_files': [],
            'ignored_files': ignored_files,
            'file_details': []
        }
        
        if results['total'] == 0:
            if results['ignored'] > 0:
                print(f"⚠️  No supported files found to check ({results['ignored']} files ignored)")
                self.print_ignored_files_report(ignored_files, directory)
            else:
                print("⚠️  No supported files found in the specified directory!")
            return results
        
        print(f"📄 Found {results['total']} files to scan")
        print(f"   C++ files: {results['cpp_files']}")
        print(f"   Python files: {results['py_files']}")
        print(f"   Shell files: {results['shell_files']}")
        if results['ignored'] > 0:
            print(f"🚫 Ignored {results['ignored']} files based on patterns")
        print()
        
        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{results['total']}] Processing: {file_path.relative_to(directory)}")
            
            has_header, message, details = self.check_file_header(file_path, verbose)
            
            # Store details for summary
            file_info = {
                'path': file_path,
                'has_header': has_header,
                'message': message,
                'details': details
            }
            results['file_details'].append(file_info)
            
            if has_header:
                results['valid'] += 1
                self.print_file_report(file_path, directory, has_header, message, details, verbose)
            else:
                if details['multiple_headers']:
                    results['multiple_headers'] += 1
                    results['multiple_header_files'].append(file_path)
                
                results['missing'] += 1
                results['missing_files'].append(file_path)
                self.print_file_report(file_path, directory, has_header, message, details, True)
                
                if fix:
                    print(f"🔧 Attempting to fix header...")
                    success, fix_message = self.add_or_replace_header_in_file(file_path)
                    if success:
                        results['fixed'] += 1
                        if "Replaced" in fix_message:
                            results['replaced'] += 1
                        print(f"   ✅ {fix_message}")
                    else:
                        results['errors'] += 1
                        results['error_files'].append(file_path)
                        print(f"   ❌ {fix_message}")
        
        # Show ignored files if any
        if ignored_files and (verbose or len(ignored_files) <= 20):
            self.print_ignored_files_report(ignored_files, directory)
        elif ignored_files:
            print(f"\n🚫 {len(ignored_files)} files ignored (use --verbose to see details)")
        
        return results
    
    def print_summary_report(self, results: Dict, base_path: Path):
        """Print comprehensive summary report"""
        print("\n" + "=" * 80)
        print("📊 ECLIPSE HEADER COMPLIANCE REPORT")
        print("=" * 80)
        
        print(f"📁 Scanned Directory: {base_path.absolute()}")
        print(f"📄 Total Files Found: {results['total'] + results['ignored']}")
        print(f"📋 Files Checked: {results['total']}")
        print(f"   C++ files: {results['cpp_files']}")
        print(f"   Python files: {results['py_files']}")
        print(f"   Shell files: {results['shell_files']}")
        if results['ignored'] > 0:
            print(f"🚫 Files Ignored: {results['ignored']}")
        print(f"✅ Valid Headers: {results['valid']}")
        print(f"❌ Missing Headers: {results['missing']}")
        if results['multiple_headers'] > 0:
            print(f"⚠️  Multiple Headers: {results['multiple_headers']}")
        
        if results['fixed'] > 0:
            print(f"🔧 Headers Fixed: {results['fixed']}")
            if results['replaced'] > 0:
                print(f"🔄 Headers Replaced: {results['replaced']}")
        if results['errors'] > 0:
            print(f"⚠️  Errors: {results['errors']}")
        
        # Compliance percentage
        if results['total'] > 0:
            compliance_rate = (results['valid'] / results['total']) * 100
            print(f"📈 Compliance Rate: {compliance_rate:.1f}%")
        
        # List files missing headers
        if results['missing_files']:
            print(f"\n❌ Files Missing Eclipse Headers ({len(results['missing_files'])}):")
            for file_path in results['missing_files']:
                print(f"   • {file_path.relative_to(base_path)}")
        
        # List files with multiple headers
        if results['multiple_header_files']:
            print(f"\n⚠️  Files With Multiple Headers ({len(results['multiple_header_files'])}):")
            for file_path in results['multiple_header_files']:
                print(f"   • {file_path.relative_to(base_path)}")
        
        # List files that couldn't be fixed
        if results['error_files']:
            print(f"\n⚠️  Files With Errors ({len(results['error_files'])}):")
            for file_path in results['error_files']:
                print(f"   • {file_path.relative_to(base_path)}")
        
        print("\n" + "=" * 80)

def main():
    parser = argparse.ArgumentParser(
        description='Check and fix Eclipse copyright headers in C++, Python, and Shell files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported file types:
  C/C++: .cpp, .hpp, .h, .cc, .cxx, .hxx, .c
  Python: .py  
  Shell: .sh, .bash

Examples:
  %(prog)s                              # Check current directory
  %(prog)s src/                         # Check src directory  
  %(prog)s . --fix                      # Fix missing/incorrect headers
  %(prog)s . --verbose                  # Detailed output for all files
  %(prog)s . --no-recursive             # Only check current level
  %(prog)s . --ignore .headerignore     # Use ignore file
  
Ignore file format (.headerignore):
  # Comments start with #
  build/                    # Ignore build directory
  *.pb.h                   # Ignore protobuf headers
  third_party/**           # Ignore all in third_party
  /external/lib.cpp        # Ignore specific file from root
  __pycache__/             # Ignore Python cache
  *.pyc                    # Ignore compiled Python
  
--fix behavior:
  - Adds headers to files without any headers
  - Replaces old/incorrect headers with correct Eclipse header
  - Fixes files with multiple headers by replacing them with single header
  - Preserves shebang lines in shell scripts
  - Uses appropriate comment style for each file type
        """
    )
    
    parser.add_argument('directory', nargs='?', default='.', 
                       help='Directory to scan (default: current directory)')
    parser.add_argument('--fix', action='store_true', 
                       help='Add missing headers or replace incorrect/multiple headers')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Don\'t scan subdirectories')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed analysis for all files')
    parser.add_argument('--ignore', type=Path, metavar='FILE',
                       help='File containing paths/patterns to ignore')
    
    args = parser.parse_args()
    
    directory = Path(args.directory).resolve()
    if not directory.exists():
        print(f"❌ Error: Directory '{directory}' does not exist")
        sys.exit(1)
    
    if not directory.is_dir():
        print(f"❌ Error: '{directory}' is not a directory")
        sys.exit(1)
    
    # Check ignore file
    ignore_file = args.ignore
    if ignore_file and not ignore_file.exists():
        print(f"❌ Error: Ignore file '{ignore_file}' does not exist")
        sys.exit(1)
    
    checker = EclipseHeaderChecker(ignore_file=ignore_file)
    
    print("🔍 Eclipse Foundation Copyright Header Checker")
    print("=" * 50)
    print(f"📅 Current Year: {checker.current_year}")
    print(f"📄 Supported Types: C++, Python, Shell scripts")
    print(f"🔧 Fix Mode: {'Enabled' if args.fix else 'Disabled'}")
    if args.fix:
        print("   🔄 Will replace old/incorrect headers")
        print("   🧹 Will fix multiple headers")
        print("   📝 Will preserve shebang lines")
    print(f"📂 Recursive: {'No' if args.no_recursive else 'Yes'}")
    print(f"📝 Verbose: {'Yes' if args.verbose else 'No'}")
    if ignore_file:
        print(f"🚫 Ignore File: {ignore_file}")
    print()
    
    try:
        results = checker.scan_directory(
            directory,
            fix=args.fix,
            verbose=args.verbose
        )
        
        # Print summary report
        checker.print_summary_report(results, directory)
        
        # Exit codes
        if results['total'] == 0:
            if results['ignored'] > 0:
                print("ℹ️  All files were ignored")
                sys.exit(0)
            else:
                print("⚠️  No files found to check")
                sys.exit(2)
        elif results['missing'] > 0 and not args.fix:
            print(f"\n💡 Run with --fix to automatically add/replace missing or incorrect headers")
            sys.exit(1)
        elif results['missing'] > 0 and results['errors'] > 0:
            print(f"\n⚠️  Some headers could not be fixed automatically")
            sys.exit(1)
        else:
            print(f"\n🎉 All files have proper Eclipse copyright headers!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Scan interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
