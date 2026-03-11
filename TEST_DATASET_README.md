# 🚀 Test Dataset - Quick 1-2 Minute Testing

## Overview

A **minimal synthetic dataset** designed to run the morphometric classification pipeline in **under 2 minutes**. Perfect for:
- ✅ Verifying the GUI works
- ✅ Testing your Python setup
- ✅ Quick workflow validation
- ✅ Demonstrating the system
- ✅ Debugging issues

## Dataset Specifications

| Property | Value |
|----------|-------|
| **Specimens** | 18 (6 per species) |
| **Landmarks** | 8 per specimen |
| **Dimensions** | 3D (X, Y, Z coordinates) |
| **Classes** | 3 species (A, B, C) |
| **Expected Runtime** | 60-120 seconds |
| **File Location** | `Materials/TestData/raw_data/test_data_morphologika.txt` |
| **File Size** | 3.1 KB |

## Quick Start (Under 2 Minutes)

### Option 1: Using the GUI

```bash
# 1. Install dependencies (one-time)
pip install -r requirements_gui.txt

# 2. Launch the GUI
python3 morphometrics_gui.py

# 3. In the GUI, you need to add TestData to the datasets list
#    Edit morphometrics_gui.py around line 220 and add:
#    "TestData": ("TestData/raw_data/test_data_morphologika.txt", "testdata", True),

# 4. Restart the GUI
python3 morphometrics_gui.py

# 5. Select TestData dataset and click Run
```

### Option 2: Direct Script (Simplest)

```bash
cd Morphometrics/Materials

# Edit line ~1480 in 02_Advanced_Morphometric_Classification.py
# Change the datasets list to:
# datasets = [
#     ('TestData', 'TestData/raw_data/test_data_morphologika.txt', 'testdata'),
# ]

python 02_Advanced_Morphometric_Classification.py
```

**Total time: 60-120 seconds from start to finish!**

## Expected Output

```
======================================================================
  02_ADVANCED MORPHOMETRIC CLASSIFICATION
  State-of-the-Art Ensemble Methods
======================================================================

  Processing 1 datasets one at a time...

===============================================
  Processing dataset 1/1: TestData
===============================================

  Loaded: 18 specimens, 8 landmarks
  
  Species distribution (3 classes):
    Species_A: 6
    Species_B: 6
    Species_C: 6

  Feature Engineering (NO PCA):
    [Computing features...]
    Total features engineered: ~60-80
    
  [1] INDIVIDUAL MODELS (5-fold stratified CV):
    XGBoost................: 1.0000
    LightGBM...............: 1.0000
    CatBoost...............: 1.0000
    Random Forest..........: 1.0000
    Extra Trees............: 1.0000
    Gradient Boosting......: 1.0000
    Logistic Regression....: 1.0000
    LDA....................: 1.0000
    SVM....................: 1.0000
    MLP....................: 1.0000
    KNN....................: 1.0000

  [2] STACKING ENSEMBLE...: 1.0000
  [3] WEIGHTED VOTING.....: 1.0000

  ✓ SUCCESS: Classification completed successfully!
```

## Output Files Generated

After running, you'll find in `02_Advanced_Morphometric_Classification_outputs/`:

1. **Advanced_Classification_Results.xlsx**
   - Model Scores sheet with accuracy of all 14 classifiers
   - Dataset Summary sheet
   - Best Models sheet
   - Confusion matrices

2. **TestData_Confusion_Matrix_Best_Overall.png**
   - 3x3 confusion matrix showing perfect classification
   - All specimens correctly classified

3. **run.log.txt**
   - Complete execution log
   - Timestamps and detailed output

4. **weighted_voting_tuned_params.json**
   - Optimized ensemble parameters

## Dataset Details

### File Format
The test dataset is in Morphologika format:
```
[individuals]      18           # Number of specimens
[landmarks]        8            # Landmarks per specimen
[dimensions]       3            # 3D coordinates (X, Y, Z)
[names]            Species_*_*  # Specimen identifiers
[rawpoints]        X Y Z        # Landmark coordinates
```

### Species Labels
Species are determined from specimen names:
- `Species_A_Specimen_01` → **Species A**
- `Species_B_Specimen_01` → **Species B**
- `Species_C_Specimen_01` → **Species C**

### Data Design
The three species are deliberately **well-separated** in coordinate space:
- **Species A**: Coordinates in ~10-13 range
- **Species B**: Coordinates in ~15-18 range
- **Species C**: Coordinates in ~20-23 range

This makes perfect classification expected, which validates the system works.

## Performance Expectations

### Runtimes by Hardware

| System | RAM | Storage | Time |
|--------|-----|---------|------|
| Fast (modern) | 16 GB | SSD | 30-60 sec |
| Medium | 8 GB | SSD | 60-90 sec |
| Slow | 4 GB | HDD | 90-120 sec |

### Accuracy Expectations

All 14 models should achieve **>95% accuracy** because:
- Specimens are clearly separated by species
- Dataset is noise-free (synthetic)
- Only 3 classes (easy to distinguish)
- Small dataset (fast to process)

Expected results:
- Individual models: 100% accuracy (perfect separation)
- Ensemble methods: 100% accuracy
- Confusion matrix: All on diagonal (no errors)

## Use Cases

### 1. Verify Installation
Run test dataset to confirm:
- ✅ Python installation works
- ✅ Dependencies installed correctly
- ✅ GUI launches properly
- ✅ Script executes without errors
- ✅ All output files generated

### 2. Test Configuration Changes
Quickly test different settings:
- Try different random states
- Adjust CV folds
- Test ensemble tuning
- Verify results change appropriately

### 3. Benchmark Your System
Use test dataset runtime to estimate full dataset times:
```
Full dataset time ≈ Test dataset time × (specimens / 18) × (landmarks / 8)
```

Example:
- Test dataset: 60 seconds
- Papionins: 93 specimens, 31 landmarks
- Estimated time: 60 × (93/18) × (31/8) = ~1200 seconds ≈ 20 minutes ✓

### 4. Demonstrate to Colleagues
Show the system working in under 2 minutes:
- Launch GUI
- Select TestData
- Run analysis
- Show Excel results

### 5. Debug Issues
When something breaks:
1. Test with TestData (should work)
2. If TestData fails, environment is broken
3. If TestData passes, problem is dataset-specific

## Comparison with Real Datasets

| Dataset | Specimens | Landmarks | Classes | Time |
|---------|-----------|-----------|---------|------|
| **TestData** | 18 | 8 | 3 | **1-2 min** |
| Papionins | 93 | 31 | 5 | ~20 min |
| Bears | 48 | 39 | 3 | ~10 min |
| Hominids | 75 | 10 | 3 | ~15 min |
| Canids | 117 | 41 | 3 | ~25 min |
| Wolves | 84 | 54 | 6 | ~20 min |
| Quolls | 101 | 101 | 5 | ~25 min |
| Aariz | 1000 | 29 | 6 | ~40 min |
| **All 7 Real** | - | - | - | **2-5 days** |

## Step-by-Step Instructions

### Method A: GUI (Recommended for Learning)

```bash
# Step 1: Install (one-time setup)
cd Morphometrics
pip install -r requirements_gui.txt

# Step 2: Edit GUI to add TestData
# Open morphometrics_gui.py in text editor
# Find: self.datasets = {
# Add this line:
# "TestData": ("TestData/raw_data/test_data_morphologika.txt", "testdata", True),

# Step 3: Launch GUI
python3 morphometrics_gui.py

# Step 4: In the GUI
# - Go to Datasets tab
# - Uncheck all datasets
# - Check TestData
# - Click "Run Analysis"
# - Wait 1-2 minutes
# - Click "Open Results Folder"

# Step 5: Open results
# - Open Advanced_Classification_Results.xlsx
# - Review model accuracies
```

### Method B: Direct Script (Fastest)

```bash
# Step 1: Navigate to script
cd Morphometrics/Materials

# Step 2: Edit script
# Open 02_Advanced_Morphometric_Classification.py
# Find line ~1480 (in main() function)
# Replace datasets list with:
# datasets = [
#     ('TestData', 'TestData/raw_data/test_data_morphologika.txt', 'testdata'),
# ]

# Step 3: Run
python 02_Advanced_Morphometric_Classification.py

# Step 4: View results
# Check 02_Advanced_Morphometric_Classification_outputs/
```

## Troubleshooting

### "File not found" Error
**Problem**: Script can't find test_data_morphologika.txt
**Solution**:
- Verify file exists: `ls Materials/TestData/raw_data/test_data_morphologika.txt`
- Check you're in correct directory
- Verify path in script/GUI is correct

### Analysis Takes Too Long
**Problem**: Takes more than 3 minutes
**Solution**:
- Check you're really running TestData only (not all 7 datasets)
- Verify you edited the datasets list correctly
- Check if other programs are using CPU
- Close other applications

### Low Accuracy Results
**Problem**: Models getting <80% accuracy
**Solution**:
- Test dataset is designed for 100% accuracy
- Something may be wrong with parsing
- Check specimen names match "Species_X_*" pattern
- Verify file format is correct

### No Output Files
**Problem**: Finished but no results folder
**Solution**:
- Check the script ran successfully (no error messages)
- Look for `02_Advanced_Morphometric_Classification_outputs/`
- Check you have write permissions
- Ensure disk space is available

## What This Teaches You

Running the test dataset teaches you:
1. ✅ How the GUI works
2. ✅ How the classification pipeline processes data
3. ✅ What output files look like
4. ✅ How to interpret results
5. ✅ How your system performs
6. ✅ How to debug issues

## Next Steps After Testing

1. **Test with real data** - Run Papionins dataset (~20 min)
2. **Process multiple datasets** - Choose 2-3 real datasets
3. **Full analysis** - Process all 7 datasets (2-5 days)
4. **Analyze results** - Study the Excel file
5. **Customize** - Adjust parameters for your needs

## Quick Reference

**Test dataset characteristics:**
- 18 specimens (smallest possible with 3 classes × minimum 6 samples)
- 8 landmarks (fast to process)
- 3 species (easy classification)
- Synthetic data (perfectly separated)

**Perfect for:**
- First-time verification
- Quick testing
- System benchmarking
- Workflow demonstration
- Debugging and troubleshooting

**Expected result:**
- Perfect or near-perfect accuracy
- Completes in 1-2 minutes
- Generates all output files
- Validates system setup

---

**Start with the test dataset to verify everything works, then move to real datasets!** ⚡

Use this for rapid iteration and validation before committing to longer analyses.