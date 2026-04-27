"""Compare two snapshots and provide line-by-line diff for text files."""
import difflib


def diff_snapshots(old_snap, new_snap):
    """Return (added, removed, modified) lists."""
    old_files = set(old_snap.get("files", {}).keys())
    new_files = set(new_snap.get("files", {}).keys())

    added    = list(new_files - old_files)
    removed  = list(old_files - new_files)
    modified = []

    for f in old_files & new_files:
        if old_snap["files"][f]["hash"] != new_snap["files"][f]["hash"]:
            modified.append(f)

    return added, removed, modified


def line_diff(old_text: str, new_text: str) -> list[dict]:
    """
    Return a list of line-diff entries.
    Each entry: {"type": "added"|"removed"|"equal", "line": str, "old_no": int|None, "new_no": int|None}
    """
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    result  = []

    old_no = 1
    new_no = 1

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for line in old_lines[i1:i2]:
                result.append({"type": "equal", "line": line.rstrip("\n"), "old_no": old_no, "new_no": new_no})
                old_no += 1
                new_no += 1
        elif tag == "replace":
            for line in old_lines[i1:i2]:
                result.append({"type": "removed", "line": line.rstrip("\n"), "old_no": old_no, "new_no": None})
                old_no += 1
            for line in new_lines[j1:j2]:
                result.append({"type": "added", "line": line.rstrip("\n"), "old_no": None, "new_no": new_no})
                new_no += 1
        elif tag == "delete":
            for line in old_lines[i1:i2]:
                result.append({"type": "removed", "line": line.rstrip("\n"), "old_no": old_no, "new_no": None})
                old_no += 1
        elif tag == "insert":
            for line in new_lines[j1:j2]:
                result.append({"type": "added", "line": line.rstrip("\n"), "old_no": None, "new_no": new_no})
                new_no += 1

    return result
