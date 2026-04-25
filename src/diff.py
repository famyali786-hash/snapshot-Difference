"""Compare two snapshots."""


def diff_snapshots(old_snap, new_snap):
    """Return (added, removed, modified) lists."""
    old_files = set(old_snap.get("files", {}).keys())
    new_files = set(new_snap.get("files", {}).keys())

    added = list(new_files - old_files)
    removed = list(old_files - new_files)
    modified = []

    for f in old_files & new_files:
        if old_snap["files"][f]["hash"] != new_snap["files"][f]["hash"]:
            modified.append(f)

    return added, removed, modified