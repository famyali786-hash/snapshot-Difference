"""Compare individual files."""
import os
from src.snapshot import get_file_hash


def file_status(old_file, new_file):
    """Return status: ADDED, REMOVED, MODIFIED, NO CHANGE, BOTH FILES MISSING."""
    old_exists = os.path.exists(old_file)
    new_exists = os.path.exists(new_file)

    if not old_exists and not new_exists:
        return "BOTH FILES MISSING"
    if old_exists and not new_exists:
        return "REMOVED"
    if not old_exists and new_exists:
        return "ADDED"

    old_hash = get_file_hash(old_file)
    new_hash = get_file_hash(new_file)

    return "MODIFIED" if old_hash != new_hash else "NO CHANGE"