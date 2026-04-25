# File System Snapshot Difference Tool

A Python tool for creating snapshots of file systems and comparing differences over time.

## Features

- **Snapshot Generation**: Recursively hash all files in a directory using MD5
- **Snapshot Comparison**: Find added, removed, and modified files between two snapshots
- **File Comparison**: Compare two individual files and report their status
- **CLI Interface**: Text-based menu for command-line usage
- **Web UI**: Streamlit-based web interface with dark/light mode

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### CLI Interface
```bash
python src/main.py
```

### Web UI
```bash
streamlit run app.py
```

## Project Structure

```
File-System-Snapshot-Difference/
├── src/
│   ├── snapshot.py      # Snapshot generation with MD5 hashing
│   ├── diff.py          # Compare two snapshots
│   ├── file_compare.py  # Compare individual files
│   └── main.py          # CLI text-based menu
├── snapshots/           # Folder to store JSON snapshots
├── folder/             # Sample test folder
├── app.py              # Streamlit web UI entry point
├── requirements.txt    # Dependencies: streamlit
├── README.md           # Documentation
└── LICENSE             # MIT License
```

## JSON Snapshot Format

```json
{
  "files": {
    "relative/path/file.txt": {
      "size": 123,
      "mtime": 1234567890.123,
      "hash": "md5hashstring"
    }
  }
}
```

## License

MIT