#!/usr/bin/env python

import tempfile
import time
from pathlib import Path

import streamlit as st

from src.utils import create_zip_buffer, start_classification, validate_uploaded_files

st.title("🏴‍☠️ CLASSIKA")
st.header(
    "Advanced morphometric classification from Morphologika files using machine learning"
)

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

    # Show the last 10 lines of run.log.txt on each poll cycle
    st.subheader("Process status...")
    log_container = st.empty()

    def read_log_tail(n=10):
        """Read last n lines of log file if it exists."""
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            return "\n".join(lines[-n:])
        return ""

    # Rerun to return to start page if the cancel button is pressed
    if cancel:
        process.terminate()
        try:
            process.wait(timeout=5)
        except Exception:
            process.kill()
        st.session_state["running"] = False
        st.session_state["tmp_dir"].cleanup()
        st.rerun()

    # Compute elapsed time from session state
    elapsed = int(time.time() - st.session_state.get("start_time", time.time()))
    mins, secs = divmod(elapsed, 60)
    elapsed_str = f"{mins}m {secs:02d}s" if mins else f"{secs}s"

    # If the process is still running, show the log tail and rerun to poll again
    if process.poll() is None:
        status.info(f"Classification running... {elapsed_str}")
        log_container.code(read_log_tail(), language=None)
        time.sleep(1)
        st.rerun()

    # Process has returned an exit code
    else:
        st.session_state["running"] = False
        tmp_dir = st.session_state["tmp_dir"]
        log_container.code(read_log_tail(), language=None)

        try:
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
            tmp_dir.cleanup()

    # Stop rendering — prevents form widgets from appearing below
    st.stop()

# Start a fresh classification if none is currently running
else:
    # Data importing
    with st.expander("Data importing", expanded=True):
        uploaded_files = st.file_uploader(
            "Select Morphologika files", type="txt", accept_multiple_files=True
        )

    # General settings
    with st.expander("General settings", expanded=True):
        seed = st.number_input("Random seed", value=42, min_value=0)
        min_samples = st.number_input(
            "Minimum total samples per class", value=3, min_value=1
        )
        n_splits = st.number_input("Number of data splits", value=5, min_value=2)
        st.caption(
            "How many times to split the data into training and testing sets. Higher = more reliable results but slower."
        )

    # Advanced ensemble settings
    with st.expander("Advanced settings"):
        tune_weighted_voting = st.checkbox("Tune weighted voting", value=True)
        st.caption("Automatically search for the best voting weights across models.")

        voting_top_k_grid = st.text_input("Voting top-k grid", value="3,4,5,6")
        st.caption(
            "Number of top models to include in the voting ensemble. Comma-separated list of values to try."
        )

        voting_weight_power_grid = st.text_input(
            "Voting weight power grid", value="0.5,1.0,2.0"
        )
        st.caption(
            "Controls how much higher-scoring models are favoured. Comma-separated list of values to try."
        )

        cv_folds_grid = st.text_input("CV folds grid", value="5,7,10")
        st.caption(
            "Cross-validation folds to try during ensemble tuning. Comma-separated list."
        )

        blend_holdout_grid = st.text_input("Blend holdout grid", value="0.2,0.3,0.4")
        st.caption(
            "Proportion of training data held out for blending meta-learner. Comma-separated list."
        )

        blend_meta_c_grid = st.text_input(
            "Blend meta-learner C grid", value="0.1,1.0,10.0"
        )
        st.caption(
            "Regularisation strength for the blending meta-learner. Comma-separated list."
        )

    # Model-specific settings
    st.subheader("Model-specific settings")

    with st.expander("XGBoost / LightGBM / CatBoost"):
        boost_n_estimators = st.number_input(
            "Number of estimators",
            value=200,
            min_value=10,
            max_value=2000,
            key="boost_n_est",
        )
        boost_max_depth = st.number_input(
            "Max depth", value=6, min_value=1, max_value=20, key="boost_depth"
        )
        boost_learning_rate = st.number_input(
            "Learning rate",
            value=0.1,
            min_value=0.001,
            max_value=1.0,
            step=0.01,
            format="%.3f",
            key="boost_lr",
        )

    with st.expander("Random Forest / Extra Trees"):
        rf_n_estimators = st.number_input(
            "Number of estimators",
            value=300,
            min_value=10,
            max_value=2000,
            key="rf_n_est",
        )
        rf_max_depth = st.number_input(
            "Max depth (0 = unlimited)",
            value=0,
            min_value=0,
            max_value=100,
            key="rf_depth",
        )

    with st.expander("Gradient Boosting (sklearn)"):
        gb_n_estimators = st.number_input(
            "Number of estimators",
            value=150,
            min_value=10,
            max_value=2000,
            key="gb_n_est",
        )
        gb_max_depth = st.number_input(
            "Max depth", value=5, min_value=1, max_value=20, key="gb_depth"
        )
        gb_learning_rate = st.number_input(
            "Learning rate",
            value=0.1,
            min_value=0.001,
            max_value=1.0,
            step=0.01,
            format="%.3f",
            key="gb_lr",
        )

    with st.expander("MLP (Neural Network)"):
        st.caption("Set a layer to 0 to remove it.")
        mlp_l1 = st.number_input(
            "Layer 1 size", value=512, min_value=0, max_value=2048, key="mlp_l1"
        )
        mlp_l2 = st.number_input(
            "Layer 2 size", value=256, min_value=0, max_value=2048, key="mlp_l2"
        )
        mlp_l3 = st.number_input(
            "Layer 3 size", value=128, min_value=0, max_value=2048, key="mlp_l3"
        )
        mlp_l4 = st.number_input(
            "Layer 4 size", value=64, min_value=0, max_value=2048, key="mlp_l4"
        )
        mlp_layers = ",".join(str(x) for x in [mlp_l1, mlp_l2, mlp_l3, mlp_l4])
        mlp_alpha = st.number_input(
            "L2 regularisation (alpha)",
            value=0.001,
            min_value=0.0001,
            max_value=1.0,
            step=0.001,
            format="%.4f",
            key="mlp_alpha",
        )
        mlp_max_iter = st.number_input(
            "Max iterations", value=500, min_value=50, max_value=5000, key="mlp_iter"
        )

    with st.expander("SVM"):
        svm_c = st.number_input(
            "Regularisation parameter (C)",
            value=10.0,
            min_value=0.01,
            max_value=1000.0,
            step=1.0,
            key="svm_c",
        )

    with st.expander("Logistic Regression"):
        lr_c = st.number_input(
            "Regularisation parameter (C)",
            value=1.0,
            min_value=0.001,
            max_value=1000.0,
            step=0.1,
            format="%.3f",
            key="lr_c",
        )

    with st.expander("KNN"):
        knn_n_neighbors = st.number_input(
            "Number of neighbours", value=5, min_value=1, max_value=50, key="knn_k"
        )
        knn_weights = st.selectbox(
            "Weight function", options=["distance", "uniform"], key="knn_weights"
        )

    # Classify button
    if st.button("Classify"):
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
                output_dir = tmp_path / "output"
                input_dir.mkdir()
                output_dir.mkdir()

                file_paths = []
                for f in uploaded_files:
                    f.seek(0)
                    p = input_dir / f.name
                    p.write_bytes(f.read())
                    file_paths.append(str(p))

                process = start_classification(
                    output_dir=output_dir,
                    file_paths=file_paths,
                    min_samples=min_samples,
                    n_splits=n_splits,
                    seed=seed,
                    tune_weighted_voting=int(tune_weighted_voting),
                    voting_top_k_grid=voting_top_k_grid,
                    voting_weight_power_grid=voting_weight_power_grid,
                    cv_folds_grid=cv_folds_grid,
                    blend_holdout_grid=blend_holdout_grid,
                    blend_meta_c_grid=blend_meta_c_grid,
                    boost_n_estimators=boost_n_estimators,
                    boost_max_depth=boost_max_depth,
                    boost_learning_rate=boost_learning_rate,
                    rf_n_estimators=rf_n_estimators,
                    rf_max_depth=rf_max_depth,
                    gb_n_estimators=gb_n_estimators,
                    gb_max_depth=gb_max_depth,
                    gb_learning_rate=gb_learning_rate,
                    mlp_layers=mlp_layers,
                    mlp_alpha=mlp_alpha,
                    mlp_max_iter=mlp_max_iter,
                    svm_c=svm_c,
                    lr_c=lr_c,
                    knn_n_neighbors=knn_n_neighbors,
                    knn_weights=knn_weights,
                )

                st.session_state["process"] = process
                st.session_state["tmp_dir"] = tmp_dir
                st.session_state["output_dir"] = output_dir
                st.session_state["running"] = True
                st.session_state["start_time"] = time.time()

                st.rerun()

st.markdown("*Classification algorithm: Sara Behnamian. App: Oliver Todreas*")
