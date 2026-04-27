"""Streamlit web UI for File System Snapshot Difference tool."""
import os
import io
import hashlib
import zipfile
import json
from datetime import datetime

import streamlit as st

from src.diff import diff_snapshots, line_diff

st.set_page_config(
    page_title="SnapDiff — File System Snapshot Tool",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

MAX_FILE_SIZE_MB = 50


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


def build_snapshot_from_uploads(uploaded_files):
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


def build_snapshot_from_zip(zip_bytes: bytes):
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
    st.markdown("""
    <div style='text-align:center; padding: 10px 0 20px 0;'>
        <span style='font-size:2.5rem;'>📸</span>
        <h2 style='margin:4px 0 0 0; font-size:1.3rem; font-weight:700; letter-spacing:1px;'>SnapDiff</h2>
        <p style='margin:0; font-size:0.75rem; opacity:0.6;'>File Snapshot Tool</p>
    </div>
    """, unsafe_allow_html=True)

    theme = st.toggle("🌙 Dark Mode", value=st.session_state.theme)
    st.session_state.theme = theme
    st.divider()

    st.markdown("<p style='font-size:0.75rem; opacity:0.5; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>Navigation</p>", unsafe_allow_html=True)
    section = st.radio(
        "nav",
        ["📸 Take Snapshot", "🗂️ Snapshot History", "🔍 Compare Snapshots", "📄 Compare Files"],
        label_visibility="collapsed"
    )

    st.divider()
    snaps_count = len([f for f in os.listdir(SNAPSHOT_DIR) if f.endswith(".json")]) if os.path.exists(SNAPSHOT_DIR) else 0
    st.markdown(f"""
    <div style='text-align:center; opacity:0.6; font-size:0.8rem;'>
        <span>💾 {snaps_count} snapshot(s) saved</span>
    </div>
    """, unsafe_allow_html=True)

dark        = theme
bg          = "#0d1117" if dark else "#f0f2f6"
fg          = "#e6edf3" if dark else "#1f2328"
sidebar_bg  = "#010409" if dark else "#ffffff"
card_bg     = "#161b22" if dark else "#ffffff"
card_border = "#30363d" if dark else "#d0d7de"
input_bg    = "#0d1117" if dark else "#ffffff"
c_added     = "#3fb950" if dark else "#1a7f37"
c_modified  = "#d29922" if dark else "#9a6700"
c_removed   = "#f85149" if dark else "#cf222e"
c_equal     = "#8b949e" if dark else "#57606a"
diff_add_bg = "#0d4429" if dark else "#dafbe1"
diff_rem_bg = "#4d1818" if dark else "#ffebe9"
accent      = "#58a6ff" if dark else "#0969da"

st.markdown(f"""
<style>
/* ── Base ── */
.stApp {{ background-color: {bg}; color: {fg}; }}
[data-testid="stSidebar"] {{
    background-color: {sidebar_bg};
    border-right: 1px solid {card_border};
}}

/* ── Hide default streamlit elements ── */
#MainMenu, footer, header {{ visibility: hidden; }}

/* ── Buttons ── */
.stButton > button {{
    background: linear-gradient(135deg, #238636, #2ea043);
    color: white !important;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(35,134,54,0.3);
}}
.stButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(35,134,54,0.4);
}}

/* ── Cards ── */
.snap-card {{
    background: {card_bg};
    border: 1px solid {card_border};
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
}}
.snap-card:hover {{ border-color: {accent}; }}

/* ── Hero header ── */
.hero {{
    background: linear-gradient(135deg, #161b22 0%, #0d1117 50%, #161b22 100%);
    border: 1px solid {card_border};
    border-radius: 16px;
    padding: 32px 36px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}}
.hero::before {{
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 30% 50%, rgba(88,166,255,0.06) 0%, transparent 60%);
    pointer-events: none;
}}
.hero-title {{
    font-size: 2rem;
    font-weight: 800;
    margin: 0 0 6px 0;
    background: linear-gradient(90deg, #58a6ff, #79c0ff, #a5d6ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.hero-sub {{
    font-size: 0.95rem;
    opacity: 0.6;
    margin: 0;
}}

/* ── Section header ── */
.section-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid {card_border};
}}
.section-title {{
    font-size: 1.4rem;
    font-weight: 700;
    margin: 0;
}}

/* ── Stats badges ── */
.stat-box {{
    background: {card_bg};
    border: 1px solid {card_border};
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
}}
.stat-num {{
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 4px;
}}
.stat-label {{
    font-size: 0.75rem;
    opacity: 0.55;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

/* ── Diff table ── */
.diff-table {{
    width: 100%;
    border-collapse: collapse;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.8rem;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid {card_border};
}}
.diff-table td {{
    padding: 3px 10px;
    white-space: pre-wrap;
    word-break: break-all;
}}
.diff-add {{ background: {diff_add_bg}; color: {c_added}; }}
.diff-rem {{ background: {diff_rem_bg}; color: {c_removed}; }}
.diff-eq  {{ background: transparent; color: {c_equal}; }}
.lineno   {{
    color: #8b949e;
    text-align: right;
    user-select: none;
    min-width: 40px;
    border-right: 1px solid {card_border};
    padding-right: 8px !important;
    opacity: 0.6;
}}

/* ── Change badges ── */
.badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 2px;
}}
.badge-add  {{ background: rgba(63,185,80,0.15);  color: {c_added};    border: 1px solid rgba(63,185,80,0.3); }}
.badge-mod  {{ background: rgba(210,153,34,0.15); color: {c_modified}; border: 1px solid rgba(210,153,34,0.3); }}
.badge-rem  {{ background: rgba(248,81,73,0.15);  color: {c_removed};  border: 1px solid rgba(248,81,73,0.3); }}

/* ── File row ── */
.file-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 8px;
    margin: 3px 0;
    font-family: monospace;
    font-size: 0.88rem;
    border: 1px solid transparent;
}}
.file-row-add {{ background: rgba(63,185,80,0.08);  border-color: rgba(63,185,80,0.2);  color: {c_added}; }}
.file-row-rem {{ background: rgba(248,81,73,0.08);  border-color: rgba(248,81,73,0.2);  color: {c_removed}; }}
.file-row-mod {{ background: rgba(210,153,34,0.08); border-color: rgba(210,153,34,0.2); color: {c_modified}; }}

/* ── Upload area ── */
[data-testid="stFileUploader"] {{
    border: 2px dashed {card_border};
    border-radius: 12px;
    padding: 8px;
    transition: border-color 0.2s;
}}
[data-testid="stFileUploader"]:hover {{ border-color: {accent}; }}

/* ── Radio buttons ── */
[data-testid="stRadio"] label {{
    padding: 6px 12px;
    border-radius: 8px;
    transition: background 0.15s;
}}
[data-testid="stRadio"] label:hover {{ background: rgba(88,166,255,0.08); }}

/* ── Inputs ── */
.stTextInput input {{
    background: {input_bg} !important;
    border: 1px solid {card_border} !important;
    border-radius: 8px !important;
    color: {fg} !important;
}}
.stTextInput input:focus {{
    border-color: {accent} !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.15) !important;
}}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {{
    background: {input_bg} !important;
    border: 1px solid {card_border} !important;
    border-radius: 8px !important;
}}
</style>
""", unsafe_allow_html=True)

# ── Hero Banner ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
    <p class="hero-title">📸 SnapDiff</p>
    <p class="hero-sub">Track file changes with precision — snapshot, compare, and diff your files instantly</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 1 — TAKE SNAPSHOT
# ══════════════════════════════════════════════════════════════════════════════
if section == "📸 Take Snapshot":
    st.markdown("""
    <div class="section-header">
        <span style="font-size:1.6rem;">📸</span>
        <p class="section-title">Take Snapshot</p>
    </div>
    """, unsafe_allow_html=True)

    mode = st.radio("Upload mode", ["📄 Individual Files", "🗜️ ZIP Folder"], horizontal=True)
    st.markdown("<br>", unsafe_allow_html=True)

    files_data = {}
    skipped    = []

    if mode == "📄 Individual Files":
        st.markdown(f"""
        <div class="snap-card">
            <p style="margin:0 0 4px 0; font-weight:600;">📄 Upload Files</p>
            <p style="margin:0; opacity:0.6; font-size:0.85rem;">Select multiple files using <b>Ctrl+A</b> or <b>Shift+Click</b> in the file dialog. Max {MAX_FILE_SIZE_MB}MB per file.</p>
        </div>
        """, unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload files", accept_multiple_files=True, label_visibility="collapsed")
        if uploaded:
            files_data, skipped = build_snapshot_from_uploads(uploaded)
            st.markdown(f"""
            <div style="display:flex; gap:12px; margin-top:8px;">
                <span class="badge badge-add">✅ {len(files_data)} files ready</span>
                {"<span class='badge badge-mod'>⚠️ " + str(len(skipped)) + " skipped</span>" if skipped else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="snap-card">
            <p style="margin:0 0 4px 0; font-weight:600;">🗜️ Upload ZIP Folder</p>
            <p style="margin:0; opacity:0.6; font-size:0.85rem;">Compress your entire folder into a ZIP file and upload it here.</p>
        </div>
        """, unsafe_allow_html=True)
        zip_upload = st.file_uploader("Upload ZIP file", type=["zip"], label_visibility="collapsed")
        if zip_upload:
            with st.spinner("⚙️ Extracting ZIP…"):
                files_data, skipped = build_snapshot_from_zip(zip_upload.read())
            st.markdown(f"""
            <div style="display:flex; gap:12px; margin-top:8px;">
                <span class="badge badge-add">✅ {len(files_data)} files extracted</span>
                {"<span class='badge badge-mod'>⚠️ " + str(len(skipped)) + " skipped</span>" if skipped else ""}
            </div>
            """, unsafe_allow_html=True)
            if skipped:
                with st.expander("View skipped files"):
                    st.write(skipped)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 2])
    with col1:
        snapshot_name = st.text_input("📝 Snapshot Name", placeholder="e.g. project_v1  or  backup_2024")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        save_btn = st.button("💾 Save Snapshot", type="primary", disabled=not files_data, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📥 Import existing snapshot JSON"):
        import_file = st.file_uploader("Import snapshot JSON", type=["json"], key="import_snap", label_visibility="collapsed")

    if save_btn:
        if not snapshot_name.strip():
            st.error("⚠️ Please enter a snapshot name.")
        else:
            snapshot = {"files": files_data}
            out_path = os.path.join(SNAPSHOT_DIR, snapshot_name.strip() + ".json")
            with open(out_path, "w") as fp:
                json.dump(snapshot, fp, indent=2)
            list_snapshots.clear()
            st.success(f"✅ Snapshot **{snapshot_name}** saved with **{len(files_data)}** file(s)!")
            st.balloons()

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
    st.markdown("""
    <div class="section-header">
        <span style="font-size:1.6rem;">🗂️</span>
        <p class="section-title">Snapshot History</p>
    </div>
    """, unsafe_allow_html=True)

    snaps = list_snapshots()

    if not snaps:
        st.markdown("""
        <div class="snap-card" style="text-align:center; padding:40px;">
            <p style="font-size:2.5rem; margin:0;">📭</p>
            <p style="font-size:1.1rem; font-weight:600; margin:8px 0 4px 0;">No snapshots yet</p>
            <p style="opacity:0.5; margin:0; font-size:0.85rem;">Go to "Take Snapshot" to create your first one</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        total_files = sum(s["total_files"] for s in snaps)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="stat-box">
                <div class="stat-num" style="color:#58a6ff;">{len(snaps)}</div>
                <div class="stat-label">Total Snapshots</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="stat-box">
                <div class="stat-num" style="color:#3fb950;">{total_files}</div>
                <div class="stat-label">Total Files Tracked</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            latest = snaps[0]["date"].strftime("%b %d, %Y")
            st.markdown(f"""<div class="stat-box">
                <div class="stat-num" style="color:#d29922; font-size:1.2rem;">{latest}</div>
                <div class="stat-label">Latest Snapshot</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        hdr = st.columns([4, 2, 1, 1, 1])
        for col, label in zip(hdr, ["📄 Name", "🕐 Date", "📊 Files", "⬇️", "🗑️"]):
            col.markdown(f"<span style='opacity:0.5; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.8px;'>{label}</span>", unsafe_allow_html=True)
        st.divider()

        for snap in snaps:
            row = st.columns([4, 2, 1, 1, 1])
            row[0].markdown(f"<span style='font-weight:500;'>📄 {snap['name'].replace('.json','')}</span>", unsafe_allow_html=True)
            row[1].markdown(f"<span style='opacity:0.7; font-size:0.85rem;'>{snap['date'].strftime('%Y-%m-%d %H:%M')}</span>", unsafe_allow_html=True)
            row[2].markdown(f"<span class='badge badge-add'>{snap['total_files']}</span>", unsafe_allow_html=True)

            snap_path = os.path.join(SNAPSHOT_DIR, snap["name"])
            with open(snap_path, "rb") as fp:
                snap_bytes = fp.read()
            row[3].download_button("⬇️", data=snap_bytes, file_name=snap["name"],
                                   mime="application/json", key=f"dl_{snap['name']}")
            if row[4].button("🗑️", key=f"del_{snap['name']}"):
                os.remove(snap_path)
                list_snapshots.clear()
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# 3 — COMPARE SNAPSHOTS
# ══════════════════════════════════════════════════════════════════════════════
elif section == "🔍 Compare Snapshots":
    st.markdown("""
    <div class="section-header">
        <span style="font-size:1.6rem;">🔍</span>
        <p class="section-title">Compare Snapshots</p>
    </div>
    """, unsafe_allow_html=True)

    snaps = list_snapshots()

    if len(snaps) < 2:
        st.markdown("""
        <div class="snap-card" style="text-align:center; padding:40px;">
            <p style="font-size:2.5rem; margin:0;">⚠️</p>
            <p style="font-size:1.1rem; font-weight:600; margin:8px 0 4px 0;">Need at least 2 snapshots</p>
            <p style="opacity:0.5; margin:0; font-size:0.85rem;">Create more snapshots to compare them</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        snap_names = [s["name"] for s in snaps]
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<span style='opacity:0.6; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.8px;'>SNAPSHOT A — OLDER</span>", unsafe_allow_html=True)
            snap_a = st.selectbox("A", snap_names, index=len(snap_names)-1, label_visibility="collapsed")
        with col2:
            st.markdown("<span style='opacity:0.6; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.8px;'>SNAPSHOT B — NEWER</span>", unsafe_allow_html=True)
            snap_b = st.selectbox("B", snap_names, index=0, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Compare Snapshots", type="primary", use_container_width=False):
            if snap_a == snap_b:
                st.warning("⚠️ Please select two different snapshots.")
            else:
                with st.spinner("Comparing snapshots…"):
                    with open(os.path.join(SNAPSHOT_DIR, snap_a)) as fa:
                        old = json.load(fa)
                    with open(os.path.join(SNAPSHOT_DIR, snap_b)) as fb:
                        new = json.load(fb)
                    r_added, r_removed, r_modified = diff_snapshots(old, new)

                total = len(r_added) + len(r_removed) + len(r_modified)
                st.markdown("<br>", unsafe_allow_html=True)

                if total == 0:
                    st.success("✨ Snapshots are identical — no differences found!")
                else:
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown(f"""<div class="stat-box">
                            <div class="stat-num" style="color:#58a6ff;">{total}</div>
                            <div class="stat-label">Total Changes</div>
                        </div>""", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""<div class="stat-box">
                            <div class="stat-num" style="color:{c_added};">{len(r_added)}</div>
                            <div class="stat-label">Added</div>
                        </div>""", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"""<div class="stat-box">
                            <div class="stat-num" style="color:{c_modified};">{len(r_modified)}</div>
                            <div class="stat-label">Modified</div>
                        </div>""", unsafe_allow_html=True)
                    with c4:
                        st.markdown(f"""<div class="stat-box">
                            <div class="stat-num" style="color:{c_removed};">{len(r_removed)}</div>
                            <div class="stat-label">Removed</div>
                        </div>""", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    if r_added:
                        st.markdown(f"#### ✅ Added &nbsp; <span class='badge badge-add'>{len(r_added)}</span>", unsafe_allow_html=True)
                        for f in sorted(r_added):
                            st.markdown(f"<div class='file-row file-row-add'>＋ &nbsp;{f}</div>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

                    if r_removed:
                        st.markdown(f"#### ❌ Removed &nbsp; <span class='badge badge-rem'>{len(r_removed)}</span>", unsafe_allow_html=True)
                        for f in sorted(r_removed):
                            st.markdown(f"<div class='file-row file-row-rem'>－ &nbsp;{f}</div>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

                    if r_modified:
                        st.markdown(f"#### 🔄 Modified &nbsp; <span class='badge badge-mod'>{len(r_modified)}</span>", unsafe_allow_html=True)
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
                                    st.markdown(f"""
                                    <div style="display:flex; gap:10px; margin-bottom:10px;">
                                        <span class="badge badge-add">+{added_c} lines</span>
                                        <span class="badge badge-rem">-{removed_c} lines</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    rows_html = ""
                                    for d in diff_lines:
                                        css   = "diff-add" if d["type"] == "added" else "diff-rem" if d["type"] == "removed" else "diff-eq"
                                        sign  = "+" if d["type"] == "added" else "-" if d["type"] == "removed" else " "
                                        old_n = str(d["old_no"]) if d["old_no"] else ""
                                        new_n = str(d["new_no"]) if d["new_no"] else ""
                                        line  = d["line"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                                        rows_html += f"<tr class='{css}'><td class='lineno'>{old_n}</td><td class='lineno'>{new_n}</td><td>{sign} {line}</td></tr>"
                                    st.markdown(f"<table class='diff-table'>{rows_html}</table>", unsafe_allow_html=True)
                                else:
                                    old_size = old_entry.get("size", 0)
                                    new_size = new_entry.get("size", 0)
                                    diff_b   = new_size - old_size
                                    sign     = "+" if diff_b >= 0 else ""
                                    st.info(f"🔢 Binary file — size changed: **{sign}{diff_b:,} bytes**")


# ══════════════════════════════════════════════════════════════════════════════
# 4 — COMPARE FILES
# ══════════════════════════════════════════════════════════════════════════════
elif section == "📄 Compare Files":
    st.markdown("""
    <div class="section-header">
        <span style="font-size:1.6rem;">📄</span>
        <p class="section-title">Compare Files</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="snap-card">
        <p style="margin:0 0 4px 0; font-weight:600;">📤 Upload two versions of the same file</p>
        <p style="margin:0; opacity:0.6; font-size:0.85rem;">Upload the old and new version — the tool will compare them byte-by-byte and show exact line changes.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<span style='opacity:0.6; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.8px;'>OLD FILE</span>", unsafe_allow_html=True)
        old_up = st.file_uploader("Old file", key="old_file", label_visibility="collapsed")
    with col2:
        st.markdown("<span style='opacity:0.6; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.8px;'>NEW FILE</span>", unsafe_allow_html=True)
        new_up = st.file_uploader("New file", key="new_file", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 Compare Files", type="primary"):
        if not old_up or not new_up:
            st.error("⚠️ Please upload both files.")
        else:
            old_bytes = old_up.read()
            new_bytes = new_up.read()
            old_hash  = get_hash(old_bytes)
            new_hash  = get_hash(new_bytes)
            old_size  = len(old_bytes)
            new_size  = len(new_bytes)
            status    = "NO CHANGE" if old_hash == new_hash else "MODIFIED"

            st.markdown("<br>", unsafe_allow_html=True)

            if status == "NO CHANGE":
                st.markdown(f"""
                <div style="background:rgba(63,185,80,0.1); border:1px solid rgba(63,185,80,0.3);
                     border-radius:12px; padding:20px 24px; text-align:center;">
                    <p style="font-size:2rem; margin:0;">✨</p>
                    <p style="font-size:1.2rem; font-weight:700; color:{c_added}; margin:4px 0;">NO CHANGE</p>
                    <p style="opacity:0.6; margin:0; font-size:0.85rem;">Files are byte-for-byte identical</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:rgba(210,153,34,0.1); border:1px solid rgba(210,153,34,0.3);
                     border-radius:12px; padding:20px 24px; text-align:center;">
                    <p style="font-size:2rem; margin:0;">🔄</p>
                    <p style="font-size:1.2rem; font-weight:700; color:{c_modified}; margin:4px 0;">MODIFIED</p>
                    <p style="opacity:0.6; margin:0; font-size:0.85rem;">Files are different</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f"""<div class="snap-card">
                    <p style="margin:0 0 8px 0; font-weight:600; opacity:0.6; font-size:0.8rem; text-transform:uppercase;">OLD FILE</p>
                    <p style="margin:0 0 4px 0; font-weight:600;">📄 {old_up.name}</p>
                    <p style="margin:0; font-family:monospace; font-size:0.8rem; opacity:0.6;">Size: {old_size:,} bytes</p>
                    <p style="margin:0; font-family:monospace; font-size:0.75rem; opacity:0.5; word-break:break-all;">MD5: {old_hash}</p>
                </div>""", unsafe_allow_html=True)
            with d2:
                diff_b = new_size - old_size
                sign   = "+" if diff_b >= 0 else ""
                size_color = c_added if diff_b <= 0 else c_modified
                st.markdown(f"""<div class="snap-card">
                    <p style="margin:0 0 8px 0; font-weight:600; opacity:0.6; font-size:0.8rem; text-transform:uppercase;">NEW FILE</p>
                    <p style="margin:0 0 4px 0; font-weight:600;">📄 {new_up.name}</p>
                    <p style="margin:0; font-family:monospace; font-size:0.8rem; opacity:0.6;">Size: {new_size:,} bytes &nbsp;<span style="color:{size_color};">({sign}{diff_b:,})</span></p>
                    <p style="margin:0; font-family:monospace; font-size:0.75rem; opacity:0.5; word-break:break-all;">MD5: {new_hash}</p>
                </div>""", unsafe_allow_html=True)

            if status == "MODIFIED" and is_text(old_bytes) and is_text(new_bytes):
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 📝 Line-by-Line Diff")
                old_text   = old_bytes.decode("utf-8", errors="replace")
                new_text   = new_bytes.decode("utf-8", errors="replace")
                diff_lines = line_diff(old_text, new_text)
                added_c    = sum(1 for d in diff_lines if d["type"] == "added")
                removed_c  = sum(1 for d in diff_lines if d["type"] == "removed")
                st.markdown(f"""
                <div style="display:flex; gap:10px; margin-bottom:12px;">
                    <span class="badge badge-add">+{added_c} lines added</span>
                    <span class="badge badge-rem">-{removed_c} lines removed</span>
                </div>
                """, unsafe_allow_html=True)
                rows_html = ""
                for d in diff_lines:
                    css  = "diff-add" if d["type"] == "added" else "diff-rem" if d["type"] == "removed" else "diff-eq"
                    sign = "+" if d["type"] == "added" else "-" if d["type"] == "removed" else " "
                    old_n = str(d["old_no"]) if d["old_no"] else ""
                    new_n = str(d["new_no"]) if d["new_no"] else ""
                    line  = d["line"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                    rows_html += f"<tr class='{css}'><td class='lineno'>{old_n}</td><td class='lineno'>{new_n}</td><td>{sign} {line}</td></tr>"
                st.markdown(f"<table class='diff-table'>{rows_html}</table>", unsafe_allow_html=True)
            elif status == "MODIFIED":
                st.info("🔢 Binary file — line diff not available.")
