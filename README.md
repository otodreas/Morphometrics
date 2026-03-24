# Classika

![Python](https://img.shields.io/badge/python-3.11-yellow)
![License](https://img.shields.io/badge/license-MIT-red)
![Platform](https://img.shields.io/badge/platform-streamlit-orange)
![Version](https://img.shields.io/github/v/release/otodreas/Classika)
![Last Commit](https://img.shields.io/github/last-commit/otodreas/Classika)

Interactive morphometrics classification interface for Linux and Mac

This file acts as a manual for Classika and is intended to be read top to bottom

## Repository structure

```
.
├── CHANGELOG.md
├── classika.py
├── docs/
│   ├── images/
│   └── report/
│       └── Classika_AppNote.pdf
├── LICENSE
├── README.md
├── requirements_linux.txt
├── requirements_mac.txt
├── src/
│   ├── __init__.py
│   ├── classification.py
│   └── utils.py
└── test/
    ├── input
    ├── output
    └── README.md
```

## Requirements
- Python>=3.11
- Required packages (see **Download and run** section)
- MacOS:
  - OpenMP needs to be installed via the terminal. To install it, open your terminal app and run
```sh
brew install libomp
```

## Summary
Classika (*morphometric **classi**fication program for Morphologi**ka** files*) is a Streamlit-based local host app built around Sara Behnamian's ML framework for species classification from Morphologika data.

It takes labeled Morphologika data as input, classifies specimens based on advanced morphological parameters using multiple ML algorithms, and returns statistics on those algorithms. Classika may be used to
- Validate labels (if Classika fails to label your data correctly, it could be a sign that the labels are incorrect)
- Assess the quality of your dataset's raw-points coordinates
- Explore machine learning algorithms that may be useful for you in the future

## Download and run
1. Ensure Python is installed on the system
2. Install the latest Classika release from GitHub
3. Unzip the install and open a terminal inside the folder
4. Create and activate virtual environment (recommended). The commands below should be run from the terminal, from the folder where 
```sh
python -m venv .venv
source .venv/bin/activate
```
5. Install requirements
```sh
pip install -r requirements_linux.txt
# OR
pip install -r requirements_mac.txt
```
6. Launch the app
```sh
streamlit run classika.py
```

## Usage

### Import data and set parameters

You are greeted by the data upload page when you launch Classika

<img src="docs/images/upload_screen.png" width="400">
    
Here, you can upload multiple Morphologika files and set some basic settings. Note that the "Number of data splits" option has a sizable impact on processing speed. Higher values will significantly slow down analysis. If you are unfamiliar with k-fold cross-validation, it fills the same function as a traditional train/test split, but aims to control for the quality of a given split.

The advanced settings dropdown exposes the parameters used by the model voting. These settings are best used by experienced users, but more novice users are presented with a button to completely disable the model voting.

<img src="docs/images/tune_voting.png" width="400">
    
Below the advanced settings, the user is presented by dropdown menus for each specific model. These may be left as they are if the user is less experienced in ML methods. All model-specific parameters are saved in the output for reproducibility.

When you are satisfied with the settings, click the "Classify" button at the bottom of the screen.

### Classification runs

After clicking "Classify," the app will show the elapsed time and the bottom 10 lines of the logging file.

<img src="docs/images/classification_screen.png" width="400">
    
Note that classification can take a long time. If the log under "Process status..." does not change, it does not necessarily mean that the process is stuck.

To get a general sense of how far along the analysis is, compare the current process status to the steps of the analysis. You can expect to see these headers appear in the process status viewer, in order

```
[FILTERING]
...
[TUNING]
...
[1] INDIVIDUAL MODELS
...
[2] STACKING ENSEMBLE
...
[3] WEIGHTED VOTING ENSEMBLE
...
[4] BLENDING ENSEMBLE
```

### Downloading results

When the analysis finishes, you will see the download screen

<img src="docs/images/download_screen.png" width="400">
    
Click "Download results" to download a zip folder containing the outputs. When you unzip the file you downloaded, you will find the following files
```
results/
├── Advanced_Classification_Results.xlsx
├── input_filename_Confusion_Matrix_Best_Overall.png
├── misc/
└── run.log.txt
```

`run.log.txt` is identical to all the text that was streamed to the "Process status..." section. Here, you can find information about the rest of the files. In summary:
- `Advanced_Classification_Results.xlsx` contains the bulk of the results in multiple sheets
  - Sheet 1: Run_Parameters (all settings used for the run)
  - Sheet 2: All_Results (all models for all datasets)
  - Sheet 3: Summary (dataset overview)
  - Sheet 4: Best_Models (best model per dataset)
  - Sheet 5: Best_Overall_Model (best model across all datasets)
- `input_filename_Confusion_Matrix_Best_Overall.png` is a confusion matrix that shows the performance of the best model. You will see one confusion matrix per Morphologika file uploaded
- `misc/` is a folder that contains some advanced information, such as the weighted voting summary in `json` format and some automatically generated summary files that pertain to the catboost model

## Classification methods

### Feature engineering

Instead of relying on PCA for dimensionality reduction of the data, Classika builds a feature matrix using a set of engineered features. These features are computed from the 2D or 3D landmark coordinate data present in Morphologika files. These new features include
- Pairwise distances (all combinations)
- Interlandmark angles
- Centroid-based features
- Statistical moments (skewness, kurtosis)
- Procrustes-free shape descriptors
- Distance ratios (scale-invariant)
- Bounding box features
- Principal axes (eigenvalues) - NOT PCA, just shape descriptors

### AI models

Data is not split using typical train/test partitioning, but with stratified k-fold cross validation (CV). This ensures that the training and testing set resemble each other in class proportions. The number of CV folds has a large impact on runtime.

Eleven AI models are trained to classify the data based on the new feature matrices in the process of a Classika run. These models are
- Gradient boosting:
  - XGBoost
  - LightGBM
  - CatBoost
- Tree based:
  - Random Forest
  - Extra Trees
  - Gradient boosting
- Linear models:
  - Logistic regression
  - Linear discriminant analysis (aka LDA)
- Support vector machine (aka SVM)
- Multi-layer perceptron (aka neural network or MLP)
- K-nearest neighbor classification

The breadth of models allows for the strength of all models to be leveraged together. The process is outlined below.

1. Every model is evaluated with stratified k-fold CV and gets a mean accuracy score
2. The top k models are selected
3. Each model's weight is proportional to its accuracy
4. Each model produces a probability distribution over classes 
5. These probability distributions are multiplied by each model's weight and summed
6. The class with the highest weighted total probability wins

## Troubleshooting

### Data import fails

Classika requires plain text files in Morphologika format. If your input file does not contain the headers

```
[individuals]
[landmarks]
[dimensions]
[names]
[rawpoints]
```

Classika will not recognize the file as a Morphologika file

### Slow runs

Classification runs can take anywhere from under a minute to multiple hours or days. If analysis is running slow and you suspect the program is stuck, you can
- Click "Cancel"
- Under "General settings", set "Number of data splits" to 2. This is the lightest data partitioning setting and should allow for relatively quick runs (<10 minutes) on single Morphologika files.

You can also try running the test dataset. In your install of Classika, you installed a folder called `test/`. Inside it are instructions on how to run the test set as well as the output you should expect.

### Unexpected results

You might find you get unexpected results after a run. A potential culprit is incorrect partitioning of true classes in the data. A typical Morphologika file has a `[names]` section, where the classes in the data presented. It might look like

```
[names]
papio cynocephalus  66.491
...
papio cynocephalus  61.742
mandrillus leucophaeus 1959.1.2.6
...
mandrillus leucophaeus 48.444
Macaca mulatta f80.246
...
Macaca mulatta m10.10.19.5
```

Classika assumes that the groups are defined with binomial nomenclature, split by a space or an underscore (i.e. `Homo Sapiens`, `homo_sapiens`, `H. Sapiens`). If this is not the case, your data will not be grouped properly.

## Development notes

### Implementation of original script
We elected to call a modified version of Sara Behnamian's original script with `subprocess.Popen()` so that the program could be run similarly to how it was run by the author with minimal changes. Hardcoded variables were changed to commandline arguments. Lines that were removed from the original script are commented out in `src/classification.py` rather than deleted for clarity. A goal for the future is to clean up `src/classification.py` and provide a diff file to highlight the differences between the original classification script and the Classika-adapted script.

### Temporary directories
Files are copied over to a temporary directory and read from there since Streamlit cannot read files directly from the user's disk. The output files are also written to the same temporary directory, and the files are subsequently written to a zip archive to accommodate easy downloading. The temporary directory is always deleted.
