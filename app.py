"""Streamlit web UI for File System Snapshot Difference tool."""
import os
import streamlit as st
import json
from datetime import datetime

from src.snapshot import take_snapshot
from src.diff import diff_snapshots
from src.file_compare import file_status

st.set_page_config(page_title="File System Snapshot", page_icon="📁")

SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)


@st.cache_data(show_spinner=False)
def get_folder_stats(path):
    """Return (total_files, total_folders, last_modified)."""
    total_files = 0
    total_folders = 0
    last_mod = None
    for root, dirs, files in os.walk(path):
        total_folders += len(dirs)
        total_files += len(files)
        for f in files:
            fpath = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(fpath)
                if last_mod is None or mtime > last_mod:
                    last_mod = mtime
            except OSError:
                continue
    return total_files, total_folders, datetime.fromtimestamp(last_mod) if last_mod else None


@st.cache_data(show_spinner=False)
def list_snapshots():
    """Return sorted list of snapshot metadata."""
    snaps = []
    if not os.path.exists(SNAPSHOT_DIR):
        return snaps
    for f in os.listdir(SNAPSHOT_DIR):
        if f.endswith('.json'):
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


# Theme management
if "theme" not in st.session_state:
    st.session_state.theme = True

# Sidebar Settings
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

# Theme colors
dark = theme
bg_color = "#0d1117" if dark else "#ffffff"
text_color = "#c9d1d9" if dark else "#24292f"
sidebar_color = "#161b22" if dark else "#f0f2f6"
btn_color = "#238636"
color_added = "#3fb950" if dark else "#22863a"
color_modified = "#d29922" if dark else "#b08800"
color_removed = "#f85149" if dark else "#cb2431"

st.markdown(
    f"""
<style>
.stApp {{ background-color: {bg_color}; color: {text_color}; }}
[data-testid="stSidebar"] {{ background-color: {sidebar_color}; }}
.stButton > button {{ background-color: {btn_color}; color: white; border: none; }}
.added {{ color: {color_added}; }}
.modified {{ color: {color_modified}; }}
.removed {{ color: {color_removed}; }}
</style>
""",
    unsafe_allow_html=True,
)

st.title("📁 File System Snapshot Tool")

if section == "Take Snapshot":
    st.header("Take Snapshot")
    folder_path = st.text_input("Folder Path", placeholder="Enter folder path...")
    col1, col2 = st.columns([3, 1])
    with col1:
        snapshot_name = st.text_input("Snapshot Name", placeholder="my_snapshot")
    if folder_path and os.path.isdir(folder_path):
        files, folders, last_mod = get_folder_stats(folder_path)
        st.caption(f"📁 {files} files | 📂 {folders} folders | 🕐 {last_mod}")
    if st.button("Take Snapshot", type="primary") and folder_path:
        if not snapshot_name:
            st.error("Please enter a snapshot name")
        elif not os.path.isdir(folder_path):
            st.error("Invalid folder path")
        else:
            output = os.path.join(SNAPSHOT_DIR, snapshot_name + ".json")
            try:
                result = take_snapshot(folder_path, output)
                list_snapshots.clear()
                st.success(f"✅ Snapshot saved with {len(result)} files!")
            except Exception as e:
                st.error(f"Error: {e}")

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
            with cols[1]: st.write(snap['date'].strftime("%Y-%m-%d %H:%M"))
            with cols[2]: st.write(str(snap['total_files']))
            with cols[3]:
                if st.button("🗑️", key=f"del_{snap['name']}"):
                    os.remove(os.path.join(SNAPSHOT_DIR, snap['name']))
                    list_snapshots.clear()
                    st.rerun()

elif section == "Compare Snapshots":
    st.header("Compare Snapshots")
    snaps = list_snapshots()
    if len(snaps) < 2:
        st.warning("⚠️ Need at least 2 snapshots to compare")
    else:
        snap_names = [s['name'] for s in snaps]
        cols = st.columns(2)
        with cols[0]:
            snap_a = st.selectbox("Snapshot A", snap_names, index=0)
        with cols[1]:
            snap_b = st.selectbox("Snapshot B", snap_names, index=max(0, len(snap_names) - 1))
        if st.button("🔍 Compare", type="primary"):
            with open(os.path.join(SNAPSHOT_DIR, snap_a)) as fa, \
                 open(os.path.join(SNAPSHOT_DIR, snap_b)) as fb:
                old, new = json.load(fa), json.load(fb)
            result_added, result_removed, result_modified = diff_snapshots(old, new)
            if result_added:
                st.markdown("### ✅ Added")
                for f in result_added:
                    st.markdown(f"<span class='added'>+ {f}</span>", unsafe_allow_html=True)
            if result_modified:
                st.markdown("### 🔄 Modified")
                for f in result_modified:
                    st.markdown(f"<span class='modified'>~ {f}</span>", unsafe_allow_html=True)
            if result_removed:
                st.markdown("### ❌ Removed")
                for f in result_removed:
                    st.markdown(f"<span class='removed'>- {f}</span>", unsafe_allow_html=True)
            if not (result_added or result_modified or result_removed):
                st.success("✨ No differences found!")

elif section == "Compare Files":
    st.header("Compare Files")
    cols = st.columns(2)
    with cols[0]:
        old_file = st.text_input("Old File Path", placeholder="/path/to/old_file.txt")
    with cols[1]:
        new_file = st.text_input("New File Path", placeholder="/path/to/new_file.txt")
    if st.button("🔍 Compare Files", type="primary") and old_file and new_file:
        status = file_status(old_file, new_file)
        icons = {
            "ADDED": "✅",
            "REMOVED": "❌",
            "MODIFIED": "🔄",
            "NO CHANGE": "✨",
            "BOTH FILES MISSING": "❓"
        }
        status_colors = {
            "ADDED": color_added,
            "REMOVED": color_removed,
            "MODIFIED": color_modified,
            "NO CHANGE": "#8b949e",
            "BOTH FILES MISSING": "#8b949e"
        }
        icon = icons.get(status, "")
        clr = status_colors.get(status, "#8b949e")
        st.markdown(
            f"**Status:** {icon} <span style='color:{clr}'>{status}</span>",
            unsafe_allow_html=True
        )
