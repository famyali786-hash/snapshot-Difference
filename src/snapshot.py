"""
Snapshot generation with MD5 hashing.
This module walks a folder, hashes every file, and saves the result as a JSON file.
Used by the SnapDiff Streamlit app.
"""

import os
import json
import hashlib


# Calculate the MD5 hash of a single file
def get_file_hash(file_path):
    """
    Read a file in binary mode and compute its MD5 hash.
    The file is read in small chunks so large files don't use too much memory.
    Returns the hash as a hex string (e.g. "d41d8cd98f00b204e9800998ecf8427e").
    """

    # Create a new MD5 hash object
    md5_hasher = hashlib.md5()

    # Open the file in binary mode so we can read any file type
    with open(file_path, 'rb') as file_handle:
        # Read the file in 8192-byte chunks until there is nothing left
        while True:
            chunk = file_handle.read(8192)

            # An empty chunk means we have reached the end of the file
            if chunk == b'':
                break

            # Feed this chunk into the hash calculation
            md5_hasher.update(chunk)

    # Return the final hash as a readable hex string
    return md5_hasher.hexdigest()


# Walk a folder, collect info about every file, and save it as a JSON snapshot
def take_snapshot(folder_path, output_file):
    """
    Scan every file inside folder_path recursively.
    For each file, record its size, last-modified time, and MD5 hash.
    Save all of this information to output_file as a JSON file.
    Returns the dictionary of file information.
    """

    # This dictionary will hold info for every file we find
    files = {}

    # Walk through the folder and all its subfolders
    for root_folder, subfolders, filenames in os.walk(folder_path):
        for filename in filenames:

            # Build the full path to this file
            full_path = os.path.join(root_folder, filename)

            # Build a relative path so the snapshot is not tied to one machine
            relative_path = os.path.relpath(full_path, folder_path)

            try:
                # Get file metadata (size and modification time)
                file_stat = os.stat(full_path)

                # Store the file info using the relative path as the key
                files[relative_path] = {
                    "size": file_stat.st_size,       # File size in bytes
                    "mtime": file_stat.st_mtime,     # Last modified time (Unix timestamp)
                    "hash": get_file_hash(full_path) # MD5 hash of the file contents
                }

            except (OSError, PermissionError):
                # Skip files we cannot read (e.g. permission denied or file disappeared)
                continue

    # Wrap the files dictionary in a top-level "files" key
    snapshot = {"files": files}

    # Make sure the output directory exists before writing the file
    output_directory = os.path.dirname(output_file)
    if output_directory:
        os.makedirs(output_directory, exist_ok=True)

    # Write the snapshot data to the output file as formatted JSON
    with open(output_file, 'w') as json_file:
        json.dump(snapshot, json_file, indent=2)

    # Return the files dictionary so the caller can use it right away
    return files
