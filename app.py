"""Streamlit web UI for File System Snapshot Difference tool."""
import os
import io
import hashlib
import zipfile
import json
from datetime import datetime

import streamlit as st

from src.diff import diff_snapshots, line_diff

st.set_page_config(page_title="File System Snapshot", page_icon="📁", layout="wide")

SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

MAX_FILE_SIZE_MB = 50  # per-file upload limit for hashing


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def is_text(data: bytes) -> bool:
    """Heuristic: if no null bytes in first 8 KB → treat as text."""
    return b"\x00" not in data[:8192]


@st.cache_data(show_spinner=False)
def list_snapshots():
    snaps = []
    if not os.path.exists(SNAPSHOT_DIR):
        return snaps
    for f in os.listdir(SNAPSHOT_DIR):
        if f.endswith(".json"):
            path = os.path.join(SNAPSHOT_DIR, f)
            try:
                stat = os.stat(path)
                with open(path) as fp:
                    data = json.load(fp)
                snaps.append({
                    "name": f,
                    "date": datetime.fromtimestamp(stat.st_mtime),
                    "total_files": len(data.get("files", {}))
                })
            except (OSError, json.JSONDecodeError):
                continue
    return sorted(snaps, key=lambda x: x["date"], reverse=True)


def build_snapshot_from_uploads(uploaded_files) -> dict:
    """Build snapshot dict from a list of UploadedFile objects."""
    files_data = {}
    skipped = []
    for uf in uploaded_files:
        raw = uf.read()
        size_mb = len(raw) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            skipped.append(uf.name)
            continue
        files_data[uf.name] = {
            "size": len(raw),
            "hash": get_hash(raw),
            "text": raw.decode("utf-8", errors="replace") if is_text(raw) else None
        }
    return files_data, skipped


def build_snapshot_from_zip(zip_bytes: bytes) -> tuple[dict, list]:
    """Extract ZIP and build snapshot dict."""
    files_data = {}
    skipped = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            size_mb = info.file_size / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                skipped.append(info.filename)
                continue
            raw = zf.read(info.filename)
            files_data[info.filename] = {
                "size": len(raw),
                "hash": get_hash(raw),
                "text": raw.decode("utf-8", errors="replace") if is_text(raw) else None
            }
    return files_data, skipped


# ── Theme ─────────────────────────────────────────────────────────────────────

if "theme" not in st.session_state:
    st.session_state.theme = True

with st.sidebar:
    st.title("⚙️ Settings")
    theme = st.toggle("Dark Mode", value=st.session_state.theme)
    st.session_state.theme = theme
    st.divider()
    st.write("**Navigate**")
    section = st.radio(
        "nav",
        ["📸 Take Snapshot", "🗂️ Snapshot History", "🔍 Compare Snapshots", "📄 Compare Files"],
        label_visibility="collapsed"
    )

dark          = theme
bg            = "#0d1117" if dark else "#ffffff"
fg            = "#c9d1d9" if dark else "#24292f"
sidebar_bg    = "#161b22" if dark else "#f0f2f6"
card_bg       = "#161b22" if dark else "#f6f8fa"
border        = "#30363d" if dark else "#d0d7de"
c_added       = "#3fb950" if dark else "#22863a"
c_modified    = "#d29922" if dark else "#b08800"
c_removed     = "#f85149" if dark else "#cb2431"
c_equal       = "#8b949e" if dark else "#57606a"
diff_add_bg   = "#0d4429" if dark else "#e6ffec"
diff_rem_bg   = "#4d1818" if dark else "#ffebe9"
diff_eq_bg    = "transparent"

st.markdown(f"""
<style>
.stApp {{ background-color: {bg}; color: {fg}; }}
[data-testid="stSidebar"] {{ background-color: {sidebar_bg}; }}
.stButton > button {{ background-color: #238636; color: white; border: none; border-radius: 6px; }}
.diff-table {{ width:100%; border-collapse:collapse; font-family:monospace; font-size:0.82rem; }}
.diff-table td {{ padding: 2px 8px; white-space: pre-wrap; word-break: break-all; }}
.diff-add  {{ background:{diff_add_bg}; color:{c_added}; }}
.diff-rem  {{ background:{diff_rem_bg}; color:{c_removed}; }}
.diff-eq   {{ background:{diff_eq_bg};  color:{c_equal}; }}
.lineno    {{ color:#8b949e; text-align:right; user-select:none; min-width:36px; }}
.badge-add  {{ color:{c_added};    font-weight:bold; }}
.badge-mod  {{ color:{c_modified}; font-weight:bold; }}
.badge-rem  {{ color:{c_removed};  font-weight:bold; }}
</style>
""", unsafe_allow_html=True)

st.title("📁 File System Snapshot Tool")


# ══════════════════════════════════════════════════════════════════════════════
# 1 — TAKE SNAPSHOT
# ══════════════════════════════════════════════════════════════════════════════
if section == "📸 Take Snapshot":
    st.header("📸 Take Snapshot")

    mode = st.radio("Upload mode", ["📄 Individual Files", "🗜️ ZIP Folder"], horizontal=True)
    st.divider()

    files_data = {}
    skipped    = []

    if mode == "📄 Individual Files":
        st.info("Select multiple files using **Ctrl+A** or **Shift+Click** in the file dialog.")
        uploaded = st.file_uploader(
            "Upload files", accept_multiple_files=True,
            help=f"Max {MAX_FILE_SIZE_MB} MB per file"
        )
        if uploaded:
            files_data, skipped = build_snapshot_from_uploads(uploaded)
            st.caption(f"✅ {len(files_data)} file(s) ready  |  ⚠️ {len(skipped)} skipped (too large)")

    else:  # ZIP mode
        st.info("Zip your entire folder → upload the ZIP here.")
        zip_upload = st.file_uploader("Upload ZIP file", type=["zip"])
        if zip_upload:
            with st.spinner("Extracting ZIP…"):
                files_data, skipped = build_snapshot_from_zip(zip_upload.read())
            st.caption(f"✅ {len(files_data)} file(s) extracted  |  ⚠️ {len(skipped)} skipped (too large)")
            if skipped:
                with st.expander("Skipped files"):
                    st.write(skipped)

    st.divider()
    snapshot_name = st.text_input("Snapshot Name", placeholder="e.g. project_v1")

    col1, col2 = st.columns([1, 1])
    with col1:
        save_btn = st.button("💾 Save Snapshot", type="primary", disabled=not files_data)
    with col2:
        # Also allow importing a previously downloaded snapshot JSON
        import_file = st.file_uploader("📥 Import snapshot JSON", type=["json"], key="import_snap")

    if save_btn:
        if not snapshot_name.strip():
            st.error("Please enter a snapshot name.")
        else:
            snapshot = {"files": files_data}
            out_path = os.path.join(SNAPSHOT_DIR, snapshot_name.strip() + ".json")
            with open(out_path, "w") as fp:
                json.dump(snapshot, fp, indent=2)
            list_snapshots.clear()
            st.success(f"✅ Snapshot **{snapshot_name}** saved with {len(files_data)} file(s)!")

    if import_file:
        try:
            imported = json.load(import_file)
            imp_name = import_file.name
            out_path = os.path.join(SNAPSHOT_DIR, imp_name)
            with open(out_path, "w") as fp:
                json.dump(imported, fp, indent=2)
            list_snapshots.clear()
            st.success(f"✅ Snapshot **{imp_name}** imported successfully!")
        except Exception as e:
            st.error(f"Import failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# 2 — SNAPSHOT HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif section == "🗂️ Snapshot History":
    st.header("🗂️ Snapshot History")
    snaps = list_snapshots()
    if not snaps:
        st.info("📭 No snapshots yet. Create one first!")
    else:
        hdr = st.columns([4, 2, 1, 1, 1])
        for col, label in zip(hdr, ["Name", "Date", "Files", "Download", "Delete"]):
            col.write(f"**{label}**")
        st.divider()

        for snap in snaps:
            row = st.columns([4, 2, 1, 1, 1])
            row[0].write(f"📄 {snap['name']}")
            row[1].write(snap["date"].strftime("%Y-%m-%d %H:%M"))
            row[2].write(str(snap["total_files"]))

            # Download button
            snap_path = os.path.join(SNAPSHOT_DIR, snap["name"])
            with open(snap_path, "rb") as fp:
                snap_bytes = fp.read()
            row[3].download_button(
                "⬇️", data=snap_bytes,
                file_name=snap["name"],
                mime="application/json",
                key=f"dl_{snap['name']}"
            )

            # Delete button
            if row[4].button("🗑️", key=f"del_{snap['name']}"):
                os.remove(snap_path)
                list_snapshots.clear()
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# 3 — COMPARE SNAPSHOTS
# ══════════════════════════════════════════════════════════════════════════════
elif section == "🔍 Compare Snapshots":
    st.header("🔍 Compare Snapshots")
    snaps = list_snapshots()

    if len(snaps) < 2:
        st.warning("⚠️ Need at least 2 snapshots to compare.")
    else:
        snap_names = [s["name"] for s in snaps]
        col1, col2 = st.columns(2)
        with col1:
            snap_a = st.selectbox("Snapshot A — Older", snap_names, index=len(snap_names) - 1)
        with col2:
            snap_b = st.selectbox("Snapshot B — Newer", snap_names, index=0)

        if st.button("🔍 Compare", type="primary"):
            if snap_a == snap_b:
                st.warning("Please select two different snapshots.")
            else:
                with open(os.path.join(SNAPSHOT_DIR, snap_a)) as fa:
                    old = json.load(fa)
                with open(os.path.join(SNAPSHOT_DIR, snap_b)) as fb:
                    new = json.load(fb)

                r_added, r_removed, r_modified = diff_snapshots(old, new)
                total = len(r_added) + len(r_removed) + len(r_modified)

                if total == 0:
                    st.success("✨ Snapshots are identical — no differences found!")
                else:
                    st.markdown(
                        f"**{total} change(s):** "
                        f"<span class='badge-add'>+{len(r_added)} added</span> &nbsp;"
                        f"<span class='badge-mod'>~{len(r_modified)} modified</span> &nbsp;"
                        f"<span class='badge-rem'>-{len(r_removed)} removed</span>",
                        unsafe_allow_html=True
                    )
                    st.divider()

                    # ── Added ──
                    if r_added:
                        st.markdown(f"### ✅ Added ({len(r_added)})")
                        for f in sorted(r_added):
                            st.markdown(f"<span class='badge-add'>+ {f}</span>", unsafe_allow_html=True)

                    # ── Removed ──
                    if r_removed:
                        st.markdown(f"### ❌ Removed ({len(r_removed)})")
                        for f in sorted(r_removed):
                            st.markdown(f"<span class='badge-rem'>- {f}</span>", unsafe_allow_html=True)

                    # ── Modified with line diff ──
                    if r_modified:
                        st.markdown(f"### 🔄 Modified ({len(r_modified)})")
                        for fname in sorted(r_modified):
                            old_entry = old["files"].get(fname, {})
                            new_entry = new["files"].get(fname, {})
                            old_text  = old_entry.get("text")
                            new_text  = new_entry.get("text")

                            with st.expander(f"📄 {fname}"):
                                if old_text is not None and new_text is not None:
                                    diff_lines = line_diff(old_text, new_text)
                                    added_c   = sum(1 for d in diff_lines if d["type"] == "added")
                                    removed_c = sum(1 for d in diff_lines if d["type"] == "removed")
                                    st.caption(f"+{added_c} lines added  |  -{removed_c} lines removed")

                                    rows_html = ""
                                    for d in diff_lines:
                                        css   = "diff-add" if d["type"] == "added" else \
                                                "diff-rem" if d["type"] == "removed" else "diff-eq"
                                        sign  = "+" if d["type"] == "added" else \
                                                "-" if d["type"] == "removed" else " "
                                        old_n = str(d["old_no"]) if d["old_no"] else ""
                                        new_n = str(d["new_no"]) if d["new_no"] else ""
                                        line  = d["line"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                                        rows_html += (
                                            f"<tr class='{css}'>"
                                            f"<td class='lineno'>{old_n}</td>"
                                            f"<td class='lineno'>{new_n}</td>"
                                            f"<td>{sign} {line}</td>"
                                            f"</tr>"
                                        )
                                    st.markdown(
                                        f"<table class='diff-table'>{rows_html}</table>",
                                        unsafe_allow_html=True
                                    )
                                else:
                                    old_size = old_entry.get("size", 0)
                                    new_size = new_entry.get("size", 0)
                                    diff_b   = new_size - old_size
                                    sign     = "+" if diff_b >= 0 else ""
                                    st.info(f"Binary file — size changed: {sign}{diff_b:,} bytes")


# ══════════════════════════════════════════════════════════════════════════════
# 4 — COMPARE FILES
# ══════════════════════════════════════════════════════════════════════════════
elif section == "📄 Compare Files":
    st.header("📄 Compare Files")
    st.info("Upload the same file from two different points in time.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Old File**")
        old_up = st.file_uploader("Upload old file", key="old_file")
    with col2:
        st.markdown("**New File**")
        new_up = st.file_uploader("Upload new file", key="new_file")

    if st.button("🔍 Compare Files", type="primary"):
        if not old_up or not new_up:
            st.error("Please upload both files.")
        else:
            old_bytes = old_up.read()
            new_bytes = new_up.read()
            old_hash  = get_hash(old_bytes)
            new_hash  = get_hash(new_bytes)
            old_size  = len(old_bytes)
            new_size  = len(new_bytes)
            status    = "NO CHANGE" if old_hash == new_hash else "MODIFIED"

            # Status badge
            if status == "NO CHANGE":
                st.success("✨ NO CHANGE — Files are identical!")
            else:
                st.warning("🔄 MODIFIED — Files are different!")

            # Details row
            st.divider()
            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f"**Old:** `{old_up.name}`")
                st.caption(f"Size : {old_size:,} bytes")
                st.caption(f"MD5  : `{old_hash}`")
            with d2:
                st.markdown(f"**New:** `{new_up.name}`")
                st.caption(f"Size : {new_size:,} bytes")
                st.caption(f"MD5  : `{new_hash}`")

            if status == "MODIFIED":
                diff_b = new_size - old_size
                sign   = "+" if diff_b >= 0 else ""
                st.caption(f"Size difference: **{sign}{diff_b:,} bytes**")

                # Line-by-line diff for text files
                if is_text(old_bytes) and is_text(new_bytes):
                    st.divider()
                    st.markdown("### 📝 Line-by-Line Diff")
                    old_text   = old_bytes.decode("utf-8", errors="replace")
                    new_text   = new_bytes.decode("utf-8", errors="replace")
                    diff_lines = line_diff(old_text, new_text)
                    added_c    = sum(1 for d in diff_lines if d["type"] == "added")
                    removed_c  = sum(1 for d in diff_lines if d["type"] == "removed")
                    st.caption(f"+{added_c} lines added  |  -{removed_c} lines removed")

                    rows_html = ""
                    for d in diff_lines:
                        css  = "diff-add" if d["type"] == "added" else \
                               "diff-rem" if d["type"] == "removed" else "diff-eq"
                        sign = "+" if d["type"] == "added" else \
                               "-" if d["type"] == "removed" else " "
                        old_n = str(d["old_no"]) if d["old_no"] else ""
                        new_n = str(d["new_no"]) if d["new_no"] else ""
                        line  = d["line"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        rows_html += (
                            f"<tr class='{css}'>"
                            f"<td class='lineno'>{old_n}</td>"
                            f"<td class='lineno'>{new_n}</td>"
                            f"<td>{sign} {line}</td>"
                            f"</tr>"
                        )
                    st.markdown(
                        f"<table class='diff-table'>{rows_html}</table>",
                        unsafe_allow_html=True
                    )
                else:
                    st.info("Binary file — line diff not available.")
