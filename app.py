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

MAX_FILE_SIZE_MB = 50


def get_hash(data):
    return hashlib.md5(data).hexdigest()


def is_text(data):
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


def build_snapshot_from_uploads(uploaded_files):
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


def build_snapshot_from_zip(zip_bytes):
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

with st.sidebar:
    st.title("Settings")
    st.divider()

    # ── Live Stats ──────────────────────────────
    # Snapshots folder se real data calculate karo
    total_snapshots = 0
    total_files     = 0
    last_snapshot   = "None"

    if os.path.exists(SNAPSHOT_DIR):
        snap_files = [f for f in os.listdir(SNAPSHOT_DIR) if f.endswith(".json")]
        total_snapshots = len(snap_files)

        latest_time = None
        for snap_file in snap_files:
            snap_path = os.path.join(SNAPSHOT_DIR, snap_file)
            try:
                mtime = os.path.getmtime(snap_path)
                with open(snap_path) as fp:
                    data = json.load(fp)
                total_files += len(data.get("files", {}))
                if latest_time is None or mtime > latest_time:
                    latest_time = mtime
            except (OSError, json.JSONDecodeError):
                continue

        if latest_time:
            snap_date = datetime.fromtimestamp(latest_time)
            today     = datetime.now()
            if snap_date.date() == today.date():
                last_snapshot = "Today"
            elif (today.date() - snap_date.date()).days == 1:
                last_snapshot = "Yesterday"
            else:
                last_snapshot = snap_date.strftime("%b %d, %Y")

    st.markdown("**📊 Live Stats**")
    st.markdown(f"""
    <div style="
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.88rem;
        line-height: 2;
    ">
        💾 &nbsp;<b>Snapshots:</b> {total_snapshots}<br>
        📄 &nbsp;<b>Files tracked:</b> {total_files}<br>
        🕐 &nbsp;<b>Last snapshot:</b> {last_snapshot}
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.write("**Select Section**")
    section = st.radio(
        "Navigation",
        ["Take Snapshot", "Snapshot History", "Compare Snapshots", "Compare Files"],
        label_visibility="collapsed"
    )

# Fixed diff colors that work in both light and dark mode
color_added    = "#2ea043"
color_removed  = "#da3633"
color_modified = "#d29922"

st.markdown("""
<style>
.stButton > button {
    background-color: #238636 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
}
.stDownloadButton > button {
    background-color: #238636 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
}
.diff-table {
    width: 100%;
    border-collapse: collapse;
    font-family: monospace;
    font-size: 0.82rem;
}
.diff-table td {
    padding: 2px 8px;
    white-space: pre-wrap;
    word-break: break-all;
}
.diff-add { background: #0d4429; color: #3fb950; }
.diff-rem { background: #4d1818; color: #f85149; }
.diff-eq  { color: #8b949e; }
.lineno   {
    color: #8b949e !important;
    text-align: right;
    user-select: none;
    min-width: 36px;
}
</style>
""", unsafe_allow_html=True)

st.title("📁 File System Snapshot Tool")


# ── TAKE SNAPSHOT ─────────────────────────────────────────────────────────────
if section == "Take Snapshot":
    st.header("Take Snapshot")

    mode = st.radio("Upload mode", ["📄 Individual Files", "🗜️ ZIP Folder"], horizontal=True)
    st.divider()

    files_data = {}
    skipped = []

    if mode == "📄 Individual Files":
        st.info("Select multiple files using **Ctrl+A** or **Shift+Click** in the file dialog.")
        uploaded = st.file_uploader("Upload files", accept_multiple_files=True)
        if uploaded:
            files_data, skipped = build_snapshot_from_uploads(uploaded)
            st.caption(f"✅ {len(files_data)} file(s) ready  |  ⚠️ {len(skipped)} skipped (too large)")

    else:
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
    snapshot_name = st.text_input("Snapshot Name", placeholder="e.g. my_snapshot")

    col1, col2 = st.columns([1, 1])
    with col1:
        save_btn = st.button("💾 Save Snapshot", type="primary", disabled=not files_data)
    with col2:
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
            st.rerun()  # sidebar stats turant update honge

    if import_file:
        try:
            imported = json.load(import_file)
            imp_name = import_file.name
            out_path = os.path.join(SNAPSHOT_DIR, imp_name)
            with open(out_path, "w") as fp:
                json.dump(imported, fp, indent=2)
            list_snapshots.clear()
            st.success(f"✅ Snapshot **{imp_name}** imported successfully!")
            st.rerun()  # sidebar stats turant update honge
        except Exception as e:
            st.error(f"Import failed: {e}")


# ── SNAPSHOT HISTORY ──────────────────────────────────────────────────────────
elif section == "Snapshot History":
    st.header("Snapshot History")
    snaps = list_snapshots()
    if not snaps:
        st.info("📭 No snapshots yet. Create one first!")
    else:
        cols = st.columns([4, 2, 1, 1, 1])
        with cols[0]: st.write("**Name**")
        with cols[1]: st.write("**Date**")
        with cols[2]: st.write("**Files**")
        with cols[3]: st.write("**DL**")
        with cols[4]: st.write("**Del**")
        st.divider()
        for snap in snaps:
            cols = st.columns([4, 2, 1, 1, 1])
            with cols[0]: st.write(f"📄 {snap['name']}")
            with cols[1]: st.write(snap["date"].strftime("%Y-%m-%d %H:%M"))
            with cols[2]: st.write(str(snap["total_files"]))
            snap_path = os.path.join(SNAPSHOT_DIR, snap["name"])
            with open(snap_path, "rb") as fp:
                snap_bytes = fp.read()
            with cols[3]:
                st.download_button(
                    "⬇️", data=snap_bytes,
                    file_name=snap["name"],
                    mime="application/json",
                    key=f"dl_{snap['name']}"
                )
            with cols[4]:
                if st.button("🗑️", key=f"del_{snap['name']}"):
                    os.remove(snap_path)
                    list_snapshots.clear()
                    st.rerun()


# ── COMPARE SNAPSHOTS ─────────────────────────────────────────────────────────
elif section == "Compare Snapshots":
    st.header("Compare Snapshots")
    snaps = list_snapshots()
    if len(snaps) < 2:
        st.warning("⚠️ Need at least 2 snapshots to compare.")
    else:
        snap_names = [s["name"] for s in snaps]
        cols = st.columns(2)
        with cols[0]:
            snap_a = st.selectbox("Snapshot A (older)", snap_names, index=len(snap_names) - 1)
        with cols[1]:
            snap_b = st.selectbox("Snapshot B (newer)", snap_names, index=0)

        if st.button("🔍 Compare", type="primary"):
            if snap_a == snap_b:
                st.warning("Please select two different snapshots.")
            else:
                with open(os.path.join(SNAPSHOT_DIR, snap_a)) as fa:
                    old = json.load(fa)
                with open(os.path.join(SNAPSHOT_DIR, snap_b)) as fb:
                    new = json.load(fb)

                result_added, result_removed, result_modified = diff_snapshots(old, new)
                total = len(result_added) + len(result_removed) + len(result_modified)

                if total == 0:
                    st.success("✨ No differences found — snapshots are identical!")
                else:
                    st.markdown(
                        f"**{total} change(s):** "
                        f"+{len(result_added)} added | "
                        f"~{len(result_modified)} modified | "
                        f"-{len(result_removed)} removed"
                    )
                    st.divider()

                    if result_added:
                        st.markdown(f"### ✅ Added ({len(result_added)})")
                        for f in sorted(result_added):
                            st.markdown(f"<span style='color:{color_added}'>+ {f}</span>", unsafe_allow_html=True)

                    if result_removed:
                        st.markdown(f"### ❌ Removed ({len(result_removed)})")
                        for f in sorted(result_removed):
                            st.markdown(f"<span style='color:{color_removed}'>- {f}</span>", unsafe_allow_html=True)

                    if result_modified:
                        st.markdown(f"### 🔄 Modified ({len(result_modified)})")
                        for fname in sorted(result_modified):
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
                                        css   = "diff-add" if d["type"] == "added" else "diff-rem" if d["type"] == "removed" else "diff-eq"
                                        sign  = "+" if d["type"] == "added" else "-" if d["type"] == "removed" else " "
                                        old_n = str(d["old_no"]) if d["old_no"] else ""
                                        new_n = str(d["new_no"]) if d["new_no"] else ""
                                        line  = d["line"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                                        rows_html += f"<tr class='{css}'><td class='lineno'>{old_n}</td><td class='lineno'>{new_n}</td><td>{sign} {line}</td></tr>"
                                    st.markdown(f"<table class='diff-table'>{rows_html}</table>", unsafe_allow_html=True)
                                else:
                                    old_size = old_entry.get("size", 0)
                                    new_size = new_entry.get("size", 0)
                                    diff_b   = new_size - old_size
                                    sign     = "+" if diff_b >= 0 else ""
                                    st.info(f"Binary file — size changed: {sign}{diff_b:,} bytes")


# ── COMPARE FILES ─────────────────────────────────────────────────────────────
elif section == "Compare Files":
    st.header("Compare Files")
    st.info("Upload the same file from two different points in time.")

    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Old File**")
        old_up = st.file_uploader("Upload old file", key="old_file")
    with cols[1]:
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

            if status == "NO CHANGE":
                st.success("✨ NO CHANGE — Files are identical!")
            else:
                st.warning("🔄 MODIFIED — Files are different!")

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
                        css   = "diff-add" if d["type"] == "added" else "diff-rem" if d["type"] == "removed" else "diff-eq"
                        sign  = "+" if d["type"] == "added" else "-" if d["type"] == "removed" else " "
                        old_n = str(d["old_no"]) if d["old_no"] else ""
                        new_n = str(d["new_no"]) if d["new_no"] else ""
                        line  = d["line"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        rows_html += f"<tr class='{css}'><td class='lineno'>{old_n}</td><td class='lineno'>{new_n}</td><td>{sign} {line}</td></tr>"
                    st.markdown(f"<table class='diff-table'>{rows_html}</table>", unsafe_allow_html=True)
                else:
                    st.info("Binary file — line diff not available.")
