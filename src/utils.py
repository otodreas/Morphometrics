#!/usr/bin/env python3

import io
import subprocess
import zipfile
from pathlib import Path


def is_morphologika(file: list[str]) -> bool:
    """
    Validate a list of strings representing the lines of a Morphologika file based on header presence.
    Returns True if the file appears to be a valid Morphologika file, False otherwise.
    """

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
        if line.strip().lower() in required_headers.keys():
            # Update dictionary value to True for the corresponding header
            required_headers[line.strip().lower()] = True
            # Break if all required headers have been found
            if all(required_headers.values()):
                return True

    # If not all required headers were found, return False
    print(required_headers)
    return False


def validate_uploaded_files(uploaded_files) -> list[str]:
    """
    Validates a list of Streamlit UploadedFile objects.
    Uses the is_morphologika function to validate each file.
    Returns a list of error messages; empty if all files are valid.
    """
    # Instantiate lists
    errors = []
    file_names = []

    # Loop through items in Streamlit UploadedFile object
    for file in uploaded_files:
        # Update file_names list with the current file's name
        file_names.append(file.name)

        # Attempt to read the file's content and validate it
        try:
            content = file.read().decode("utf-8").splitlines()
            if not is_morphologika(content):
                errors.append(f"{file.name} is not a valid Morphologika file.")
        except UnicodeDecodeError:
            errors.append(
                f"{file.name} could not be read. Please ensure it is UTF-8 encoded."
            )

    # Create list of repeated file names
    repeats = [name for name in file_names if file_names.count(name) > 1]
    if repeats:
        errors.append(
            f"Multiple files with the name ({', '.join(set(repeats))}) detected. "
            "Please give them unique names before uploading."
        )

    # Return the list of errors all at once
    return errors


def create_zip_buffer(output_dir: Path) -> bytes:
    """Returns zipped bytes of all files in output_dir."""
    # Assign a zip buffer in memory to write to
    zip_buffer = io.BytesIO()

    # Open buffer as ZIP archive and write files from the temporary output directory
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        # Loop through all files and directories in the output directory
        for output_file in output_dir.rglob("*"):
            # Only write files to the ZIP archive
            if output_file.is_file():  # TODO: do not return empty catboost directory
                zf.write(output_file, output_file.relative_to(output_dir))

    # Return the zipped bytes
    return zip_buffer.getvalue()


def start_classification(
    output_dir: Path,
    file_paths: list[str],
    test_size: float,
    min_samples: int,
    n_splits: int,
    seed: int,
) -> subprocess.Popen:
    """
    Launches the classification subprocess and returns the process handle.
    Arguments are sourced from the UI, and the subprocess is started with the given arguments.
    """
    return subprocess.Popen(
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
        stderr=subprocess.PIPE,
        text=True,
    )
