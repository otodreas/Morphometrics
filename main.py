#!/usr/bin/env python

import streamlit as st


def is_morphologika(file: list[str]) -> bool:
    # Instantiate dictionary with required headers as keys and False as values
    required_headers = {
        "[individuals]": False,
        "[landmarks]": False,
        "[dimensions]": False,
        "[names]": False,
        "[rawpoints]": False,
    }

    # Loop through lines
    for line in file:
        if line.strip() in required_headers.keys():
            # Update dictionary value to True for the corresponding header
            required_headers[line.strip()] = True
            # Break if all required headers have been found
            if all(required_headers.values()):
                return True

    # If not all required headers were found, return False
    return False


def upload():
    st.title("Advanced Morphometric Classification")

    # File importer
    uploaded_files = st.file_uploader(
        "Import Morphologika data", type="txt", accept_multiple_files=True
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

            # TODO: check for duplicate files?

            # If there were errors, display them and interrupt execution
            if errors:
                for error in errors:
                    st.error(error)

                st.stop()

            # If all files are valid, proceed to classification
            else:
                st.session_state.files = uploaded_files
                st.session_state.screen = "running"
                st.rerun()

    st.markdown("*Classification algorithm: Sara Behnamian. App: Oliver Todreas*")


def running():
    st.title("Classifying morphologika data...")
    cancel = st.button("Cancel")
    if cancel:
        st.session_state.screen = "upload"
        st.rerun()
    # import subprocess

    # subprocess.run(["python3", "test_heartbeat.py"])


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
