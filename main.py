#!/usr/bin/env python

import tempfile
import time
from pathlib import Path

import streamlit as st

from src.utils import create_zip_buffer, start_classification, validate_uploaded_files

st.title("Advanced Morphometric Classification")

# --- Poll for running classification (persists across reruns) ---
if st.session_state.get("running"):
    process = st.session_state["process"]
    status = st.empty()
    cancel = st.button("Cancel classification")

    if cancel:
        process.terminate()
        try:
            process.wait(timeout=5)
        except Exception:
            process.kill()
        st.session_state["running"] = False
        st.session_state["tmp_dir"].cleanup()
        status.warning("Classification cancelled.")
        st.stop()

    if process.poll() is None:  # still running
        status.info("Classification running...")
        time.sleep(0.5)
        st.rerun()
    else:
        st.session_state["running"] = False
        _, stderr = process.communicate()
        tmp_dir = st.session_state["tmp_dir"]
        output_dir = st.session_state["output_dir"]
        try:
            if process.returncode != 0:
                st.error(stderr)
            else:
                status.success("Done!")
                st.download_button(
                    label="Download results",
                    data=create_zip_buffer(output_dir),
                    file_name="results.zip",
                    mime="application/zip",
                )
        finally:
            tmp_dir.cleanup()

else:
    # --- Settings ---
    st.subheader("Model Parameters (leave as-is for defaults)")
    seed = st.number_input("Random seed", value=42, min_value=0)
    test_size = st.slider(
        "Test Size", min_value=0.1, max_value=0.5, value=0.25, step=0.05
    )
    min_samples = st.number_input(
        "Minimum total samples per class", value=3, min_value=1
    )
    n_splits = st.number_input("CV folds", value=5, min_value=2)

    # --- File importer ---
    st.subheader("Data importing")
    uploaded_files = st.file_uploader(
        "Select Morphologika files", type="txt", accept_multiple_files=True
    )

    # --- Classify button ---
    if st.button("Classify Morphologika files"):
        if not uploaded_files:
            st.error("No files uploaded.")
        else:
            errors = validate_uploaded_files(uploaded_files)

            if errors:
                for error in errors:
                    st.error(error)
                st.stop()
            else:
                tmp_dir = tempfile.TemporaryDirectory()
                tmp_path = Path(tmp_dir.name)

                input_dir = tmp_path / "input"
                input_dir.mkdir()
                file_paths = []
                for f in uploaded_files:
                    f.seek(0)
                    p = input_dir / f.name
                    p.write_bytes(f.read())
                    file_paths.append(str(p))

                output_dir = tmp_path / "output"
                output_dir.mkdir()

                process = start_classification(
                    output_dir=output_dir,
                    file_paths=file_paths,
                    test_size=test_size,
                    min_samples=min_samples,
                    n_splits=n_splits,
                    seed=seed,
                )

                st.session_state["process"] = process
                st.session_state["tmp_dir"] = tmp_dir
                st.session_state["output_dir"] = output_dir
                st.session_state["running"] = True
                st.rerun()

st.markdown("*Classification algorithm: Sara Behnamian. App: Oliver Todreas*")
