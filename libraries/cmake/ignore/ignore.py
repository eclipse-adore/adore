import fnmatch
import os
import sys
import logging

log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ignore.log')
logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def is_path_ignored(path, ignore_patterns):
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(path, pattern):
            logging.info(f"path: {path} pattern: {pattern} match: fnmatch")
            return True
        elif pattern in path:
            logging.info(f"path: {path} pattern: {pattern} match: substring")
            return True

    logging.info(f"path: {path} match: false")
    return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python ignore.py <path> <ignorefile>")
        sys.exit(1)

    path = sys.argv[1]
    ignorefile = sys.argv[2]

    if not os.path.exists(ignorefile):
        print(f"Ignore file '{ignorefile}' not found.")
        sys.exit(1)

    with open(ignorefile, 'r') as f:
        ignore_patterns = [
            line.strip() for line in f.readlines() 
            if line.strip() and not line.lstrip().startswith('#')
        ]

    logging.info(f"Checking path: {path} against {len(ignore_patterns)} patterns")
    
    if is_path_ignored(path, ignore_patterns):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
