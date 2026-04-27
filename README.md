[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-ff4b4b?logo=streamlit)](https://snapshot-difference-kgankzlgova2faayonisbx.streamlit.app)

# 📁 File System Snapshot Difference

A **Python-based developer tool** that captures snapshots of uploaded files and compares them to detect **added, modified, and removed files**. The project includes a **Streamlit web UI** for easy interaction and supports both **individual file uploads** and **ZIP folder uploads**.

This project was developed as part of an On-the-Job Training (OJT) program to understand file system behavior, hashing, and UI integration using Streamlit.

🚀 **Live App:** https://snapshot-difference-kgankzlgova2faayonisbx.streamlit.app

---

## 🚀 Features

### 1. File Snapshot Generation
- Upload individual files or a ZIP folder
- Stores file metadata (**file path + MD5 hash**) in a JSON file
- Helps track file-level changes across snapshot versions
- Download snapshots as JSON for permanent storage
- Import previously saved snapshots

### 2. Snapshot Comparison (Diff Tool)
Compares **Snapshot A** and **Snapshot B** to detect:
- 🟢 **Added Files** – Present in Snapshot B but not in Snapshot A
- 🟡 **Modified Files** – File content changed (detected via MD5 hash)
- 🔴 **Removed Files** – Present in Snapshot A but missing in Snapshot B
- 📝 **Line-by-Line Diff** – For text files, shows exactly which lines changed

### 3. Streamlit Web UI
A clean and simple browser-based interface that allows users to:
- Upload files or ZIP folder → Generate a snapshot
- Select two snapshots → Compare and view differences
- View added, modified, and removed files clearly
- Download and import snapshots for permanent storage

### 4. Snapshot History Table
Displays all snapshots in a structured table with columns:
- Snapshot Name
- Date & Time
- Number of files in the snapshot
- Download button (⬇️)
- Delete button (🗑️)

### 5. Live Stats in Sidebar
The sidebar shows real-time statistics:
- 💾 Total snapshots saved
- 📄 Total files tracked
- 🕐 Last snapshot date

### 6. Compare Files
Directly upload two versions of the same file to:
- Check if files are identical or modified
- View MD5 hash and file size comparison
- See line-by-line diff for text files

---

## 🗂️ Project Structure

```text
FILE-SYSTEM-SNAPSHOT-DIFFERENCE/
│
├── folder/                 # Sample folder for testing
│
├── snapshots/              # Auto-generated snapshot JSON files
│
├── src/
│   ├── diff.py             # Snapshot comparison logic
│   ├── file_compare.py     # File comparison logic
│   ├── main.py             # CLI text-based menu interface
│   └── snapshot.py         # Snapshot generation logic
│
├── app.py                  # Streamlit UI entry point
├── LICENSE
├── README.md
└── requirements.txt
```

---

## 🛠️ Tech Stack

- **Python 3**
- **Streamlit**
- **JSON**
- **Hashlib (MD5)**
- **Zipfile**
- **OS Module**

---

## ▶️ How to Run the Project

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Streamlit App

```bash
streamlit run app.py
```

---

## 🧭 How to Use the Streamlit UI

### Step 1: Take a Snapshot
- Go to **Take Snapshot** section
- Choose upload mode: **Individual Files** or **ZIP Folder**
- Upload your files
- Enter a snapshot name
- Click **💾 Save Snapshot**

### Step 2: Compare Snapshots
- Go to **Compare Snapshots** section
- Select **Snapshot A** (older) and **Snapshot B** (newer)
- Click **🔍 Compare**
- The UI displays:
  - Added files
  - Modified files (with line-by-line diff for text files)
  - Removed files

### Step 3: Compare Files Directly
- Go to **Compare Files** section
- Upload the **Old File** and **New File**
- Click **🔍 Compare Files**
- View status, MD5 hash, size difference, and line diff

### Step 4: Manage Snapshots
- Go to **Snapshot History** section
- Download snapshots as JSON (⬇️) for permanent storage
- Delete snapshots (🗑️) when no longer needed
- Import previously downloaded snapshots

---

## 📌 Example Output

### Snapshot Diff

**Added Files**
- `new_feature.py`

**Modified Files**
- `README.md`
- `app.py`

**Removed Files**
- `old_script.py`

---

## 🎯 Purpose of the Project

This OJT project is designed to help learners understand:
- How file systems store and update data
- How hashing helps detect content changes
- How to build real-world developer tools
- How to integrate backend logic with a Streamlit web UI
- How to design clean, professional, and scalable project architecture

---

## 🌱 Future Improvements (Optional)

- Snapshot versioning and tagging
- Export diff results as PDF/CSV reports
- UI filters and search for large snapshot histories
- Support for ignore rules (e.g. skip `.pyc` files)

---

⭐ If you found this project useful, consider starring the repository!
