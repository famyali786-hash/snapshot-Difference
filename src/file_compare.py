"""
Compare individual files between two locations.
Used by the SnapDiff Streamlit app to check the status of a single file.
"""

import os
from src.snapshot import get_file_hash


# Check whether a file was added, removed, modified, or unchanged
def file_status(old_file, new_file):
    """
    Compare two file paths and return a string describing what happened to the file.

    Possible return values:
      - "BOTH FILES MISSING"  — neither path exists
      - "REMOVED"             — the old file exists but the new one does not
      - "ADDED"               — the new file exists but the old one does not
      - "MODIFIED"            — both files exist but their contents are different
      - "NO CHANGE"           — both files exist and their contents are identical
    """

    # Check whether each file path actually exists on disk
    old_file_exists = os.path.exists(old_file)
    new_file_exists = os.path.exists(new_file)

    # If neither file exists, we cannot compare anything
    if not old_file_exists and not new_file_exists:
        return "BOTH FILES MISSING"

    # If only the old file exists, the file was removed in the new version
    if old_file_exists and not new_file_exists:
        return "REMOVED"

    # If only the new file exists, the file was added in the new version
    if not old_file_exists and new_file_exists:
        return "ADDED"

    # Both files exist — compare their contents using MD5 hashes
    old_hash = get_file_hash(old_file)
    new_hash = get_file_hash(new_file)

    # If the hashes differ, the file content has changed
    if old_hash != new_hash:
        return "MODIFIED"

    # Hashes are the same, so the file has not changed
    return "NO CHANGE"
