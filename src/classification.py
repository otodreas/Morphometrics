#!/usr/bin/env python3
"""
=============================================================================
02_ADVANCED MORPHOMETRIC CLASSIFICATION - STATE-OF-THE-ART TECHNIQUES
=============================================================================
Inspired by Kaggle-winning approaches and latest research:

ADVANCED ENSEMBLES:
- XGBoost, LightGBM, CatBoost (gradient boosting trifecta)
- Stacking with meta-learner
- Blending ensemble
- Weighted voting ensemble
- Multi-layer stacking

ADVANCED OPTIMIZATION:
- Cross-validation with stratification
- Grid search for ensemble tuning

ADVANCED FEATURE ENGINEERING (NO PCA!):
- Pairwise distances (all combinations)
- Interlandmark angles
- Centroid-based features
- Statistical moments (skewness, kurtosis)
- Procrustes-free shape descriptors
- Distance ratios (scale-invariant)
- Bounding box features
- Principal axes (eigenvalues) - NOT PCA, just shape descriptors

FILTERS OUT RARE SPECIES (< 3 samples) including "Unknown"

Author: Sara
Date: 2025

"""

import argparse
import json
import os
import re
import sys
import time
import warnings
from collections import Counter
from datetime import datetime
from itertools import combinations
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyarrow import StructType
from scipy.stats import kurtosis, skew
from sklearn.discriminant_analysis import (
    LinearDiscriminantAnalysis,
    QuadraticDiscriminantAnalysis,
)

# NO PCA - we use comprehensive feature engineering instead!
from sklearn.ensemble import (
    AdaBoostClassifier,
    BaggingClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
    StackingClassifier,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# ML imports
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_predict,
    cross_val_score,
    train_test_split,
)
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, PolynomialFeatures, StandardScaler
from sklearn.svm import SVC

matplotlib.use("Agg")  # Non-interactive backend

warnings.filterwarnings("ignore")


# =============================================================================
# PARSE ARGUMENTS FROM STREAMLIT
# =============================================================================

parser = argparse.ArgumentParser()

parser.add_argument("--output_dir", type=str)
parser.add_argument("--files", nargs="+", type=str)  # list of Path objects
parser.add_argument("--min_samples", type=int)
parser.add_argument("--n_splits", type=int)
parser.add_argument("--seed", type=int, default=None)

# Ensemble tuning settings
parser.add_argument("--tune_weighted_voting", type=int, default=1)  # 1=True, 0=False
parser.add_argument("--voting_top_k_grid", type=str, default="3,4,5,6")
parser.add_argument("--voting_weight_power_grid", type=str, default="0.5,1.0,2.0")
parser.add_argument("--cv_folds_grid", type=str, default="5,7,10")
parser.add_argument("--blend_holdout_grid", type=str, default="0.2,0.3,0.4")
parser.add_argument("--blend_meta_c_grid", type=str, default="0.1,1.0,10.0")

# XGBoost/LightGBM/CatBoost
parser.add_argument("--boost_n_estimators", type=int, default=200)
parser.add_argument("--boost_max_depth", type=int, default=6)
parser.add_argument("--boost_learning_rate", type=float, default=0.1)

# Random Forest/Extra Trees
parser.add_argument("--rf_n_estimators", type=int, default=300)
parser.add_argument("--rf_max_depth", type=int, default=0)  # 0 = None

# Gradient Boosting (sklearn)
parser.add_argument("--gb_n_estimators", type=int, default=150)
parser.add_argument("--gb_max_depth", type=int, default=5)
parser.add_argument("--gb_learning_rate", type=float, default=0.1)

# MLP
parser.add_argument("--mlp_layers", type=str, default="512,256,128,64")
parser.add_argument("--mlp_alpha", type=float, default=0.001)
parser.add_argument("--mlp_max_iter", type=int, default=500)

# SVM
parser.add_argument("--svm_c", type=float, default=10.0)

# Logistic Regression
parser.add_argument("--lr_c", type=float, default=1.0)

# KNN
parser.add_argument("--knn_n_neighbors", type=int, default=5)
parser.add_argument(
    "--knn_weights", type=str, default="distance", choices=["distance", "uniform"]
)

args = parser.parse_args()

# Paths: resolve data relative to project root (parent of scripts/)
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Output directory based on script name (under project root)
# SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
OUTPUT_DIR = args.output_dir
MISC_DIR = os.path.join(OUTPUT_DIR, "misc")

datasets_filepaths = args.files
datasets = []
for f in datasets_filepaths:
    datasets.append(
        (
            Path(f).stem,
            f,
            Path(f).stem,
        )
    )

print(datasets)


# -----------------------------------------------------------------------------
# Logging to both console and file (for live progress tracking)
# -----------------------------------------------------------------------------
def setup_logging():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(MISC_DIR, exist_ok=True)
    log_path = os.path.join(OUTPUT_DIR, "run.log.txt")

    class Tee:
        def __init__(self, *streams):
            self.streams = streams

        def write(self, data):
            for stream in self.streams:
                stream.write(data)
                stream.flush()

        def flush(self):
            for stream in self.streams:
                stream.flush()

    log_file = open(log_path, "w", encoding="utf-8")
    sys.stdout = Tee(sys.__stdout__, log_file)
    sys.stderr = Tee(sys.__stderr__, log_file)
    print(f"[LOG] Writing live log to: {os.path.basename(log_path)}")


setup_logging()

# =============================================================================
# TRY IMPORTING ADVANCED LIBRARIES
# =============================================================================

try:
    import xgboost as xgb

    HAS_XGBOOST = True
    print("[OK] XGBoost available")
except ImportError:
    HAS_XGBOOST = False
    print("[!] XGBoost not installed - pip install xgboost")

try:
    import lightgbm as lgb

    HAS_LIGHTGBM = True
    print("[OK] LightGBM available")
except ImportError:
    HAS_LIGHTGBM = False
    print("[!] LightGBM not installed - pip install lightgbm")

try:
    import catboost as cb

    HAS_CATBOOST = True
    print("[OK] CatBoost available")
except ImportError:
    HAS_CATBOOST = False
    print("[!] CatBoost not installed - pip install catboost")

# Optuna (optional, not currently used but kept for future extensions)
try:
    import optuna
    from optuna.samplers import TPESampler

    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False

# =============================================================================
# SETTINGS
# =============================================================================
RANDOM_STATE = args.seed
TEST_SIZE = (
    0.25  # This is not used anywhere. I left it as is so Sara can find it for later use
)
MIN_SAMPLES = args.min_samples  # Minimum total samples per class
N_SPLITS = args.n_splits  # CV folds (was 10)
TUNE_WEIGHTED_VOTING = bool(args.tune_weighted_voting)
VOTING_TOP_K_GRID = [int(x) for x in args.voting_top_k_grid.split(",")]
VOTING_WEIGHT_POWER_GRID = [float(x) for x in args.voting_weight_power_grid.split(",")]
GLOBAL_TUNE_WEIGHTED_VOTING = True
CV_FOLDS_GRID = [int(x) for x in args.cv_folds_grid.split(",")]
BLEND_HOLDOUT_GRID = [float(x) for x in args.blend_holdout_grid.split(",")]
BLEND_META_C_GRID = [float(x) for x in args.blend_meta_c_grid.split(",")]

np.random.seed(RANDOM_STATE)

# =============================================================================
# DATA LOADING
# =============================================================================


def read_morphologika(filepath):
    """Read Morphologika format file"""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    def find_tag(tag):
        for i, line in enumerate(lines):
            if line.strip().lower() == f"[{tag}]":
                return i
        return None

    i_ind = find_tag("individuals")
    i_lmk = find_tag("landmarks")
    i_dim = find_tag("dimensions")

    n_ind = int(lines[i_ind + 1].strip())
    n_lmk = int(lines[i_lmk + 1].strip())
    n_dim = int(lines[i_dim + 1].strip())

    # Names
    i_names = find_tag("names")
    names = []
    i = i_names + 1
    while len(names) < n_ind and i < len(lines):
        name = lines[i].strip()
        if name and not name.startswith("["):
            names.append(name)
        i += 1

    # Coordinates
    i_raw = find_tag("rawpoints")
    coords = []
    i = i_raw + 1
    while len(coords) < n_ind * n_lmk and i < len(lines):
        line = lines[i].strip()
        if line and not line.startswith("[") and not line.startswith("'"):
            try:
                coord = [float(x) for x in line.split()]
                if len(coord) == n_dim:
                    coords.append(coord)
            except:
                pass
        i += 1

    landmarks = np.array(coords).reshape(n_ind, n_lmk, n_dim)
    return landmarks, names


def get_species(names, dataset_type):
    """Extract species labels"""
    species = []
    for name in names:
        # name_lower = name.lower().strip()

        # if dataset_type == "canids":
        #     # Classify by skull type (long/medium/short) instead of breed group
        #     # We'll derive this from landmark measurements in the analysis function
        #     # For now, keep original name - will be replaced with skull type
        #     sp = name.strip()
        #     if sp == "Non-":
        #         sp = "Non-sporting"
        #     species.append(sp)
        # elif dataset_type == "hominids":
        #     # Classify by GENUS only (not species)
        #     # Extract genus (first word): Gorilla, Pan, Homo
        #     parts = name.split()
        #     if len(parts) >= 1:
        #         genus = parts[0]  # "Gorilla", "Pan", "Homo"
        #         species.append(genus)
        #     else:
        #         species.append(name)
        # elif dataset_type == "papionins":
        #     if "papio" in name_lower:
        #         species.append("Papio")
        #     elif "mandrillus" in name_lower:
        #         species.append("Mandrillus")
        #     elif "macaca" in name_lower:
        #         species.append("Macaca")
        #     elif "lophocebus" in name_lower and "albigena" in name_lower:
        #         species.append("L. albigena")
        #     elif "lophocebus" in name_lower and "aterrimus" in name_lower:
        #         species.append("L. aterrimus")
        #     elif "cercocebus" in name_lower:
        #         species.append("Cercocebus")
        #     else:
        #         species.append(name.split()[0] if name.split() else name)
        # elif dataset_type == "bears":
        #     # Morphologika names are "OTU_ID" e.g. Apennine_160, Scandinavia_42, Kamčatka_xxx
        #     sp = name.split("_")[0] if "_" in name else name.strip()
        #     species.append(sp)
        # elif dataset_type == "quolls":
        #     # Names are "Population_MuseumID" e.g. Groote_NQG0001, mainland_CM01022
        #     sp = name.split("_")[0] if "_" in name else name.strip()
        #     species.append(sp)
        # elif dataset_type == "aariz":
        #     # Names are "CVM-SX_ceph_id" — class is CVM stage (CVM-S1 .. CVM-S6)
        #     sp = name.split("_")[0] if "_" in name else name.strip()
        #     species.append(sp)
        # elif dataset_type == "wolves":
        #     # groups_6: Region_temporal (Scandinavia_before, Finland_after, Fennoscandia_NAN, etc.)
        #     parts = name.split("_")
        #     sp = (
        #         "_".join(parts[:2])
        #         if len(parts) >= 2
        #         else (parts[0] if parts else name.strip())
        #     )
        #     species.append(sp)

        # Assume species names
        parts = re.split(r"[ _]", name)
        label = "_".join(parts[0:2])
        label = label[0].upper() + label[1:]  # capitalise first letter
        species.append(label)
    return np.array(species)


def filter_rare(labels, landmarks):
    """Remove classes with fewer than MIN_SAMPLES samples."""
    counts = Counter(labels)
    rare = [lab for lab, c in counts.items() if c < MIN_SAMPLES]
    if not rare:
        return labels, landmarks, []
    mask = ~np.isin(labels, rare)
    return labels[mask], landmarks[mask], rare


# =============================================================================
# ADVANCED FEATURE ENGINEERING
# =============================================================================


def compute_pairwise_distances(landmarks):
    """All pairwise Euclidean distances between landmarks"""
    n_samples, n_landmarks, _ = landmarks.shape
    n_pairs = n_landmarks * (n_landmarks - 1) // 2
    distances = np.zeros((n_samples, n_pairs))

    for i in range(n_samples):
        idx = 0
        for j in range(n_landmarks):
            for k in range(j + 1, n_landmarks):
                distances[i, idx] = np.linalg.norm(landmarks[i, j] - landmarks[i, k])
                idx += 1
    return distances


def compute_centroid_features(landmarks):
    """Centroid-based shape features"""
    n_samples, n_landmarks, n_dims = landmarks.shape
    features = []

    for i in range(n_samples):
        centroid = np.mean(landmarks[i], axis=0)

        # Distance from each landmark to centroid
        centroid_dists = np.array(
            [np.linalg.norm(landmarks[i, j] - centroid) for j in range(n_landmarks)]
        )

        # Centroid size (Procrustes)
        centroid_size = np.sqrt(np.sum((landmarks[i] - centroid) ** 2))

        # Moments of centroid distances
        feat = [
            centroid_size,
            np.mean(centroid_dists),
            np.std(centroid_dists),
            np.min(centroid_dists),
            np.max(centroid_dists),
            skew(centroid_dists),
            kurtosis(centroid_dists),
        ]
        feat.extend(centroid_dists)  # Individual distances
        features.append(feat)

    return np.array(features)


def compute_angles(landmarks, max_triplets=200):
    """Angles between landmark triplets"""
    n_samples, n_landmarks, _ = landmarks.shape

    triplets = list(combinations(range(n_landmarks), 3))
    if len(triplets) > max_triplets:
        np.random.seed(RANDOM_STATE)
        indices = np.random.choice(len(triplets), max_triplets, replace=False)
        triplets = [triplets[i] for i in indices]

    angles = np.zeros((n_samples, len(triplets)))

    for i in range(n_samples):
        for idx, (a, b, c) in enumerate(triplets):
            v1 = landmarks[i, a] - landmarks[i, b]
            v2 = landmarks[i, c] - landmarks[i, b]
            cos_angle = np.dot(v1, v2) / (
                np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10
            )
            angles[i, idx] = np.arccos(np.clip(cos_angle, -1, 1))

    return angles


def compute_shape_descriptors(landmarks):
    """Advanced shape descriptors"""
    n_samples, n_landmarks, n_dims = landmarks.shape
    features = []

    for i in range(n_samples):
        lm = landmarks[i]
        centroid = np.mean(lm, axis=0)
        centered = lm - centroid

        # Bounding box
        bbox_min = np.min(lm, axis=0)
        bbox_max = np.max(lm, axis=0)
        bbox_dims = bbox_max - bbox_min

        # Principal axes (eigenvalues of covariance)
        cov_matrix = np.cov(centered.T)
        eigenvalues = np.linalg.eigvalsh(cov_matrix)
        eigenvalues = np.sort(eigenvalues)[::-1]  # Descending

        # Shape indices
        total_var = np.sum(eigenvalues)
        if total_var > 0:
            elongation = eigenvalues[0] / total_var
            flatness = eigenvalues[-1] / total_var if len(eigenvalues) > 1 else 0
        else:
            elongation, flatness = 0, 0

        feat = list(bbox_dims)  # n_dims features (2 or 3)
        feat.append(np.prod(bbox_dims))  # Area (2D) or volume (3D)
        feat.append(
            bbox_dims[0] / (bbox_dims[1] + 1e-10)
        )  # Aspect ratio (always valid)
        if n_dims == 3:
            feat.extend(
                [
                    bbox_dims[0] / (bbox_dims[2] + 1e-10),  # XZ
                    bbox_dims[1] / (bbox_dims[2] + 1e-10),  # YZ
                ]
            )
        feat.extend(eigenvalues)  # Principal variances
        feat.extend([elongation, flatness])

        # Statistical moments per axis
        for d in range(n_dims):
            axis_coords = centered[:, d]
            feat.extend([np.var(axis_coords), skew(axis_coords), kurtosis(axis_coords)])

        features.append(feat)

    return np.array(features)


def compute_distance_ratios(landmarks):
    """Ratios between pairs of distances (scale-invariant)"""
    n_samples, n_landmarks, _ = landmarks.shape

    # Select key distance pairs
    n_pairs = min(20, n_landmarks * (n_landmarks - 1) // 4)

    ratios = []
    for i in range(n_samples):
        dists = []
        for j in range(n_landmarks):
            for k in range(j + 1, n_landmarks):
                dists.append(np.linalg.norm(landmarks[i, j] - landmarks[i, k]))

        dists = np.array(dists)
        if len(dists) > n_pairs:
            # Create ratios
            sample_ratios = []
            for p in range(n_pairs):
                d1 = dists[p]
                d2 = dists[-(p + 1)]
                if d2 > 0:
                    sample_ratios.append(d1 / d2)
                else:
                    sample_ratios.append(0)
            ratios.append(sample_ratios)
        else:
            ratios.append([0] * n_pairs)

    return np.array(ratios)


def engineer_all_features(landmarks):
    """Comprehensive feature engineering - NO PCA!"""
    print("  Computing features (NO PCA - comprehensive shape features only)...")
    n_samples, n_landmarks, n_dims = landmarks.shape

    # 1. Raw coordinates
    X_raw = landmarks.reshape(n_samples, -1)
    print(f"    Raw coordinates: {X_raw.shape[1]}")

    # 2. Pairwise distances
    X_dist = compute_pairwise_distances(landmarks)
    print(f"    Pairwise distances: {X_dist.shape[1]}")

    # 3. Centroid features
    X_centroid = compute_centroid_features(landmarks)
    print(f"    Centroid features: {X_centroid.shape[1]}")

    # 4. Angles (always compute - may help with canid data)
    X_angles = compute_angles(landmarks)
    print(f"    Angle features: {X_angles.shape[1]}")

    # 5. Shape descriptors
    X_shape = compute_shape_descriptors(landmarks)
    print(f"    Shape descriptors: {X_shape.shape[1]}")

    # 6. Distance ratios (scale-invariant)
    X_ratios = compute_distance_ratios(landmarks)
    print(f"    Distance ratios: {X_ratios.shape[1]}")

    # Combine all (NO PCA!)
    X_combined = np.hstack([X_raw, X_dist, X_centroid, X_angles, X_shape, X_ratios])

    print(f"    TOTAL FEATURES: {X_combined.shape[1]} (NO PCA - pure shape features)")

    return X_combined


# =============================================================================
# ADVANCED MODELS
# =============================================================================


def get_base_models(n_classes):
    """Get diverse base models for ensemble"""
    models = {}

    # Resolve rf_max_depth: 0 = None (unlimited)
    rf_max_depth = None if args.rf_max_depth == 0 else args.rf_max_depth

    # Parse MLP layers from comma-separated string, filtering out zeros
    mlp_layers = tuple(int(x) for x in args.mlp_layers.split(",") if int(x) > 0)

    # Gradient Boosting variants (XGBoost / LightGBM / CatBoost)
    if HAS_XGBOOST:
        models["XGBoost"] = xgb.XGBClassifier(
            n_estimators=args.boost_n_estimators,
            max_depth=args.boost_max_depth,
            learning_rate=args.boost_learning_rate,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_STATE,
            use_label_encoder=False,
            eval_metric="mlogloss",
            verbosity=0,
        )

    if HAS_LIGHTGBM:
        models["LightGBM"] = lgb.LGBMClassifier(
            n_estimators=args.boost_n_estimators,
            max_depth=args.boost_max_depth,
            learning_rate=args.boost_learning_rate,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_STATE,
            verbose=-1,
            force_col_wise=True,
        )

    if HAS_CATBOOST:
        models["CatBoost"] = cb.CatBoostClassifier(
            iterations=args.boost_n_estimators,
            train_dir=os.path.join(MISC_DIR, "catboost_info"),
            depth=args.boost_max_depth,
            learning_rate=args.boost_learning_rate,
            random_state=RANDOM_STATE,
            verbose=False,
        )

    # Tree-based
    models["RandomForest"] = RandomForestClassifier(
        n_estimators=args.rf_n_estimators,
        max_depth=rf_max_depth,
        min_samples_split=2,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    models["ExtraTrees"] = ExtraTreesClassifier(
        n_estimators=args.rf_n_estimators,
        max_depth=rf_max_depth,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    models["GradientBoosting"] = GradientBoostingClassifier(
        n_estimators=args.gb_n_estimators,
        max_depth=args.gb_max_depth,
        learning_rate=args.gb_learning_rate,
        random_state=RANDOM_STATE,
    )

    # Linear models
    models["LogisticRegression"] = LogisticRegression(
        C=args.lr_c, max_iter=2000, random_state=RANDOM_STATE, n_jobs=-1
    )

    if n_classes > 2:
        models["LDA"] = LinearDiscriminantAnalysis()

    # SVM
    models["SVM_RBF"] = SVC(
        kernel="rbf",
        C=args.svm_c,
        gamma="scale",
        probability=True,
        random_state=RANDOM_STATE,
    )

    # Neural Network
    models["MLP"] = MLPClassifier(
        hidden_layer_sizes=mlp_layers,
        activation="relu",
        solver="adam",
        alpha=args.mlp_alpha,
        batch_size=32,
        learning_rate_init=0.001,
        max_iter=args.mlp_max_iter,
        random_state=RANDOM_STATE,
        early_stopping=True,
        validation_fraction=0.15,
    )

    # KNN
    models["KNN"] = KNeighborsClassifier(
        n_neighbors=args.knn_n_neighbors, weights=args.knn_weights, n_jobs=-1
    )

    return models


# =============================================================================
# STACKING ENSEMBLE
# =============================================================================


def create_stacking_ensemble(n_classes):
    """Create multi-layer stacking ensemble"""

    # Level 0: Diverse base learners
    base_estimators = []

    if HAS_XGBOOST:
        base_estimators.append(
            (
                "xgb",
                xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=RANDOM_STATE,
                    verbosity=0,
                    use_label_encoder=False,
                ),
            )
        )

    if HAS_LIGHTGBM:
        base_estimators.append(
            (
                "lgb",
                lgb.LGBMClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=RANDOM_STATE,
                    verbose=-1,
                ),
            )
        )

    if HAS_CATBOOST:
        base_estimators.append(
            (
                "cb",
                cb.CatBoostClassifier(
                    iterations=100,
                    train_dir=os.path.join(MISC_DIR, "catboost_info"),
                    depth=5,
                    learning_rate=0.1,
                    random_state=RANDOM_STATE,
                    verbose=False,
                ),
            )
        )

    base_estimators.extend(
        [
            (
                "rf",
                RandomForestClassifier(
                    n_estimators=150, random_state=RANDOM_STATE, n_jobs=-1
                ),
            ),
            (
                "et",
                ExtraTreesClassifier(
                    n_estimators=150, random_state=RANDOM_STATE, n_jobs=-1
                ),
            ),
            (
                "svm",
                SVC(kernel="rbf", C=10, probability=True, random_state=RANDOM_STATE),
            ),
            (
                "mlp",
                MLPClassifier(
                    hidden_layer_sizes=(256, 128),
                    max_iter=300,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    # Meta-learner: Random Forest (robust to overfitting)
    meta_learner = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=RANDOM_STATE, n_jobs=-1
    )

    stacking = StackingClassifier(
        estimators=base_estimators,
        final_estimator=meta_learner,
        cv=5,
        stack_method="predict_proba",
        n_jobs=-1,
        passthrough=True,  # Include original features
    )

    return stacking


# =============================================================================
# BLENDING ENSEMBLE
# =============================================================================


def create_blending_ensemble(
    X_train, y_train, X_test, n_classes, blend_holdout=0.3, meta_C=1.0
):
    """Manual blending ensemble with holdout"""

    # Split training into blend_train and blend_holdout
    X_blend_train, X_blend_hold, y_blend_train, y_blend_hold = train_test_split(
        X_train,
        y_train,
        test_size=blend_holdout,
        random_state=RANDOM_STATE,
        stratify=y_train,
    )

    # Get base models
    models = get_base_models(n_classes)

    # Train base models and get predictions on holdout
    blend_train_preds = np.zeros((len(y_blend_hold), len(models) * n_classes))
    blend_test_preds = np.zeros((len(X_test), len(models) * n_classes))

    scaler = StandardScaler()
    X_blend_train_s = scaler.fit_transform(X_blend_train)
    X_blend_hold_s = scaler.transform(X_blend_hold)
    X_test_s = scaler.transform(X_test)

    col_idx = 0
    for name, model in models.items():
        try:
            model.fit(X_blend_train_s, y_blend_train)

            # Predictions on holdout (for meta-learner training)
            if hasattr(model, "predict_proba"):
                preds_hold = model.predict_proba(X_blend_hold_s)
                preds_test = model.predict_proba(X_test_s)
            else:
                preds_hold = np.eye(n_classes)[model.predict(X_blend_hold_s)]
                preds_test = np.eye(n_classes)[model.predict(X_test_s)]

            blend_train_preds[:, col_idx : col_idx + n_classes] = preds_hold
            blend_test_preds[:, col_idx : col_idx + n_classes] = preds_test
            col_idx += n_classes

        except Exception as e:
            print(f"    [!] Blending error with {name}: {e}")
            col_idx += n_classes

    # Train meta-learner on holdout predictions
    meta_learner = LogisticRegression(
        max_iter=1000, C=meta_C, random_state=RANDOM_STATE
    )
    meta_learner.fit(blend_train_preds, y_blend_hold)

    # Final predictions
    y_pred = meta_learner.predict(blend_test_preds)

    return y_pred


# =============================================================================
# WEIGHTED VOTING ENSEMBLE
# =============================================================================


def create_weighted_voting(X_train, y_train, n_classes):
    """Create voting ensemble with optimized weights"""

    models = get_base_models(n_classes)
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    # Get CV scores for each model to determine weights
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)

    model_scores = {}
    for name, model in models.items():
        try:
            scores = cross_val_score(
                model, X_train_s, y_train, cv=cv, scoring="accuracy", n_jobs=-1
            )
            model_scores[name] = scores.mean()
        except:
            model_scores[name] = 0

    # Select top models and compute weights
    sorted_models = sorted(model_scores.items(), key=lambda x: -x[1])
    top_models = sorted_models[:6]  # Top 6 models

    # Weights proportional to accuracy
    total_score = sum([s for _, s in top_models])
    if total_score > 0:
        weights = [s / total_score for _, s in top_models]
    else:
        weights = [1.0 / max(len(top_models), 1) for _ in top_models]

    estimators = [(name, models[name]) for name, _ in top_models]

    voting = VotingClassifier(
        estimators=estimators, voting="soft", weights=weights, n_jobs=-1
    )

    return voting, dict(top_models)


def create_weighted_voting_with_params(
    n_classes, model_scores, top_k=6, weight_power=1.0
):
    """Create voting ensemble from precomputed scores and params."""
    models = get_base_models(n_classes)
    sorted_models = sorted(model_scores.items(), key=lambda x: -x[1])
    top_models = sorted_models[:top_k]

    scores = [max(s, 0) for _, s in top_models]
    if weight_power != 1.0:
        scores = [s**weight_power for s in scores]
    total_score = sum(scores)
    if total_score > 0:
        weights = [s / total_score for s in scores]
    else:
        weights = [1.0 / max(len(top_models), 1) for _ in top_models]

    estimators = [(name, models[name]) for name, _ in top_models]
    voting = VotingClassifier(
        estimators=estimators, voting="soft", weights=weights, n_jobs=-1
    )
    return voting, [name for name, _ in top_models], weights


def compute_model_scores_cv(X, y, n_classes, cv_splits=None):
    """Compute mean CV accuracy per model with scaling."""
    if cv_splits is None:
        cv_splits = N_SPLITS
    models = get_base_models(n_classes)
    skf = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=RANDOM_STATE)
    model_scores = {}
    for name, model in models.items():
        try:
            pipe = Pipeline([("scaler", StandardScaler()), ("model", model)])
            scores = cross_val_score(pipe, X, y, cv=skf, scoring="accuracy", n_jobs=-1)
            model_scores[name] = scores.mean()
        except Exception:
            model_scores[name] = 0
    return model_scores


def tune_weighted_voting_params(X, y, n_classes):
    """Tune top_k and weight_power for weighted voting using CV."""
    model_scores = compute_model_scores_cv(X, y, n_classes, cv_splits=N_SPLITS)
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    best = {
        "top_k": None,
        "weight_power": None,
        "cv_accuracy": -1,
        "model_scores": model_scores,
    }

    for top_k in VOTING_TOP_K_GRID:
        for weight_power in VOTING_WEIGHT_POWER_GRID:
            voting, top_models, weights = create_weighted_voting_with_params(
                n_classes, model_scores, top_k=top_k, weight_power=weight_power
            )
            pipe = Pipeline([("scaler", StandardScaler()), ("model", voting)])
            try:
                scores = cross_val_score(
                    pipe, X, y, cv=skf, scoring="accuracy", n_jobs=-1
                )
                avg = scores.mean()
            except Exception:
                avg = -1
            if avg > best["cv_accuracy"]:
                best.update(
                    {
                        "top_k": top_k,
                        "weight_power": weight_power,
                        "cv_accuracy": avg,
                        "top_models": top_models,
                        "weights": weights,
                    }
                )

    return best


def tune_global_weighted_voting(datasets):
    """Tune one global weighted voting config across all datasets."""
    dataset_cache = []
    for name, path, dtype in datasets:
        if not os.path.exists(path):
            continue
        landmarks, specimen_names = read_morphologika(path)
        labels = get_species(specimen_names, dtype)
        if dtype == "canids":
            labels = classify_canids_by_type(landmarks, specimen_names)
        labels, landmarks, _ = filter_rare(labels, landmarks)
        if len(np.unique(labels)) < 2:
            continue
        X = engineer_all_features(landmarks)
        le = LabelEncoder()
        y = le.fit_transform(labels)
        dataset_cache.append((name, X, y, len(le.classes_)))

    if not dataset_cache:
        return None

    best = {
        "top_k": None,
        "weight_power": None,
        "cv_accuracy": -1,
        "cv_folds": None,
        "model_scores": None,
    }

    for cv_folds in CV_FOLDS_GRID:
        # Average model scores across datasets for this CV setting
        score_sums = None
        for _, X, y, n_classes in dataset_cache:
            scores = compute_model_scores_cv(X, y, n_classes, cv_splits=cv_folds)
            if score_sums is None:
                score_sums = {k: v for k, v in scores.items()}
            else:
                for k, v in scores.items():
                    score_sums[k] = score_sums.get(k, 0) + v
        global_scores = {k: v / len(dataset_cache) for k, v in score_sums.items()}

        for top_k in VOTING_TOP_K_GRID:
            for weight_power in VOTING_WEIGHT_POWER_GRID:
                per_dataset_scores = []
                for _, X, y, n_classes in dataset_cache:
                    voting, _, _ = create_weighted_voting_with_params(
                        n_classes, global_scores, top_k=top_k, weight_power=weight_power
                    )
                    pipe = Pipeline([("scaler", StandardScaler()), ("model", voting)])
                    skf = StratifiedKFold(
                        n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE
                    )
                    try:
                        scores = cross_val_score(
                            pipe, X, y, cv=skf, scoring="accuracy", n_jobs=-1
                        )
                        per_dataset_scores.append(scores.mean())
                    except Exception:
                        per_dataset_scores.append(0)
                avg = float(np.mean(per_dataset_scores)) if per_dataset_scores else -1
                if avg > best["cv_accuracy"]:
                    voting, top_models, weights = create_weighted_voting_with_params(
                        dataset_cache[0][3],
                        global_scores,
                        top_k=top_k,
                        weight_power=weight_power,
                    )
                    best.update(
                        {
                            "top_k": top_k,
                            "weight_power": weight_power,
                            "cv_accuracy": avg,
                            "cv_folds": cv_folds,
                            "model_scores": global_scores,
                            "top_models": top_models,
                            "weights": weights,
                        }
                    )

    return best


def tune_global_blending(datasets):
    """Tune blending params across all datasets."""
    dataset_cache = []
    for name, path, dtype in datasets:
        if not os.path.exists(path):
            continue
        landmarks, specimen_names = read_morphologika(path)
        labels = get_species(specimen_names, dtype)
        if dtype == "canids":
            labels = classify_canids_by_type(landmarks, specimen_names)
        labels, landmarks, _ = filter_rare(labels, landmarks)
        if len(np.unique(labels)) < 2:
            continue
        X = engineer_all_features(landmarks)
        le = LabelEncoder()
        y = le.fit_transform(labels)
        dataset_cache.append((name, X, y, len(le.classes_)))

    if not dataset_cache:
        return None

    best = {
        "blend_holdout": None,
        "meta_C": None,
        "cv_accuracy": -1,
        "cv_folds": None,
    }

    for cv_folds in CV_FOLDS_GRID:
        for blend_holdout in BLEND_HOLDOUT_GRID:
            for meta_C in BLEND_META_C_GRID:
                per_dataset_scores = []
                for _, X, y, n_classes in dataset_cache:
                    skf = StratifiedKFold(
                        n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE
                    )
                    fold_scores = []
                    for train_idx, test_idx in skf.split(X, y):
                        X_train, X_test = X[train_idx], X[test_idx]
                        y_train, y_test = y[train_idx], y[test_idx]
                        scaler = StandardScaler()
                        X_train_s = scaler.fit_transform(X_train)
                        X_test_s = scaler.transform(X_test)
                        try:
                            y_pred = create_blending_ensemble(
                                X_train_s,
                                y_train,
                                X_test_s,
                                n_classes,
                                blend_holdout=blend_holdout,
                                meta_C=meta_C,
                            )
                            fold_scores.append(accuracy_score(y_test, y_pred))
                        except Exception:
                            fold_scores.append(0)
                    per_dataset_scores.append(
                        float(np.mean(fold_scores)) if fold_scores else 0
                    )
                avg = float(np.mean(per_dataset_scores)) if per_dataset_scores else -1
                if avg > best["cv_accuracy"]:
                    best.update(
                        {
                            "blend_holdout": blend_holdout,
                            "meta_C": meta_C,
                            "cv_accuracy": avg,
                            "cv_folds": cv_folds,
                        }
                    )

    return best


def build_confusion_matrix_for_model(
    dataset_name, filepath, dataset_type, model_name, output_dir, best_model_params=None
):
    """Build confusion matrix using stratified K-fold CV on full dataset.
    Every specimen gets predicted exactly once (like Mohseni et al. Table 1)."""
    if not os.path.exists(filepath):
        print(f"  [SKIP] Missing file for confusion matrix: {filepath}")
        return None

    landmarks, specimen_names = read_morphologika(filepath)
    labels = get_species(specimen_names, dataset_type)
    if dataset_type == "canids":
        labels = classify_canids_by_type(landmarks, specimen_names)
    labels, landmarks, _ = filter_rare(labels, landmarks)
    if len(np.unique(labels)) < 2:
        print(f"  [SKIP] {dataset_name}: <2 classes after filtering")
        return None

    X = engineer_all_features(landmarks)
    le = LabelEncoder()
    y = le.fit_transform(labels)
    n_classes = len(le.classes_)

    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    y_pred = None
    try:
        if model_name == "Blending":
            # Manual CV for Blending (does its own internal split)
            blend_holdout = 0.3
            meta_C = 1.0
            if best_model_params:
                blend_holdout = best_model_params.get("blend_holdout", blend_holdout)
                meta_C = best_model_params.get("meta_C", meta_C)

            y_pred = np.zeros(len(y), dtype=int)
            for train_idx, test_idx in skf.split(X, y):
                X_train, X_test = X[train_idx], X[test_idx]
                y_train = y[train_idx]
                scaler = StandardScaler()
                X_train_s = scaler.fit_transform(X_train)
                X_test_s = scaler.transform(X_test)
                fold_pred = create_blending_ensemble(
                    X_train_s,
                    y_train,
                    X_test_s,
                    n_classes,
                    blend_holdout=blend_holdout,
                    meta_C=meta_C,
                )
                y_pred[test_idx] = fold_pred

        elif model_name == "Weighted Voting":
            voting_params = None
            if best_model_params and best_model_params.get("model_scores"):
                voting_params = best_model_params
            if voting_params:
                model, _, _ = create_weighted_voting_with_params(
                    n_classes,
                    voting_params["model_scores"],
                    top_k=voting_params["top_k"],
                    weight_power=voting_params["weight_power"],
                )
            else:
                scaler_tmp = StandardScaler()
                X_s_tmp = scaler_tmp.fit_transform(X)
                model, _ = create_weighted_voting(X_s_tmp, y, n_classes)
            pipe = Pipeline([("scaler", StandardScaler()), ("model", model)])
            y_pred = cross_val_predict(pipe, X, y, cv=skf, n_jobs=-1)

        elif model_name == "Stacking Ensemble":
            model = create_stacking_ensemble(n_classes)
            pipe = Pipeline([("scaler", StandardScaler()), ("model", model)])
            y_pred = cross_val_predict(pipe, X, y, cv=skf, n_jobs=-1)

        else:
            base_models = get_base_models(n_classes)
            model = base_models.get(model_name)
            if model is None:
                print(f"  [WARN] Unknown model for confusion matrix: {model_name}")
                return None
            pipe = Pipeline([("scaler", StandardScaler()), ("model", model)])
            y_pred = cross_val_predict(pipe, X, y, cv=skf, n_jobs=-1)

    except Exception as exc:
        print(f"  [WARN] Confusion matrix failed for {dataset_name}: {exc}")
        return None

    cm = confusion_matrix(y, y_pred, labels=np.arange(n_classes))

    # Plot confusion matrix
    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues", aspect="auto")

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(
        "Number of Samples", rotation=270, labelpad=20, fontsize=12, fontweight="bold"
    )

    # Set ticks and labels
    tick_marks = np.arange(n_classes)
    class_names = [sp.replace(" ", "\n") for sp in le.classes_]
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(
        class_names, fontsize=10, fontweight="bold", rotation=45, ha="right"
    )
    ax.set_yticklabels(class_names, fontsize=10, fontweight="bold")

    # Add labels
    ax.set_xlabel("Predicted Species", fontsize=13, fontweight="bold", labelpad=15)
    ax.set_ylabel("True Species", fontsize=13, fontweight="bold", labelpad=15)

    # Add text annotations with accuracy percentages
    thresh = cm.max() / 2.0
    for i in range(n_classes):
        for j in range(n_classes):
            text_color = "white" if cm[i, j] > thresh else "black"
            if i == j:
                text_color = "white"
                fontweight = "bold"
                fontsize = 12
                if cm[i, :].sum() > 0:
                    acc_pct = (cm[i, j] / cm[i, :].sum()) * 100
                    text = f"{cm[i, j]}\n({acc_pct:.1f}%)"
                else:
                    text = format(cm[i, j], "d")
            else:
                fontweight = "normal"
                fontsize = 10
                text = format(cm[i, j], "d")
            ax.text(
                j,
                i,
                text,
                horizontalalignment="center",
                verticalalignment="center",
                color=text_color,
                fontweight=fontweight,
                fontsize=fontsize,
            )

    acc = accuracy_score(y, y_pred) * 100
    plt.title(
        f"Confusion Matrix - Best Overall ({model_name})\n"
        f"{dataset_name} Dataset ({N_SPLITS}-fold CV, all specimens)\n"
        f"Accuracy: {acc:.2f}%",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    plt.tight_layout()

    cm_filename = os.path.join(
        output_dir, f"{dataset_name}_Confusion_Matrix_Best_Overall.png"
    )
    plt.savefig(cm_filename, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"    [OK] Confusion matrix saved: {os.path.basename(cm_filename)}")
    print(
        f"    [OK] Overall Accuracy: {acc:.2f}% ({N_SPLITS}-fold CV, {len(y)} specimens)"
    )

    return {"dataset": dataset_name, "matrix": cm, "labels": le.classes_}


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================


def classify_canids_by_type(landmarks, specimen_names):
    """
    Advanced Canids classification:
    1. First separate: Wild (FOX, NATURAL/wolves) vs Domestic dogs
    2. For domestic dogs: Use morphological traits (Nose, Cephalic type, UKC standard)
    """
    import pandas as pd

    n_samples = len(specimen_names)
    classifications = []

    # Load classifier sheet for wild vs domestic and morphological traits
    classifier_path = "Canids/Data/Classifier_sheet.csv"
    breed_path = "Canids/Data/Breed_list.csv"

    # Create lookup dictionaries
    classifier_dict = {}
    breed_dict = {}

    if os.path.exists(classifier_path):
        try:
            classifier_df = pd.read_csv(classifier_path)
            for _, row in classifier_df.iterrows():
                inst = str(row["Institution"]).strip()
                spec = str(row["Specimen"]).strip()
                key = f"{inst}_{spec}"
                classifier_dict[key] = {
                    "nose": str(row.get("Nose", "")).strip()
                    if pd.notna(row.get("Nose"))
                    else "",
                    "bitework": str(row.get("Bitework", "")).strip()
                    if pd.notna(row.get("Bitework"))
                    else "",
                    "ukc": str(row.get("UKC breeding Standard", "")).strip()
                    if pd.notna(row.get("UKC breeding Standard"))
                    else "",
                    "akc": str(row.get("AKC breeding standard", "")).strip()
                    if pd.notna(row.get("AKC breeding standard"))
                    else "",
                }
            print(f"    Loaded {len(classifier_dict)} entries from classifier sheet")
        except Exception as e:
            print(f"    Warning: Could not load classifier sheet: {e}")

    if os.path.exists(breed_path):
        try:
            breed_df = pd.read_csv(breed_path)
            for _, row in breed_df.iterrows():
                inst = str(row["Institution"]).strip()
                spec = str(row["Specimen"]).strip()
                key = f"{inst}_{spec}"
                breed_dict[key] = (
                    str(row.get("Breed", "")).strip()
                    if pd.notna(row.get("Breed"))
                    else ""
                )
            print(f"    Loaded {len(breed_dict)} entries from breed list")
        except Exception as e:
            print(f"    Warning: Could not load breed list: {e}")

    # Calculate cephalic indices (skull length/width ratio) from landmarks
    cephalic_indices = []
    for i in range(n_samples):
        lm = landmarks[i]
        # Calculate length (anterior-posterior, X-axis) and width (lateral, Y-axis)
        length = np.max(lm[:, 0]) - np.min(lm[:, 0])  # X-axis extent
        width = np.max(lm[:, 1]) - np.min(lm[:, 1])  # Y-axis extent
        if width > 0:
            cephalic_index = length / width
        else:
            cephalic_index = 1.0  # Default
        cephalic_indices.append(cephalic_index)

    cephalic_indices = np.array(cephalic_indices)

    # Classify cephalic types based on ratios
    # Dolichocephalic: CI > 1.5 (long narrow skull)
    # Mesocephalic: 1.2 < CI <= 1.5 (medium)
    # Brachycephalic: CI <= 1.2 (short wide skull)
    p33 = np.percentile(cephalic_indices, 33.33)
    p66 = np.percentile(cephalic_indices, 66.67)

    print(f"    Cephalic index percentiles: 33rd={p33:.2f}, 67th={p66:.2f}")

    # Process each specimen
    for i, name in enumerate(specimen_names):
        name_str = str(name).strip()

        # Try to extract Institution_Code from name
        inst_code = None
        parts = name_str.split()
        for part in parts:
            if "_" in part and len(part.split("_")) == 2:
                inst_code = part
                break

        # Check if wild canid (FOX or NATURAL/wolves)
        is_wild = False
        wild_type = None

        if inst_code and inst_code in classifier_dict:
            akc = classifier_dict[inst_code].get("akc", "").upper()
            ukc = classifier_dict[inst_code].get("ukc", "").upper()

            if akc in ["FOX", "NATURAL"] or ukc in ["FOX", "NATURAL"]:
                is_wild = True
                if "FOX" in akc or "FOX" in ukc:
                    wild_type = "Fox"
                else:
                    wild_type = "Wolf"  # NATURAL = wolves

        if is_wild:
            classifications.append(wild_type)
        else:
            # Domestic dog - use morphological classification
            nose = None
            bitework = None
            ukc_std = None
            cephalic_type = None

            if inst_code and inst_code in classifier_dict:
                nose = classifier_dict[inst_code].get("nose", "").upper()
                bitework = classifier_dict[inst_code].get("bitework", "").upper()
                ukc_std = classifier_dict[inst_code].get("ukc", "").strip()

            # Determine cephalic type
            ci = cephalic_indices[i]
            if ci > 1.5:
                cephalic_type = "Dolichocephalic"
            elif ci > 1.2:
                cephalic_type = "Mesocephalic"
            else:
                cephalic_type = "Brachycephalic"

            # Classification strategy: Combine multiple traits
            if nose and nose in ["YES", "NO"]:
                # Use Nose + Cephalic type
                if nose == "YES":
                    if cephalic_type == "Dolichocephalic":
                        classifications.append("Long_Nose_Dolichocephalic")
                    elif cephalic_type == "Mesocephalic":
                        classifications.append("Long_Nose_Mesocephalic")
                    else:
                        classifications.append("Long_Nose_Brachycephalic")
                else:  # NO
                    if cephalic_type == "Brachycephalic":
                        classifications.append("Short_Nose_Brachycephalic")
                    elif cephalic_type == "Mesocephalic":
                        classifications.append("Short_Nose_Mesocephalic")
                    else:
                        classifications.append("Short_Nose_Dolichocephalic")
            elif ukc_std and ukc_std not in ["NATURAL", "FOX", ""]:
                # Use UKC standard (more biologically meaningful)
                # Clean up UKC standard name
                ukc_clean = ukc_std.replace(" ", "_").replace("-", "_")
                classifications.append(f"UKC_{ukc_clean}")
            elif bitework and bitework in ["YES", "NO"]:
                # Use Bitework + Cephalic type
                if bitework == "YES":
                    classifications.append(f"Bitework_{cephalic_type}")
                else:
                    classifications.append(f"No_Bitework_{cephalic_type}")
            else:
                # Fallback: Use cephalic type only
                classifications.append(cephalic_type)

    return np.array(classifications)


def analyze_dataset(name, filepath, dataset_type, output_dir):
    """Full advanced analysis of one dataset"""
    print(f"\n{'=' * 70}")
    print(f"  {name.upper()} - ADVANCED ANALYSIS")
    print(f"{'=' * 70}")

    if not os.path.exists(filepath):
        print(f"  ERROR: File not found: {filepath}")
        return None

    # Load data (all datasets: raw landmarks via Morphologika for consistency)
    landmarks, specimen_names = read_morphologika(filepath)
    species = get_species(specimen_names, dataset_type)

    # For Canids: Advanced classification (Wild vs Domestic)
    if dataset_type == "canids":
        print(f"\n  [CANIDS] Advanced classification:")
        print(f"    - Separate Wild (Fox/Wolf) from Domestic dogs")
        print(f"    - For domestic dogs, use morphological traits:")
        print(f"      * Nose type (Yes/No) + Cephalic type")
        print(f"      * UKC standard (more biologically meaningful)")
        print(f"      * Bitework + Cephalic type")
        species = classify_canids_by_type(landmarks, specimen_names)
        print(f"  Classification distribution:")
        for st, c in sorted(Counter(species).items(), key=lambda x: -x[1]):
            print(f"    {st}: {c}")

    print(f"\n  Loaded: {len(species)} specimens, {landmarks.shape[1]} landmarks")

    # Filter rare species (including "Unknown" and others with < 3 samples)
    counts = Counter(species)
    rare = [sp for sp, c in counts.items() if c < MIN_SAMPLES]
    if rare:
        print(
            f"\n  [FILTERING] Removing {len(rare)} rare species (< {MIN_SAMPLES} samples):"
        )
        for sp in rare:
            print(f"    - {sp}: {counts[sp]} samples (OUTLIER - will be excluded)")
        mask = ~np.isin(species, rare)
        landmarks = landmarks[mask]
        species = species[mask]
        print(f"  After filtering: {len(species)} specimens remaining")

    # Species distribution
    print(f"\n  Species distribution ({len(set(species))} classes):")
    for sp, c in sorted(Counter(species).items(), key=lambda x: -x[1]):
        print(f"    {sp}: {c}")

    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(species)
    n_classes = len(le.classes_)

    # Feature engineering (NO PCA!)
    print(f"\n  Feature Engineering (NO PCA - comprehensive shape features only):")
    X = engineer_all_features(landmarks)

    # Optional tuning for weighted voting on full dataset
    tuned_weighted_voting = None
    if TUNE_WEIGHTED_VOTING:
        print(f"\n  [TUNING] Weighted Voting (CV on full dataset):")
        tuned_weighted_voting = tune_weighted_voting_params(X, y, n_classes)
        print(
            f"    Best params: top_k={tuned_weighted_voting['top_k']}, "
            f"weight_power={tuned_weighted_voting['weight_power']}, "
            f"cv_accuracy={tuned_weighted_voting['cv_accuracy']:.4f}"
        )

    # =========================================================================
    # EVALUATE ALL METHODS - STRATIFIED K-FOLD CV ON FULL DATASET
    # (Like Mohseni et al. Table 1: every specimen predicted exactly once)
    # =========================================================================
    results = {}
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    # 1. Individual models (use cross_val_predict - every sample predicted once)
    print(f"\n  [1] INDIVIDUAL MODELS ({N_SPLITS}-fold stratified CV on full dataset):")
    print("  " + "-" * 50)
    models = get_base_models(n_classes)

    for model_name, model in models.items():
        try:
            start = time.time()
            pipe = Pipeline([("scaler", StandardScaler()), ("model", model)])
            y_pred_cv = cross_val_predict(pipe, X, y, cv=skf, n_jobs=-1)
            acc = accuracy_score(y, y_pred_cv)
            elapsed = time.time() - start
            results[model_name] = acc
            print(f"    {model_name:<20}: {acc:.4f} ({elapsed:.1f}s)")
        except Exception as e:
            print(f"    {model_name:<20}: ERROR - {str(e)[:50]}")

    # 2. Stacking Ensemble
    print(f"\n  [2] STACKING ENSEMBLE ({N_SPLITS}-fold CV):")
    print("  " + "-" * 50)
    try:
        start = time.time()
        stacking = create_stacking_ensemble(n_classes)
        pipe = Pipeline([("scaler", StandardScaler()), ("model", stacking)])
        y_pred_cv = cross_val_predict(pipe, X, y, cv=skf, n_jobs=-1)
        acc_stack = accuracy_score(y, y_pred_cv)
        elapsed = time.time() - start
        results["Stacking Ensemble"] = acc_stack
        print(f"    Stacking: {acc_stack:.4f} ({elapsed:.1f}s)")
    except Exception as e:
        print(f"    Stacking: ERROR - {e}")

    # 3. Weighted Voting
    print(f"\n  [3] WEIGHTED VOTING ENSEMBLE ({N_SPLITS}-fold CV):")
    print("  " + "-" * 50)
    try:
        start = time.time()
        voting_params = None
        if tuned_weighted_voting and tuned_weighted_voting.get("model_scores"):
            voting_params = tuned_weighted_voting

        if voting_params:
            voting, top_models, weights = create_weighted_voting_with_params(
                n_classes,
                voting_params["model_scores"],
                top_k=voting_params["top_k"],
                weight_power=voting_params["weight_power"],
            )
            model_weights = dict(zip(top_models, weights))
        else:
            # Need a quick CV to get scores for weighting
            scaler_tmp = StandardScaler()
            X_s_tmp = scaler_tmp.fit_transform(X)
            voting, model_weights = create_weighted_voting(X_s_tmp, y, n_classes)

        pipe = Pipeline([("scaler", StandardScaler()), ("model", voting)])
        y_pred_cv = cross_val_predict(pipe, X, y, cv=skf, n_jobs=-1)
        acc_vote = accuracy_score(y, y_pred_cv)
        elapsed = time.time() - start
        results["Weighted Voting"] = acc_vote
        print(f"    Weighted Voting: {acc_vote:.4f} ({elapsed:.1f}s)")
        if voting_params:
            print(f"    Model weights: {model_weights}")
    except Exception as e:
        print(f"    Weighted Voting: ERROR - {e}")

    # 4. Blending (manual CV - can't use cross_val_predict since blending
    #    does its own internal train/holdout split)
    print(f"\n  [4] BLENDING ENSEMBLE ({N_SPLITS}-fold CV):")
    print("  " + "-" * 50)
    try:
        start = time.time()
        y_pred_blend_cv = np.zeros(len(y), dtype=int)
        for train_idx, test_idx in skf.split(X, y):
            X_train_fold, X_test_fold = X[train_idx], X[test_idx]
            y_train_fold, y_test_fold = y[train_idx], y[test_idx]
            scaler_fold = StandardScaler()
            X_train_fold_s = scaler_fold.fit_transform(X_train_fold)
            X_test_fold_s = scaler_fold.transform(X_test_fold)
            fold_pred = create_blending_ensemble(
                X_train_fold_s, y_train_fold, X_test_fold_s, n_classes
            )
            y_pred_blend_cv[test_idx] = fold_pred
        acc_blend = accuracy_score(y, y_pred_blend_cv)
        elapsed = time.time() - start
        results["Blending"] = acc_blend
        print(f"    Blending: {acc_blend:.4f} ({elapsed:.1f}s)")
    except Exception as e:
        print(f"    Blending: ERROR - {e}")

    print(
        f"\n  Evaluation: {N_SPLITS}-fold stratified CV on full dataset (all specimens)"
    )
    print(f"  (Like Mohseni et al. Table 1 - every specimen predicted exactly once)\n")

    print(f"\n  {'=' * 50}")
    print(f"  RESULTS SUMMARY - {name} ({N_SPLITS}-fold CV)")
    print(f"  {'=' * 50}")

    sorted_results = sorted(results.items(), key=lambda x: -x[1])

    print(f"\n  {'Model':<25} {'Accuracy':<10}")
    print("  " + "-" * 35)
    for model_name, acc in sorted_results:
        print(f"  {model_name:<25} {acc:.4f}")

    best_model, best_acc = sorted_results[0]
    print(f"\n  *** BEST: {best_model} = {best_acc:.4f} ({best_acc * 100:.2f}%) ***")

    return {
        "dataset": name,
        "specimens": len(species),
        "landmarks": landmarks.shape[1],
        "features": X.shape[1],
        "classes": n_classes,
        "best_model": best_model,
        "best_accuracy": best_acc,
        "best_accuracy_pct": best_acc * 100,
        "all_results": results,
        "tuned_weighted_voting": tuned_weighted_voting,
    }


# =============================================================================
# MAIN
# =============================================================================


def main():
    print("=" * 70)
    print("  02_ADVANCED MORPHOMETRIC CLASSIFICATION")
    print("  State-of-the-Art Ensemble Methods")
    print("=" * 70)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # print(f"\n  Output directory: {OUTPUT_DIR}")

    # datasets = [
    #     ("Canids", "Canids/raw_data/canids_morphologika.txt", "canids"),
    #     ("Hominids", "Hominids/raw_data/landmarks_paper_morphologika.txt", "hominids"),
    #     (
    #         "Papionins",
    #         "Papionins/raw_data/cercocebus,macaca mandrilus, papio and lophocebus adults .txt",
    #         "papionins",
    #     ),
    #     ("Bears", "Bears/raw_data/bears_morphologika.txt", "bears"),
    #     ("Quolls", "Quolls/raw_data/quolls_morphologika.txt", "quolls"),
    #     ("Wolves", "Wolf/raw_data/wolf_morphologika.txt", "wolves"),
    #     ("Aariz", "Aariz/raw_data/aariz_morphologika.txt", "aariz"),
    # ]

    # # Resolve paths relative to project root so script works from any cwd
    # adjusted_datasets = []
    # for name, path, dtype in datasets:
    #     path_resolved = os.path.join(PROJECT_ROOT, path)
    #     if not os.path.exists(path_resolved):
    #         alt_paths = [
    #             path_resolved,
    #             path,
    #             os.path.join(
    #                 PROJECT_ROOT,
    #                 os.path.dirname(path).replace("raw_data", ""),
    #                 os.path.basename(path),
    #             ),
    #             os.path.join(PROJECT_ROOT, "raw_data", os.path.basename(path)),
    #         ]
    #         if "wolf" in path.lower():
    #             alt_paths.extend(
    #                 [
    #                     os.path.join(
    #                         PROJECT_ROOT, "Wolves", "raw_data", os.path.basename(path)
    #                     ),
    #                     os.path.join(
    #                         PROJECT_ROOT, "wolf", "raw_data", os.path.basename(path)
    #                     ),
    #                 ]
    #             )
    #         found = False
    #         for alt_path in alt_paths:
    #             if os.path.exists(alt_path):
    #                 path_resolved = alt_path
    #                 found = True
    #                 break
    #         if not found:
    #             print(f"  WARNING: {name} file not found at: {path_resolved}")
    #             print(f"    Skipping {name}...")
    #             continue
    #     adjusted_datasets.append((name, path_resolved, dtype))

    # datasets = adjusted_datasets

    # Process datasets one at a time and save incrementally to reduce memory usage
    excel_path = os.path.join(OUTPUT_DIR, "Advanced_Classification_Results.xlsx")
    all_summaries = []
    model_scores = {}  # model_name -> list of accuracies (for final comparison)
    tuned_voting_params = {}
    confusion_matrices = {}
    best_overall_model = None

    best_overall_params = None

    # Initialize Excel file with headers
    results_data = []
    summary_data = []
    best_models_data = []

    print(f"\n  Processing {len(datasets)} datasets one at a time...")
    print("  Results will be saved incrementally to reduce memory usage.\n")

    for idx, (name, path, dtype) in enumerate(datasets, 1):
        print(f"\n{'=' * 70}")
        print(f"  Processing dataset {idx}/{len(datasets)}: {name}")
        print(f"{'=' * 70}")

        # Process this dataset
        result = analyze_dataset(name, path, dtype, OUTPUT_DIR)

        if result:
            # Store minimal summary info
            summary_info = {
                "dataset": result["dataset"],
                "specimens": result["specimens"],
                "landmarks": result["landmarks"],
                "features": result["features"],
                "classes": result["classes"],
                "best_model": result["best_model"],
                "best_accuracy": result["best_accuracy"],
                "best_accuracy_pct": result.get(
                    "best_accuracy_pct", result["best_accuracy"] * 100
                ),
            }
            all_summaries.append(summary_info)

            # Collect model scores for final comparison
            for model_name, acc in result["all_results"].items():
                if model_name not in model_scores:
                    model_scores[model_name] = []
                model_scores[model_name].append(
                    {"dataset": result["dataset"], "accuracy": acc}
                )

            # Add to Excel data (will be saved incrementally)
            for model, acc in result["all_results"].items():
                results_data.append(
                    {"Dataset": result["dataset"], "Model": model, "Accuracy": acc}
                )

            summary_data.append(summary_info)
            best_models_data.append(
                {
                    "Dataset": result["dataset"],
                    "Best_Model": result["best_model"],
                    "Accuracy": result["best_accuracy"],
                    "Accuracy_%": f"{result['best_accuracy'] * 100:.2f}%",
                }
            )

            if result.get("tuned_weighted_voting"):
                tuned_voting_params[result["dataset"]] = result["tuned_weighted_voting"]

            # Save incrementally after each dataset
            try:
                with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                    pd.DataFrame(results_data).to_excel(
                        writer, sheet_name="All_Results", index=False
                    )
                    pd.DataFrame(summary_data).to_excel(
                        writer, sheet_name="Summary", index=False
                    )
                    pd.DataFrame(best_models_data).to_excel(
                        writer, sheet_name="Best_Models", index=False
                    )
                print(f"\n  [OK] Incremental save: Results for {name} saved to Excel")
            except Exception as e:
                print(f"  [WARNING] Could not save incrementally: {e}")

        # Force garbage collection to free memory
        import gc

        gc.collect()
        print(f"  Memory cleared after processing {name}")

    # Final comparison
    print("\n" + "=" * 70)
    print("  FINAL COMPARISON - ALL DATASETS")
    print("=" * 70)

    print(
        f"\n  {'Dataset':<12} {'Spec':<6} {'LM':<4} {'Feat':<6} {'Cls':<4} {'Best Model':<22} {'Accuracy':<10} {'Accuracy %':<12}"
    )
    print("  " + "-" * 85)

    for s in all_summaries:
        acc_pct = s.get("best_accuracy_pct", s["best_accuracy"] * 100)
        print(
            f"  {s['dataset']:<12} {s['specimens']:<6} {s['landmarks']:<4} {s['features']:<6} {s['classes']:<4} {s['best_model']:<22} {s['best_accuracy']:.4f} {acc_pct:>10.2f}%"
        )

    avg_acc = np.mean([s["best_accuracy"] for s in all_summaries])
    avg_acc_pct = avg_acc * 100
    print("  " + "-" * 85)
    print(
        f"  {'AVERAGE':<12} {'':<6} {'':<4} {'':<6} {'':<4} {'':<22} {avg_acc:.4f} {avg_acc_pct:>10.2f}%"
    )
    print("=" * 85)

    # =========================================================================
    # FIND BEST MODEL ACROSS ALL DATASETS
    # =========================================================================
    print("\n" + "=" * 70)
    print("  BEST MODEL ACROSS ALL DATASETS")
    print("=" * 70)

    # Calculate average accuracy per model (only for models tested on all datasets)
    model_averages = {}
    for model_name, scores in model_scores.items():
        if len(scores) == len(all_summaries):  # Model tested on all datasets
            avg_acc = np.mean([s["accuracy"] for s in scores])
            model_averages[model_name] = {"average": avg_acc, "scores": scores}

    if len(model_averages) > 0:
        # Sort by average accuracy, tiebreak by minimum per-dataset accuracy (higher = better)
        sorted_models = sorted(
            model_averages.items(),
            key=lambda x: (
                -x[1]["average"],
                -min(s["accuracy"] for s in x[1]["scores"]),
            ),
        )

        print(f"\n  Models tested on all {len(all_summaries)} datasets:")
        print(
            f"\n  {'Model':<25} {'Avg Accuracy':<15} {'Accuracy %':<12} {'Per-Dataset Scores'}"
        )
        print("  " + "-" * 100)

        for model_name, data in sorted_models:
            avg = data["average"]
            scores_str = ", ".join(
                [f"{s['dataset']}: {s['accuracy']:.3f}" for s in data["scores"]]
            )
            print(
                f"  {model_name:<25} {avg:.4f}          {avg * 100:>10.2f}%    {scores_str}"
            )

        # Best overall model
        best_overall_model, best_overall_data = sorted_models[0]
        best_overall_avg = best_overall_data["average"]

        print(f"\n  {'=' * 70}")
        print(f"  *** BEST MODEL ACROSS ALL DATASETS: {best_overall_model} ***")
        print(
            f"  *** Average Accuracy: {best_overall_avg:.4f} ({best_overall_avg * 100:.2f}%) ***"
        )
        print(f"  {'=' * 70}")

        print(f"\n  Per-Dataset Performance:")
        for s in best_overall_data["scores"]:
            print(
                f"    {s['dataset']}: {s['accuracy']:.4f} ({s['accuracy'] * 100:.2f}%)"
            )
    else:
        print(f"\n  No model was tested on all {len(all_summaries)} datasets.")
        print(f"  This may happen if some models failed on certain datasets.")

    # Tune the best overall model across datasets
    if best_overall_model:
        print("\n" + "=" * 70)
        print(f"  GLOBAL TUNING - BEST OVERALL MODEL ({best_overall_model})")
        print("=" * 70)
        if best_overall_model == "Weighted Voting":
            best_overall_params = tune_global_weighted_voting(datasets)
            if best_overall_params:
                print(
                    f"    Params: top_k={best_overall_params['top_k']}, "
                    f"weight_power={best_overall_params['weight_power']}, "
                    f"cv_folds={best_overall_params.get('cv_folds')}, "
                    f"cv_accuracy={best_overall_params['cv_accuracy']:.4f}"
                )
        elif best_overall_model == "Blending":
            best_overall_params = tune_global_blending(datasets)
            if best_overall_params:
                print(
                    f"    Params: blend_holdout={best_overall_params['blend_holdout']}, "
                    f"meta_C={best_overall_params['meta_C']}, "
                    f"cv_folds={best_overall_params.get('cv_folds')}, "
                    f"cv_accuracy={best_overall_params['cv_accuracy']:.4f}"
                )
        else:
            print("    [INFO] No global tuning implemented for this model.")

    # Build confusion matrices using the best overall model
    if best_overall_model:
        print("\n" + "=" * 70)
        print(f"  CONFUSION MATRICES - BEST OVERALL MODEL ({best_overall_model})")
        print("=" * 70)
        for name, path, dtype in datasets:
            cm_data = build_confusion_matrix_for_model(
                name,
                path,
                dtype,
                best_overall_model,
                OUTPUT_DIR,
                best_model_params=best_overall_params,
            )
            if cm_data:
                confusion_matrices[name] = {
                    "matrix": cm_data["matrix"],
                    "labels": cm_data["labels"],
                }

    # Final save with all sheets including best overall model
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        # Sheet 1: Run parameters (first so it's the landing sheet when opening)
        params_rows = [
            {"Parameter": "run_timestamp", "Value": datetime.now().isoformat()},
            {"Parameter": "seed", "Value": RANDOM_STATE},
            {"Parameter": "min_samples", "Value": MIN_SAMPLES},
            {"Parameter": "n_splits", "Value": N_SPLITS},
            {
                "Parameter": "input_files",
                "Value": str([os.path.basename(f) for f in datasets_filepaths]),
            },
            {"Parameter": "tune_weighted_voting", "Value": TUNE_WEIGHTED_VOTING},
            {"Parameter": "voting_top_k_grid", "Value": str(VOTING_TOP_K_GRID)},
            {
                "Parameter": "voting_weight_power_grid",
                "Value": str(VOTING_WEIGHT_POWER_GRID),
            },
            {"Parameter": "cv_folds_grid", "Value": str(CV_FOLDS_GRID)},
            {"Parameter": "blend_holdout_grid", "Value": str(BLEND_HOLDOUT_GRID)},
            {"Parameter": "blend_meta_c_grid", "Value": str(BLEND_META_C_GRID)},
            {"Parameter": "XGBoost.n_estimators", "Value": args.boost_n_estimators},
            {"Parameter": "XGBoost.max_depth", "Value": args.boost_max_depth},
            {"Parameter": "XGBoost.learning_rate", "Value": args.boost_learning_rate},
            {"Parameter": "LightGBM.n_estimators", "Value": args.boost_n_estimators},
            {"Parameter": "LightGBM.max_depth", "Value": args.boost_max_depth},
            {"Parameter": "LightGBM.learning_rate", "Value": args.boost_learning_rate},
            {"Parameter": "CatBoost.iterations", "Value": args.boost_n_estimators},
            {"Parameter": "CatBoost.depth", "Value": args.boost_max_depth},
            {"Parameter": "CatBoost.learning_rate", "Value": args.boost_learning_rate},
            {"Parameter": "RandomForest.n_estimators", "Value": args.rf_n_estimators},
            {
                "Parameter": "RandomForest.max_depth",
                "Value": args.rf_max_depth if args.rf_max_depth != 0 else "unlimited",
            },
            {"Parameter": "ExtraTrees.n_estimators", "Value": args.rf_n_estimators},
            {
                "Parameter": "ExtraTrees.max_depth",
                "Value": args.rf_max_depth if args.rf_max_depth != 0 else "unlimited",
            },
            {
                "Parameter": "GradientBoosting.n_estimators",
                "Value": args.gb_n_estimators,
            },
            {"Parameter": "GradientBoosting.max_depth", "Value": args.gb_max_depth},
            {
                "Parameter": "GradientBoosting.learning_rate",
                "Value": args.gb_learning_rate,
            },
            {"Parameter": "MLP.hidden_layer_sizes", "Value": args.mlp_layers},
            {"Parameter": "MLP.alpha", "Value": args.mlp_alpha},
            {"Parameter": "MLP.max_iter", "Value": args.mlp_max_iter},
            {"Parameter": "SVM.C", "Value": args.svm_c},
            {"Parameter": "LogisticRegression.C", "Value": args.lr_c},
            {"Parameter": "KNN.n_neighbors", "Value": args.knn_n_neighbors},
            {"Parameter": "KNN.weights", "Value": args.knn_weights},
        ]
        pd.DataFrame(params_rows).to_excel(
            writer, sheet_name="Run_Parameters", index=False
        )

        # Sheet 2: All results
        results_df = pd.DataFrame(results_data)
        results_df.to_excel(writer, sheet_name="All_Results", index=False)

        # Sheet 3: Summary by dataset
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        # Sheet 4: Best models comparison
        best_models_df = pd.DataFrame(best_models_data)
        best_models_df.to_excel(writer, sheet_name="Best_Models", index=False)

        # Sheet 5: Best model across all datasets
        if len(model_averages) > 0:
            sorted_models = sorted(
                model_averages.items(), key=lambda x: -x[1]["average"]
            )
            best_overall_data_list = []
            for model_name, data in sorted_models:
                row = {
                    "Model": model_name,
                    "Average_Accuracy": data["average"],
                    "Average_Accuracy_%": data["average"] * 100,
                }
                # Add per-dataset scores
                for s in data["scores"]:
                    row[f"{s['dataset']}_Accuracy"] = s["accuracy"]
                    row[f"{s['dataset']}_Accuracy_%"] = s["accuracy"] * 100
                best_overall_data_list.append(row)

            best_overall_df = pd.DataFrame(best_overall_data_list)
            best_overall_df.to_excel(
                writer, sheet_name="Best_Overall_Model", index=False
            )

        # Sheet 6: Tuned weighted voting params (if available)
        if tuned_voting_params:
            tuned_rows = []
            for dataset_name, params in tuned_voting_params.items():
                tuned_rows.append(
                    {
                        "Dataset": dataset_name,
                        "Top_K": params.get("top_k"),
                        "Weight_Power": params.get("weight_power"),
                        "CV_Accuracy": params.get("cv_accuracy"),
                        "Top_Models": ", ".join(params.get("top_models", [])),
                        "Weights": ", ".join(
                            [f"{w:.6f}" for w in params.get("weights", [])]
                        ),
                        "CV_Folds": params.get("cv_folds", N_SPLITS),
                        "Model_Scores_JSON": json.dumps(params.get("model_scores", {})),
                    }
                )
            tuned_df = pd.DataFrame(tuned_rows)
            tuned_df.to_excel(writer, sheet_name="Tuned_Weighted_Voting", index=False)

        # Sheet 7: Tuned best overall model (if available)
        if best_overall_model and best_overall_params:
            best_rows = [
                {"Best_Overall_Model": best_overall_model, **best_overall_params}
            ]
            best_df = pd.DataFrame(best_rows)
            best_df.to_excel(writer, sheet_name="Tuned_Best_Overall_Model", index=False)

        # Sheet 8+: Confusion matrices (best overall model)
        for dataset_name, cm_data in confusion_matrices.items():
            labels = cm_data["labels"]
            cm_df = pd.DataFrame(cm_data["matrix"], index=labels, columns=labels)
            sheet_name = f"CM_{dataset_name}"
            cm_df.to_excel(writer, sheet_name=sheet_name)

    # Save tuned weighted voting params for reuse
    if tuned_voting_params:
        tuned_path = os.path.join(MISC_DIR, "weighted_voting_tuned_params.json")
        try:
            with open(tuned_path, "w", encoding="utf-8") as f:
                json.dump(tuned_voting_params, f, indent=2)
            print(
                f"\n  [OK] Tuned weighted voting params saved to: {os.path.join('misc', os.path.basename(tuned_path))}"
            )
        except Exception as e:
            print(f"\n  [WARNING] Could not save tuned voting params: {e}")

    print(f"\n  [OK] Results saved to: {os.path.basename(excel_path)}")
    print(f"    - Sheet 1: Run_Parameters (all settings used for this run)")
    print(f"    - Sheet 2: All_Results (all models for all datasets)")
    print(f"    - Sheet 3: Summary (dataset overview)")
    print(f"    - Sheet 4: Best_Models (best model per dataset)")
    if len(model_averages) > 0:
        print(f"    - Sheet 5: Best_Overall_Model (best model across all datasets)")
    print(f"\n  All outputs saved")
    print(f"    - Excel file: Advanced_Classification_Results.xlsx")
    print(f"    - Confusion matrices: *_Confusion_Matrix.png")


if __name__ == "__main__":
    main()
