"""
Compare two snapshots and provide a line-by-line diff for text files.
This module is used by the SnapDiff Streamlit app.
"""

from __future__ import annotations
import difflib


# Compare two snapshot dictionaries and find what changed between them
def diff_snapshots(old_snap, new_snap):
    """
    Compare two snapshot dictionaries.
    Returns three lists: added files, removed files, and modified files.
    """

    # Get the set of file paths from each snapshot
    old_files = set(old_snap.get("files", {}).keys())
    new_files = set(new_snap.get("files", {}).keys())

    # Files that exist in the new snapshot but not in the old one are "added"
    added = list(new_files - old_files)

    # Files that exist in the old snapshot but not in the new one are "removed"
    removed = list(old_files - new_files)

    # Files that exist in both snapshots need a hash comparison
    modified = []

    # Loop through files that appear in both snapshots
    for file_path in old_files & new_files:
        old_hash = old_snap["files"][file_path].get("hash")
        new_hash = new_snap["files"][file_path].get("hash")

        # Skip if either hash is missing (malformed snapshot)
        if old_hash is None or new_hash is None:
            continue

        # If the hashes are different, the file content has changed
        if old_hash != new_hash:
            modified.append(file_path)

    return added, removed, modified


# Compare two text strings line by line and return a structured diff
def line_diff(old_text: str, new_text: str) -> list[dict]:
    """
    Compare two text strings line by line.

    Returns a list of dictionaries. Each dictionary represents one line and has:
      - "type": either "equal", "added", or "removed"
      - "line": the text content of the line (without the newline character)
      - "old_no": the line number in the old file (or None if the line was added)
      - "new_no": the line number in the new file (or None if the line was removed)
    """

    # Split both texts into individual lines, keeping the line endings
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    # Use Python's built-in SequenceMatcher to find differences between the two line lists
    # autojunk=False means we don't skip any lines, even repeated ones
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)

    # This list will hold all the diff entries we build below
    result = []

    # Track the current line numbers for the old and new files separately
    old_line_number = 1
    new_line_number = 1

    # Loop through each "opcode" — a block of lines that are equal, replaced, deleted, or inserted
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        # Lines that are the same in both files
        if tag == "equal":
            for line in old_lines[i1:i2]:
                # Strip the trailing newline for display purposes
                clean_line = line.rstrip("\n")

                result.append({
                    "type": "equal",
                    "line": clean_line,
                    "old_no": old_line_number,
                    "new_no": new_line_number
                })

                # Both line counters advance because this line exists in both files
                old_line_number += 1
                new_line_number += 1

        # Lines that were replaced — show the old lines as removed, then the new lines as added
        elif tag == "replace":
            # First, show all the old lines as removed
            for line in old_lines[i1:i2]:
                clean_line = line.rstrip("\n")

                result.append({
                    "type": "removed",
                    "line": clean_line,
                    "old_no": old_line_number,
                    "new_no": None  # No matching line in the new file
                })

                old_line_number += 1

            # Then, show all the new lines as added
            for line in new_lines[j1:j2]:
                clean_line = line.rstrip("\n")

                result.append({
                    "type": "added",
                    "line": clean_line,
                    "old_no": None,  # No matching line in the old file
                    "new_no": new_line_number
                })

                new_line_number += 1

        # Lines that were deleted from the old file (not present in the new file)
        elif tag == "delete":
            for line in old_lines[i1:i2]:
                clean_line = line.rstrip("\n")

                result.append({
                    "type": "removed",
                    "line": clean_line,
                    "old_no": old_line_number,
                    "new_no": None  # This line does not exist in the new file
                })

                old_line_number += 1

        # Lines that were inserted into the new file (not present in the old file)
        elif tag == "insert":
            for line in new_lines[j1:j2]:
                clean_line = line.rstrip("\n")

                result.append({
                    "type": "added",
                    "line": clean_line,
                    "old_no": None,  # This line did not exist in the old file
                    "new_no": new_line_number
                })

                new_line_number += 1

    return result
