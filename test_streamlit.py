import os
import streamlit as st
import json

st.set_page_config(page_title="Test App", page_icon="📁")

st.title("Test App")
st.write("Hello World!")

if st.button("Test Button"):
    st.success("Button clicked!")

st.write(f"Current directory: {os.getcwd()}")
st.write(f"Snapshot dir exists: {os.path.exists('snapshots')}")