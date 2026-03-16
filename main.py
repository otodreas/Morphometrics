#!/usr/bin/env python

import os
import subprocess
import tempfile
from pathlib import Path

import streamlit as st

import src.classification as classification
from src.validate import is_morphologika


def upload():
    st.title("Advanced Morphometric Classification")

    # Settings buttons
    st.subheader("Model Parameters (leave as-is for defaults)")
    st.session_state.random_state = st.number_input(
        "Random seed", value=42, min_value=0
    )
    st.session_state.test_size = st.slider(
        "Test Size", min_value=0.1, max_value=0.5, value=0.25, step=0.05
    )
    st.session_state.min_samples = st.number_input(
        "Minimum total samples per class", value=3, min_value=1
    )
    st.session_state.n_splits = st.number_input("CV folds", value=5, min_value=2)

    # File importer
    st.subheader("Data importing")
    uploaded_files = st.file_uploader(
        "Select Morphologika files", type="txt", accept_multiple_files=True
    )

    # Output directory path
    st.subheader("Output directory")
    st.session_state.output_dir = st.text_input("Output directory path", value="")

    # Create temporary directory and save uploaded files
    with tempfile.TemporaryDirectory() as tmp_dir:
        uploaded_files_tmp_paths = []
        for f in uploaded_files:
            tmp_path = Path(tmp_dir) / f.name
            tmp_path.write_bytes(f.read())
            uploaded_files_tmp_paths.append(str(tmp_path))

    # Classify button
    classify = st.button("Classify Morphologika files")

    # Handle classify button click
    if classify:
        # Check if any files were uploaded
        if len(uploaded_files) == 0:
            st.error("No files uploaded.")

        else:
            file_names, errors = [], []
            # Loop through uploaded files
            for file in uploaded_files:
                file_names.append(file.name)
                # Read file and check validity
                try:
                    content = file.read().decode("utf-8").splitlines()
                    if not is_morphologika(content):
                        errors.append(f"{file.name} is not a valid Morphologika file.")

                # Throw unicode decode error if decoding fails
                except UnicodeDecodeError:
                    errors.append(
                        f"{file.name} could not be read. Please ensure it is UTF-8 encoded."
                    )

            # Check for duplicate file names
            duplicates = [name for name in file_names if file_names.count(name) > 1]
            if duplicates:
                errors.append(
                    f"Multiple files with the name ({', '.join(set(duplicates))}) detected. Please give them unique names before uploading."
                )

            # TODO: check for duplicate files?

            # If there were errors, display them and interrupt execution
            if errors:
                for error in errors:
                    st.error(error)

                st.stop()

            # If all files are valid, proceed to classification
            else:
                st.session_state.files = uploaded_files_tmp_paths
                print(st.session_state.files)
                st.session_state.screen = "running"
                st.rerun()

    st.markdown("*Classification algorithm: Sara Behnamian. App: Oliver Todreas*")


def running():
    st.title("Classifying morphologika data...")

    subprocess.run(
        [
            "python",
            "src/classification.py",
            "--output_dir",
            st.session_state.output_dir,
            "--files",
            st.session_state.files,
            "--test_size",
            st.session_state.test_size,
            "--min_samples",
            st.session_state.min_samples,
            "--n_splits",
            st.session_state.n_splits,
            "--random_state",
            st.session_state.random_state,
        ]
    )

    # # Initialize cancel flag if not already set
    # if "cancel_requested" not in st.session_state:
    #     st.session_state.cancel_requested = False

    # cancel = st.button("Cancel")
    # if cancel:
    #     st.session_state.cancel_requested = True
    #     st.session_state.screen = "upload"
    #     st.rerun()

    # if not st.session_state.cancel_requested:
    #     hb(st.session_state)


def dashboard():
    pass


def main():
    if "screen" not in st.session_state:
        st.session_state.screen = "upload"

    if st.session_state.screen == "upload":
        upload()

    elif st.session_state.screen == "running":
        running()

    else:
        dashboard()


if __name__ == "__main__":
    main()