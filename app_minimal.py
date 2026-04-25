import streamlit as st

st.set_page_config(page_title="File System Snapshot", page_icon="📁")

st.title("📁 File System Snapshot Tool")
st.write("Welcome! Use the sections below to manage your snapshots.")

section = st.radio("Go to", ["Take Snapshot", "Snapshot History", "Compare Snapshots", "Compare Files"], horizontal=True)

if section == "Take Snapshot":
    st.header("Take Snapshot")
    st.info("Configure folder path and snapshot name above to create a new snapshot.")

elif section == "Snapshot History":
    st.header("Snapshot History")
    st.info("No snapshots found. Create one first!")

elif section == "Compare Snapshots":
    st.header("Compare Snapshots")
    st.info("Select two snapshots to compare their differences.")

elif section == "Compare Files":
    st.header("Compare Files")
    st.info("Enter two file paths to compare their status.")