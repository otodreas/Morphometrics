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
            # Write outputs to the ZIP archive
            zf.write(output_file, output_file.relative_to(output_dir))

    # Return the zipped bytes
    return zip_buffer.getvalue()


def start_classification(
    output_dir: Path,
    file_paths: list[str],
    min_samples: int,
    n_splits: int,
    seed: int,
    # Ensemble tuning
    tune_weighted_voting: int = 1,
    voting_top_k_grid: str = "3,4,5,6",
    voting_weight_power_grid: str = "0.5,1.0,2.0",
    cv_folds_grid: str = "5,7,10",
    blend_holdout_grid: str = "0.2,0.3,0.4",
    blend_meta_c_grid: str = "0.1,1.0,10.0",
    # XGBoost / LightGBM / CatBoost
    boost_n_estimators: int = 200,
    boost_max_depth: int = 6,
    boost_learning_rate: float = 0.1,
    # Random Forest / Extra Trees
    rf_n_estimators: int = 300,
    rf_max_depth: int = 0,
    # Gradient Boosting (sklearn)
    gb_n_estimators: int = 150,
    gb_max_depth: int = 5,
    gb_learning_rate: float = 0.1,
    # MLP
    mlp_layers: str = "512,256,128,64",
    mlp_alpha: float = 0.001,
    mlp_max_iter: int = 500,
    # SVM
    svm_c: float = 10.0,
    # Logistic Regression
    lr_c: float = 1.0,
    # KNN
    knn_n_neighbors: int = 5,
    knn_weights: str = "distance",
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
            "--min_samples",
            str(min_samples),
            "--n_splits",
            str(n_splits),
            "--seed",
            str(seed),
            "--tune_weighted_voting",
            str(tune_weighted_voting),
            "--voting_top_k_grid",
            voting_top_k_grid,
            "--voting_weight_power_grid",
            voting_weight_power_grid,
            "--cv_folds_grid",
            cv_folds_grid,
            "--blend_holdout_grid",
            blend_holdout_grid,
            "--blend_meta_c_grid",
            blend_meta_c_grid,
            "--boost_n_estimators",
            str(boost_n_estimators),
            "--boost_max_depth",
            str(boost_max_depth),
            "--boost_learning_rate",
            str(boost_learning_rate),
            "--rf_n_estimators",
            str(rf_n_estimators),
            "--rf_max_depth",
            str(rf_max_depth),
            "--gb_n_estimators",
            str(gb_n_estimators),
            "--gb_max_depth",
            str(gb_max_depth),
            "--gb_learning_rate",
            str(gb_learning_rate),
            "--mlp_layers",
            mlp_layers,
            "--mlp_alpha",
            str(mlp_alpha),
            "--mlp_max_iter",
            str(mlp_max_iter),
            "--svm_c",
            str(svm_c),
            "--lr_c",
            str(lr_c),
            "--knn_n_neighbors",
            str(knn_n_neighbors),
            "--knn_weights",
            knn_weights,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
