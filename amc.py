#!/usr/bin/env python

import tempfile
import time
from pathlib import Path

import streamlit as st

from src.utils import create_zip_buffer, start_classification, validate_uploaded_files

st.title("Advanced Morphometric Classification")

# If a classification process was started in a previous rerun, resume it
if st.session_state.get("running"):
    # Retrieve the classification process and paths from session state
    process = st.session_state["process"]
    output_dir = st.session_state["output_dir"]
    log_path = output_dir / "run.log.txt"

    # Show status message and cancel button side by side
    col1, col2 = st.columns([4, 1])
    with col1:
        status = st.empty()
    with col2:
        cancel = st.button("Cancel")

    # Show the last 5 lines of run.log.txt on each poll cycle
    st.subheader("Process status...")
    log_container = st.empty()

    def read_log_tail(n=5):
        """Read last n lines of log file if it exists."""
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            return "\n".join(lines[-n:])
        return ""

    # Rerun to return to start page if the cancel button is pressed
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
        st.rerun()

    # Compute elapsed time from session state
    elapsed = int(time.time() - st.session_state.get("start_time", time.time()))
    mins, secs = divmod(elapsed, 60)
    elapsed_str = f"{mins}m {secs:02d}s" if mins else f"{secs}s"

    # If the process is still running (there is no exit code), show the log tail and rerun to poll again
    if process.poll() is None:
        status.info(f"Classification running... {elapsed_str}")
        log_container.code(read_log_tail(), language=None)
        time.sleep(1)
        st.rerun()

    # Process has returned an exit code
    else:
        # Update session state to reflect the process has completed
        st.session_state["running"] = False

        # Assign temp directory from session state for cleanup and result zip download
        tmp_dir = st.session_state["tmp_dir"]

        # Show final log tail
        log_container.code(read_log_tail(), language=None)

        try:
            # If the exit code is non-zero, report the error
            if process.returncode != 0:
                remaining = process.stdout.read() if process.stdout else ""
                status.error(
                    f"Classification failed after {elapsed_str}. See output above for details."
                )
                if remaining:
                    st.code(remaining, language=None)
            else:
                status.success(f"Classification complete in {elapsed_str}")
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

                    # Build the path for the file in the temporary input directory
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

                # Persist process and paths in session state to accommodate reruns
                st.session_state["process"] = process
                st.session_state["tmp_dir"] = tmp_dir
                st.session_state["output_dir"] = output_dir
                st.session_state["running"] = True
                st.session_state["start_time"] = time.time()

                # Rerun the script to trigger the UI update with the running state
                st.rerun()

st.markdown("*Classification algorithm: Sara Behnamian. App: Oliver Todreas*")
