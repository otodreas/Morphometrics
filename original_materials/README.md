# Morphometric Classification Pipeline

## What This Script Does

This script takes landmark coordinate data from skulls and bones of different animals,
computes shape features, and classifies specimens into groups (species, populations,
skull types) using 14 different machine learning methods. No PCA is used.


## Folder Structure

```
For_Oliver/
├── scripts/
│   └── 02_Advanced_Morphometric_Classification.py   # Main script (~1800 lines)
├── run02.sh                                          # SLURM job script (how I ran it on the cluster)
├── README.md                                         # This file
│
├── Aariz/raw_data/
│   └── aariz_morphologika.txt          # 2D, 1000 specimens, 29 landmarks, 6 classes
├── Bears/raw_data/
│   └── bears_morphologika.txt          # 3D, 48 specimens, 39 landmarks, 3 classes
├── Canids/
│   ├── raw_data/
│   │   └── canids_morphologika.txt     # 3D, 117 specimens, 41 landmarks, 3 classes
│   └── Data/
│       ├── Classifier_sheet.csv        # Extra file needed for canid classification
│       └── Breed_list.csv              # Extra file needed for canid classification
├── Hominids/raw_data/
│   └── landmarks_paper_morphologika.txt # 3D, 75 specimens, 10 landmarks, 3 classes
├── Papionins/raw_data/
│   └── cercocebus,macaca mandrilus, papio and lophocebus adults .txt
│                                        # 3D, 93 specimens, 31 landmarks, 5 classes
├── Quolls/raw_data/
│   └── quolls_morphologika.txt         # 3D, 101 specimens, 101 landmarks, 5 classes
├── Wolf/raw_data/
│   └── wolf_morphologika.txt           # 3D, 84 specimens, 54 landmarks, 6 classes
│
└── 02_Advanced_Morphometric_Classification_outputs/  # Output from my last run
    ├── Advanced_Classification_Results.xlsx
    ├── *_Confusion_Matrix_Best_Overall.png  (one per dataset)
    ├── run.log.txt
    └── weighted_voting_tuned_params.json
```

**Important:** The script must be inside a `scripts/` subfolder. It uses
`PROJECT_ROOT = parent of scripts/` to find the dataset folders.


## Input

The input files are plain text in Morphologika format. Example:

```
[individuals]
93

[landmarks]
31

[dimensions]
3

[names]
Lophocebus albigena AMNH 52592
Macaca mulatta AMNH 35564
Papio cynocephalus AMNH 100450
...

[rawpoints]
'1 Lophocebus albigena AMNH 52592
20.51  28.77  17.16
19.14  27.94  20.69
21.87  26.56  19.79
...
```

The tags are:
- `[individuals]` = how many specimens
- `[landmarks]` = how many landmark points per specimen
- `[dimensions]` = 2 or 3 (the script handles both automatically)
- `[names]` = specimen names, one per line
- `[rawpoints]` = the XYZ (or XY) coordinates, one line per landmark


## Output

The script creates a folder called `02_Advanced_Morphometric_Classification_outputs/`
containing:

- `Advanced_Classification_Results.xlsx` with multiple sheets: all model accuracies,
  dataset summaries, best models, tuned parameters, confusion matrices
- One PNG confusion matrix image per dataset
- `run.log.txt` with the full console output
- `weighted_voting_tuned_params.json` with saved parameters


## How I Ran It

I ran it on our university cluster using the `run02.sh` SLURM script. It took
about 2 days to run everything for all 7 datasets (including the global tuning step
which reruns models across all datasets with different parameter combinations).

To run it on a normal machine, install the dependencies and run:

```bash
pip install numpy pandas scikit-learn scipy matplotlib openpyxl xgboost lightgbm catboost
python scripts/02_Advanced_Morphometric_Classification.py
```

If xgboost, lightgbm, or catboost fail to install, the script will still run but
will skip those classifiers.

To test quickly, open the script, go to the `main()` function, and comment out all
datasets except one (Papionins is a good one to start with because it is small).


## How The Script Works

1. Reads the Morphologika file (the `read_morphologika()` function)

2. Assigns category labels to each specimen. **This is hardcoded per dataset** in the
   `get_species()` function due to time limitations. Each dataset has its own if/elif
   branch that parses the specimen name differently. For example Papionins extracts
   genus names, Hominids groups by genus, Bears extracts population names, etc.
   The Canids dataset has extra special handling in `classify_canids_by_type()` which
   uses the CSV files in `Canids/Data/`.

3. Filters out classes with fewer than 3 specimens

4. Computes shape features from the landmarks (NO PCA):
   - All pairwise distances between landmarks
   - Angles between triplets of landmarks
   - Distances from each landmark to the centroid
   - Bounding box dimensions and aspect ratios
   - Eigenvalues of the covariance matrix (shape descriptors, not PCA)
   - Scale invariant distance ratios

5. Runs 14 classifiers with stratified k fold cross validation:
   - 11 individual: XGBoost, LightGBM, CatBoost, Random Forest, Extra Trees,
     Gradient Boosting, Logistic Regression, LDA, SVM, MLP, KNN
   - 3 ensembles: Stacking, Blending, Weighted Voting

6. Tunes the Weighted Voting ensemble, finds the best model across all datasets,
   builds confusion matrices, and saves everything to Excel and PNG files


## Things That Are Hardcoded (due to time limitations)

- **Label assignment** in `get_species()`: each dataset has its own parsing logic
- **Dataset list** in `main()`: all seven datasets are listed with their file paths
- **Settings** at the top of the script: RANDOM_STATE, MIN_SAMPLES, N_SPLITS, tuning grids
- **Canids special handling**: `classify_canids_by_type()` loads external CSV files


