import fnmatch
import os
import sys

import logging
import os

log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ignore.log')
logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def is_path_ignored(path, ignore_patterns):
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(path, pattern):
            logging.info("path: " + path + " pattern: " + pattern + " match: true")
            return True
        elif pattern in path:
            logging.info("path: " + path + " pattern: " + pattern + " match: true")
            return True

    logging.info("path: " + path + " match: false")
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
        ignore_patterns = [line.strip() for line in f.readlines() if not line.lstrip().startswith('#')]
        if ignore_patterns == None:
            ignore_patterns = []
        ignore_patterns = list(filter(None, ignore_patterns))

    if is_path_ignored(path, ignore_patterns):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

