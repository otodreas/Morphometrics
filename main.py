#!/usr/bin/env python

import tempfile
import time
from pathlib import Path

import streamlit as st

from src.utils import create_zip_buffer, start_classification, validate_uploaded_files

st.title("Advanced Morphometric Classification")

# If a classification process was started in a previous rerun, resume it
if st.session_state.get("running"):
    # Retrieve the classification process from the session state
    process = st.session_state["process"]

    # Assign empty status and cancel button placeholders
    status = st.empty()
    cancel = st.button("Cancel classification")

    # Handle cancellation of the classification process
    if cancel:
        # Try to gracefully terminate the process
        process.terminate()
        try:
            process.wait(timeout=5)

        # Force-kill if it doesn't stop in time
        except Exception:
            process.kill()

        # Update session state to reflect the process has been cancelled
        st.session_state["running"] = False

        # Clean up temp files
        st.session_state["tmp_dir"].cleanup()
        status.warning("Classification cancelled.")
        st.stop()

    # If the process is still running, show a status message and rerun to poll again
    if process.poll() is None:
        status.info("Classification running...")
        time.sleep(0.5)

        # Rerun the script to poll again on the next cycle
        st.rerun()

    # Process has returned an exit code
    else:
        # Update session state to reflect the process has completed
        st.session_state["running"] = False

        # Keep stderr output for error reporting
        _, stderr = process.communicate()

        # Assign temp dir and output dir from session state for cleanup and result zip download
        tmp_dir = st.session_state["tmp_dir"]
        output_dir = st.session_state["output_dir"]

        # Check if the exit code indicates an error
        try:
            # If the exit code is non-zero, report the error
            if process.returncode != 0:
                st.error(stderr)

            # If the exit code is zero, the process completed successfully
            else:
                status.success("Done!")

                # Zip the output directory and offer it as a download
                st.download_button(
                    label="Download results",
                    data=create_zip_buffer(output_dir),
                    file_name="results.zip",
                    mime="application/zip",
                )

        finally:
            # Always clean up temp files regardless of success or failure
            tmp_dir.cleanup()

# Start a fresh classification if none is currently running
else:
    # Create settings buttons
    st.subheader("Model Parameters (leave as-is for defaults)")
    seed = st.number_input("Random seed", value=42, min_value=0)
    test_size = st.slider(
        "Test Size", min_value=0.1, max_value=0.5, value=0.25, step=0.05
    )
    min_samples = st.number_input(
        "Minimum total samples per class", value=3, min_value=1
    )
    n_splits = st.number_input("CV folds", value=5, min_value=2)

    # Show file importer
    st.subheader("Data importing")
    uploaded_files = st.file_uploader(
        "Select Morphologika files", type="txt", accept_multiple_files=True
    )

    # Classify button
    if st.button("Classify Morphologika files"):
        # Throw an error if no files are uploaded
        if not uploaded_files:
            st.error("No files uploaded.")
        else:
            # Check if all uploaded files look like Morphologika files
            errors = validate_uploaded_files(uploaded_files)

            # If there are errors, show them and stop
            if errors:
                for error in errors:
                    st.error(error)

                st.stop()

            # If there are no errors, proceed with classification
            else:
                # Create a temp directory to hold input and output files for this run
                tmp_dir = tempfile.TemporaryDirectory()
                tmp_path = Path(tmp_dir.name)

                # Create input and output directories inside the temp directory
                input_dir = tmp_path / "input"
                output_dir = tmp_path / "output"
                input_dir.mkdir()
                output_dir.mkdir()

                # Write each uploaded file to disk so the subprocess can read them
                file_paths = []
                for f in uploaded_files:
                    # Ensure the file pointer is at the beginning of the file before reading
                    f.seek(0)

                    # Build the path for the file in the tenporary input directory
                    p = input_dir / f.name

                    # Write the bytes of the files to disk
                    p.write_bytes(f.read())

                    # Append the path to the list of file paths
                    file_paths.append(str(p))

                # Launch the classification as a background subprocess
                process = start_classification(
                    output_dir=output_dir,
                    file_paths=file_paths,
                    test_size=test_size,
                    min_samples=min_samples,
                    n_splits=n_splits,
                    seed=seed,
                )

                # Persist process and paths in session state to accomodate reruns
                st.session_state["process"] = process
                st.session_state["tmp_dir"] = tmp_dir
                st.session_state["output_dir"] = output_dir
                st.session_state["running"] = True

                # Rerun the script to trigger the UI update with the running state
                st.rerun()

st.markdown("*Classification algorithm: Sara Behnamian. App: Oliver Todreas*")
