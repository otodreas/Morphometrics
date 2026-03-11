# Morphometric Classification GUI

A user-friendly PyQt6 desktop application for running advanced morphometric classification analysis on anatomical landmark data.

## Quick Start

### Installation

1. **Install Python 3.9+** (if not already installed)

2. **Install dependencies:**
```bash
pip install -r requirements_gui.txt
```

3. **Run the GUI:**
```bash
python morphometrics_gui.py
```

The GUI window will open immediately.

## Features

### 📊 Dataset Selection
- Select which datasets to process from 7 available collections:
  - **Canids**: 3D, 117 specimens, 41 landmarks, 3 classes (Wild/Domestic types)
  - **Hominids**: 3D, 75 specimens, 10 landmarks, 3 classes
  - **Papionins**: 3D, 93 specimens, 31 landmarks, 5 classes
  - **Bears**: 3D, 48 specimens, 39 landmarks, 3 classes
  - **Quolls**: 3D, 101 specimens, 101 landmarks, 5 classes
  - **Wolves**: 3D, 84 specimens, 54 landmarks, 6 classes
  - **Aariz**: 2D, 1000 specimens, 29 landmarks, 6 classes

### ⚙️ Configuration
Adjust ML pipeline settings:
- **Random State**: For reproducible results (default: 42)
- **CV Folds**: Number of cross-validation splits (default: 5)
- **Min Samples per Class**: Filter out rare classes (default: 3)
- **Ensemble Tuning**: Enable/disable weighted voting optimization
- **Global Tuning**: Optimize across all datasets simultaneously

### 📈 Real-Time Monitoring
- Live console output showing script progress
- Status updates as datasets are processed
- Elapsed time tracking

### 📁 Results Management
- Automatic results folder opening
- View all generated files (Excel, PNG, logs)
- Summary of output files in the GUI

## How It Works

### The Classification Pipeline

The script uses state-of-the-art machine learning techniques:

#### Feature Engineering (No PCA)
The script computes comprehensive shape features from landmark coordinates:
- **Pairwise Distances**: All combinations of landmark distances
- **Interlandmark Angles**: Angles between triplets of landmarks
- **Centroid Features**: Distance from each landmark to the centroid
- **Bounding Box**: Dimensions and aspect ratios
- **Statistical Moments**: Skewness and kurtosis of landmark distributions
- **Shape Descriptors**: Eigenvalues of covariance matrix
- **Scale-Invariant Ratios**: Distance ratios for scale independence

#### Machine Learning Models

**11 Base Classifiers:**
- XGBoost, LightGBM, CatBoost (Gradient Boosting ensemble)
- Random Forest, Extra Trees, Gradient Boosting
- Logistic Regression, Linear Discriminant Analysis (LDA)
- Support Vector Machine (SVM)
- Multi-layer Perceptron (Neural Network)
- K-Nearest Neighbors (KNN)

**3 Ensemble Methods:**
- **Stacking**: Uses a meta-learner to combine base models
- **Blending**: Holds out validation set for ensemble training
- **Weighted Voting**: Weights each model by cross-validation accuracy

#### Evaluation
- Stratified K-fold cross-validation (default: 5 folds)
- Ensures each specimen is predicted exactly once
- Automatic tuning of ensemble parameters
- Confusion matrices for visualization

### Output Files

The analysis generates the following files in `02_Advanced_Morphometric_Classification_outputs/`:

1. **Advanced_Classification_Results.xlsx**
   - Multiple sheets with detailed results
   - Model accuracies for all 14 classifiers
   - Dataset summaries
   - Best model identification
   - Tuned parameters

2. **[Dataset]_Confusion_Matrix_Best_Overall.png**
   - Visual representation of classification performance
   - One image per dataset
   - Shows misclassification patterns

3. **run.log.txt**
   - Complete console output
   - Timestamps for each step
   - Useful for debugging

4. **weighted_voting_tuned_params.json**
   - Optimal ensemble parameters
   - Can be used for reproducibility

## Usage Guide

### Basic Workflow

1. **Launch the GUI**
   ```bash
   python morphometrics_gui.py
   ```

2. **Select Datasets** (Datasets tab)
   - Check the datasets you want to analyze
   - Uncheck to skip datasets
   - Papionins is recommended for testing (faster, smaller dataset)

3. **Configure Settings** (Settings tab, optional)
   - Most users can use the defaults
   - Adjust only if you need specific configurations

4. **Run Analysis** (Click "Run Analysis" button)
   - Script will start processing
   - Console output shows real-time progress
   - Status bar indicates current state

5. **View Results**
   - Results tab shows file summary when complete
   - Click "Open Results Folder" to view generated files
   - Open the Excel file in a spreadsheet application

### Quick Test

To verify everything works before running full analysis:

1. Uncheck all datasets except "Papionins" (smallest dataset)
2. Click "Run Analysis"
3. Wait ~10-20 minutes depending on your computer
4. Check the results folder for output files

### Processing Time Estimates

On a modern computer (16GB RAM, SSD):
- **Single dataset**: 30 minutes - 2 hours
- **All datasets**: 2-5 days

On a university cluster:
- **All datasets**: ~2 days (with parallel processing)

## Troubleshooting

### Script Not Found
**Error**: "Could not find script at..."
**Solution**: 
- Ensure `02_Advanced_Morphometric_Classification.py` is in the `Materials` directory
- The GUI should be in the `Morphometrics` directory

### Missing Dependencies
**Error**: "ModuleNotFoundError: No module named 'xgboost'"
**Solution**:
```bash
pip install -r requirements_gui.txt
```
Note: XGBoost, LightGBM, CatBoost are optional. Script will work without them but with reduced model variety.

### Out of Memory
**Error**: "MemoryError" during processing
**Solution**:
- Process fewer datasets at once
- Close other applications to free memory
- Consider running on a machine with more RAM

### Slow Performance
**Problem**: Script runs very slowly
**Solution**:
- This is normal for the first dataset (initialization overhead)
- Subsequent datasets should be faster
- Consider running fewer datasets simultaneously

### Results Not Appearing
**Problem**: "Open Results Folder" shows empty directory
**Solution**:
- Check that the analysis completed (check status bar)
- If analysis failed, check console output for error messages
- Results folder location: `02_Advanced_Morphometric_Classification_outputs/`

## Advanced Configuration

### Command Line (For Power Users)

If you prefer command-line usage, run the original script directly:

```bash
cd Materials
python 02_Advanced_Morphometric_Classification.py
```

Then edit the script's `main()` function to customize dataset selection.

### Modifying Default Settings

Edit `morphometrics_gui.py` to change defaults (around line 180):

```python
self.random_state_spinbox = QSpinBox()
self.random_state_spinbox.setValue(42)  # Change this to your preferred value
```

### Saving Configuration

The GUI automatically saves your settings to `morphometrics_config.json` when you close it. These settings are restored when you reopen the GUI.

## Understanding the Output

### Excel Results File

The `Advanced_Classification_Results.xlsx` contains:

**Sheet 1: Model Scores**
- Accuracy of each model (14 total)
- Cross-validation performance
- Dataset-by-dataset breakdown

**Sheet 2: Dataset Summary**
- Number of specimens per dataset
- Number of landmarks
- Number of classes
- Number of features engineered

**Sheet 3: Best Models**
- Best model for each dataset
- Accuracy achieved
- Model type

**Sheet 4: Tuned Parameters**
- Optimal ensemble settings
- Hyperparameter values used
- Validation accuracy

### Confusion Matrix Images

PNG files show classification accuracy:
- Rows = true class
- Columns = predicted class
- Diagonal = correct classifications
- Off-diagonal = misclassifications

Darker colors indicate higher frequencies.

## System Requirements

**Minimum:**
- Python 3.9 or higher
- 8 GB RAM
- 2 GB disk space

**Recommended:**
- Python 3.10 or 3.11
- 16 GB RAM
- 5 GB disk space
- SSD (faster processing)

**Operating Systems:**
- macOS (tested on Big Sur, Monterey, Ventura)
- Windows 10/11
- Linux (Ubuntu 20.04+)

## Important Notes

⚠️ **Processing Time**: Full analysis of all datasets can take 2-5 days on a local machine. Plan accordingly.

⚠️ **Memory Usage**: Large datasets (especially Aariz with 1000 specimens) may use 4-8 GB RAM. Close other applications if needed.

⚠️ **First Run**: Dependencies may take time to compile on first installation (especially XGBoost/LightGBM).

✅ **Reproducibility**: Using the same random state (default 42) ensures reproducible results across runs.

## Citation

If you use this GUI or the underlying classification script in your research, please cite:

```
Advanced Morphometric Classification using Machine Learning Ensembles
Author: Sara
Year: 2025
```

The script implements state-of-the-art techniques including:
- Comprehensive feature engineering (no PCA)
- Multiple gradient boosting variants (XGBoost, LightGBM, CatBoost)
- Ensemble methods (Stacking, Blending, Weighted Voting)
- Stratified cross-validation

## Support & Issues

For issues or questions:

1. **Check the Console Tab** - detailed error messages are shown there
2. **Review run.log.txt** - saved in the output directory
3. **Check that data files exist** - ensure `Materials/[Dataset]/raw_data/` folders are present
4. **Verify Python installation** - run `python --version` in terminal

## License

This GUI is provided as-is for research and educational purposes.

---

**Version**: 1.0  
**Last Updated**: 2025  
**Python**: 3.9+  
**PyQt6**: 6.4+