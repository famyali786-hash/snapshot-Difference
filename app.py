"""Streamlit web UI for File System Snapshot Difference tool."""
import os
import io
import hashlib
import streamlit as st
import json
from datetime import datetime

from src.diff import diff_snapshots

st.set_page_config(page_title="File System Snapshot", page_icon="📁")

SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_file_hash_bytes(data: bytes) -> str:
    """Return MD5 hash of bytes."""
    return hashlib.md5(data).hexdigest()


def get_file_hash_path(path: str) -> str:
    """Return MD5 hash of a file on disk."""
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


@st.cache_data(show_spinner=False)
def list_snapshots():
    """Return sorted list of snapshot metadata."""
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


# ── Theme ─────────────────────────────────────────────────────────────────────

if "theme" not in st.session_state:
    st.session_state.theme = True

with st.sidebar:
    st.title("Settings")
    theme = st.toggle("Dark Mode", value=st.session_state.theme)
    st.session_state.theme = theme
    st.divider()
    st.write("**Select Section**")
    section = st.radio(
        "Navigation",
        ["Take Snapshot", "Snapshot History", "Compare Snapshots", "Compare Files"],
        label_visibility="collapsed"
    )

dark = theme
bg_color      = "#0d1117" if dark else "#ffffff"
text_color    = "#c9d1d9" if dark else "#24292f"
sidebar_color = "#161b22" if dark else "#f0f2f6"
card_color    = "#161b22" if dark else "#f6f8fa"
border_color  = "#30363d" if dark else "#d0d7de"
btn_color     = "#238636"
color_added    = "#3fb950" if dark else "#22863a"
color_modified = "#d29922" if dark else "#b08800"
color_removed  = "#f85149" if dark else "#cb2431"

st.markdown(f"""
<style>
.stApp {{ background-color: {bg_color}; color: {text_color}; }}
[data-testid="stSidebar"] {{ background-color: {sidebar_color}; }}
.stButton > button {{ background-color: {btn_color}; color: white; border: none; border-radius: 6px; }}
.added    {{ color: {color_added}; font-family: monospace; }}
.modified {{ color: {color_modified}; font-family: monospace; }}
.removed  {{ color: {color_removed}; font-family: monospace; }}
.info-card {{
    background: {card_color};
    border: 1px solid {border_color};
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 0.9rem;
}}
</style>
""", unsafe_allow_html=True)

st.title("📁 File System Snapshot Tool")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Take Snapshot
# ══════════════════════════════════════════════════════════════════════════════
if section == "Take Snapshot":
    st.header("Take Snapshot")
    st.info("📤 Upload files from your computer — a snapshot will be created from them.")

    uploaded_files = st.file_uploader(
        "Upload files (select multiple)",
        accept_multiple_files=True,
        help="You can select an entire folder's files using Ctrl+A in the file dialog."
    )

    snapshot_name = st.text_input("Snapshot Name", placeholder="e.g. my_snapshot_v1")

    if uploaded_files:
        st.caption(f"📄 {len(uploaded_files)} file(s) selected")

    if st.button("💾 Save Snapshot", type="primary"):
        if not snapshot_name.strip():
            st.error("Please enter a snapshot name.")
        elif not uploaded_files:
            st.error("Please upload at least one file.")
        else:
            files_data = {}
            for uf in uploaded_files:
                raw = uf.read()
                files_data[uf.name] = {
                    "size": len(raw),
                    "hash": get_file_hash_bytes(raw)
                }

            snapshot = {"files": files_data}
            out_path = os.path.join(SNAPSHOT_DIR, snapshot_name.strip() + ".json")
            with open(out_path, "w") as fp:
                json.dump(snapshot, fp, indent=2)

            list_snapshots.clear()
            st.success(f"✅ Snapshot **{snapshot_name}** saved with {len(files_data)} file(s)!")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Snapshot History
# ══════════════════════════════════════════════════════════════════════════════
elif section == "Snapshot History":
    st.header("Snapshot History")
    snaps = list_snapshots()
    if not snaps:
        st.info("📭 No snapshots yet. Create one first!")
    else:
        cols = st.columns([4, 2, 1, 1])
        with cols[0]: st.write("**Name**")
        with cols[1]: st.write("**Date**")
        with cols[2]: st.write("**Files**")
        with cols[3]: st.write("**Del**")
        st.divider()
        for snap in snaps:
            cols = st.columns([4, 2, 1, 1])
            with cols[0]: st.write(f"📄 {snap['name']}")
            with cols[1]: st.write(snap["date"].strftime("%Y-%m-%d %H:%M"))
            with cols[2]: st.write(str(snap["total_files"]))
            with cols[3]:
                if st.button("🗑️", key=f"del_{snap['name']}"):
                    os.remove(os.path.join(SNAPSHOT_DIR, snap["name"]))
                    list_snapshots.clear()
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Compare Snapshots
# ══════════════════════════════════════════════════════════════════════════════
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
                    st.markdown(f"**{total} change(s) found** — "
                                f"<span style='color:{color_added}'>+{len(result_added)} added</span> | "
                                f"<span style='color:{color_modified}'>~{len(result_modified)} modified</span> | "
                                f"<span style='color:{color_removed}'>-{len(result_removed)} removed</span>",
                                unsafe_allow_html=True)
                    st.divider()

                    if result_added:
                        st.markdown("### ✅ Added")
                        for f in sorted(result_added):
                            st.markdown(f"<div class='info-card added'>+ {f}</div>", unsafe_allow_html=True)

                    if result_modified:
                        st.markdown("### 🔄 Modified")
                        for f in sorted(result_modified):
                            st.markdown(f"<div class='info-card modified'>~ {f}</div>", unsafe_allow_html=True)

                    if result_removed:
                        st.markdown("### ❌ Removed")
                        for f in sorted(result_removed):
                            st.markdown(f"<div class='info-card removed'>- {f}</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Compare Files
# ══════════════════════════════════════════════════════════════════════════════
elif section == "Compare Files":
    st.header("Compare Files")
    st.info("📤 Upload the same file from two different points in time to compare them.")

    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Old File**")
        old_upload = st.file_uploader("Upload old file", key="old_file")
    with cols[1]:
        st.markdown("**New File**")
        new_upload = st.file_uploader("Upload new file", key="new_file")

    if st.button("🔍 Compare Files", type="primary"):
        if not old_upload and not new_upload:
            st.error("Please upload both files.")
        elif not old_upload:
            st.error("Please upload the old file.")
        elif not new_upload:
            st.error("Please upload the new file.")
        else:
            old_bytes = old_upload.read()
            new_bytes = new_upload.read()

            old_hash = get_file_hash_bytes(old_bytes)
            new_hash = get_file_hash_bytes(new_bytes)

            old_size = len(old_bytes)
            new_size = len(new_bytes)

            # Determine status
            if old_hash == new_hash:
                status = "NO CHANGE"
            else:
                status = "MODIFIED"

            icons = {"MODIFIED": "🔄", "NO CHANGE": "✨"}
            clr   = color_modified if status == "MODIFIED" else "#8b949e"
            icon  = icons.get(status, "")

            st.markdown(
                f"**Status:** {icon} <span style='color:{clr}; font-weight:bold'>{status}</span>",
                unsafe_allow_html=True
            )

            # Details
            st.divider()
            d_cols = st.columns(2)
            with d_cols[0]:
                st.markdown(f"**Old File:** `{old_upload.name}`")
                st.caption(f"Size: {old_size:,} bytes")
                st.caption(f"MD5: `{old_hash}`")
            with d_cols[1]:
                st.markdown(f"**New File:** `{new_upload.name}`")
                st.caption(f"Size: {new_size:,} bytes")
                st.caption(f"MD5: `{new_hash}`")

            if status == "MODIFIED":
                size_diff = new_size - old_size
                sign = "+" if size_diff >= 0 else ""
                st.caption(f"Size difference: {sign}{size_diff:,} bytes")
