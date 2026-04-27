"""Snapshot generation with MD5 hashing."""
import os
import json
import hashlib
from datetime import datetime


def get_file_hash(path):
    """Return MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()


def take_snapshot(folder_path, output_file):
    """Walk directory recursively, hash all files, save as JSON."""
    files = {}

    for root, dirs, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, folder_path)

            try:
                stat = os.stat(file_path)
                files[rel_path] = {
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "hash": get_file_hash(file_path)
                }
            except (OSError, PermissionError):
                continue

    snapshot = {"files": files}
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(snapshot, f, indent=2)

    return files