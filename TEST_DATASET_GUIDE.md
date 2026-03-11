# Test Dataset - Quick Testing Guide

## What Is This?

A minimal test dataset for quickly verifying the GUI and morphometric classification pipeline works correctly. 

**Perfect for:**
- Testing the GUI installation
- Verifying the pipeline runs without errors
- Getting results in under 2 minutes
- Demonstrating the system to colleagues

## Dataset Details

- **Specimens**: 18 (6 per species)
- **Landmarks**: 8 (minimal, for speed)
- **Dimensions**: 3D coordinates
- **Classes**: 3 species (A, B, C)
- **File**: `Materials/TestData/raw_data/test_data_morphologika.txt`

**Expected runtime**: 30-90 seconds per run

## How to Use with the GUI

### Step 1: Launch the GUI
```bash
cd Morphometrics
python3 morphometrics_gui.py
```

### Step 2: Select TestData Dataset
In the "Datasets" tab, you'll need to manually add TestData to the list. For now, follow these steps:

1. Open `morphometrics_gui.py` in a text editor
2. Find the line that says `self.datasets = {`
3. Add this line after the existing datasets:
   ```python
   "TestData": ("TestData/raw_data/test_data_morphologika.txt", "testdata", True),
   ```
4. Save the file
5. Restart the GUI

### Step 3: Run the Test
1. Go to "Datasets" tab
2. Uncheck all datasets
3. Check only "TestData"
4. Click "Run Analysis"
5. Wait ~1 minute

### Step 4: View Results
1. Click "Open Results Folder"
2. Open `Advanced_Classification_Results.xlsx`
3. Review the accuracy metrics for all 14 models

## Expected Output

The test dataset should produce:
- Excel file with model accuracies
- Confusion matrix PNG image
- Log file with execution details
- JSON file with tuned parameters

All models should achieve high accuracy (>90%) since the species are well-separated.

## Alternative: Direct Command Line

If you prefer to test without the GUI:

```bash
cd Materials
python 02_Advanced_Morphometric_Classification.py
```

Then edit the `main()` function in the script to include only:
```python
datasets = [
    ('TestData', 'TestData/raw_data/test_data_morphologika.txt', 'testdata'),
]
```

## Troubleshooting

**"File not found" error**
- Make sure you're in the Morphometrics directory
- Verify `TestData/raw_data/test_data_morphologika.txt` exists

**Analysis takes too long**
- Something may be wrong with the installation
- Check console output for errors
- Verify Python 3.9+ is installed

**Results look wrong**
- Test dataset is synthetic with clear separation
- Accuracy should be >90% for most models

## File Format

The test data is in Morphologika format:

```
[individuals]         # Number of specimens
[landmarks]          # Number of landmarks per specimen
[dimensions]         # 2D or 3D
[names]             # Specimen names (parsed for species label)
[rawpoints]         # X Y Z coordinates for each landmark
```

Species are identified by the prefix in the specimen name:
- `Species_A_*` → Class A
- `Species_B_*` → Class B
- `Species_C_*` → Class C

## Performance Tips

1. **Fastest**: Use the test dataset for quick verification
2. **Compare**: Run Papionins next to see performance on real data
3. **Debug**: Test dataset helps isolate GUI vs script issues

## What to Expect

The 14 models tested:
1. XGBoost
2. LightGBM
3. CatBoost
4. Random Forest
5. Extra Trees
6. Gradient Boosting
7. Logistic Regression
8. Linear Discriminant Analysis
9. Support Vector Machine
10. Multi-layer Perceptron
11. K-Nearest Neighbors
12. Stacking Ensemble
13. Blending Ensemble
14. Weighted Voting Ensemble

All should achieve >90% accuracy on test data.

## Next Steps

After testing with TestData:

1. **Quick test**: Run with Papionins (~20 min)
2. **Real data**: Process your own datasets
3. **Full analysis**: Run all 7 provided datasets (2-5 days)

## Support

If the test dataset doesn't work:
1. Check Console Output tab in GUI
2. Read run.log.txt in results folder
3. Verify Python 3.9+ and dependencies installed
4. Check that test file exists at: `Materials/TestData/raw_data/test_data_morphologika.txt`

---

**This test dataset is designed to run in under 2 minutes and verify your setup is correct.**

Use it to quickly validate the GUI and pipeline before processing larger datasets.