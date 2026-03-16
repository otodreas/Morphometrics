#!/usr/bin/env python

import subprocess
import tempfile
from pathlib import Path

import streamlit as st

from src.validate import is_morphologika

st.title("Advanced Morphometric Classification")
tmp_dir = None

# Settings buttons
st.subheader("Model Parameters (leave as-is for defaults)")
seed = st.number_input("Random seed", value=42, min_value=0)
test_size = st.slider("Test Size", min_value=0.1, max_value=0.5, value=0.25, step=0.05)
min_samples = st.number_input("Minimum total samples per class", value=3, min_value=1)
n_splits = st.number_input("CV folds", value=5, min_value=2)

# File importer
st.subheader("Data importing")
uploaded_files = st.file_uploader(
    "Select Morphologika files", type="txt", accept_multiple_files=True
)

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

        # If there were errors, display them and interrupt execution
        if errors:
            for error in errors:
                st.error(error)

            st.stop()

        # If all files are valid, proceed to classification
        else:
            try:
                tmp_dir = tempfile.TemporaryDirectory()
                tmp_path = Path(tmp_dir.name)

                # save uploaded files to temp input dir
                input_dir = tmp_path / "input"
                input_dir.mkdir()
                file_paths = []
                for f in uploaded_files:
                    p = input_dir / f.name
                    p.write_bytes(f.read())
                    file_paths.append(str(p))

                # create temp output dir
                output_dir = tmp_path / "output"
                output_dir.mkdir()

                print(*file_paths)

                # run script
                result = subprocess.run(
                    [
                        "python",
                        "src/classification.py",
                        "--output_dir",
                        str(output_dir),
                        "--files",
                        *file_paths,
                        "--test_size",
                        str(test_size),
                        "--min_samples",
                        str(min_samples),
                        "--n_splits",
                        str(n_splits),
                        "--seed",
                        str(seed),
                    ],
                    # stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                if result.returncode != 0:
                    st.error(result.stderr)
                else:
                    st.success("Done!")
                    for output_file in output_dir.iterdir():
                        st.download_button(
                            label=f"Download {output_file.name}",
                            data=output_file.read_bytes(),
                            file_name=output_file.name,
                        )
            finally:
                if tmp_dir:
                    tmp_dir.cleanup()

st.markdown("*Classification algorithm: Sara Behnamian. App: Oliver Todreas*")
