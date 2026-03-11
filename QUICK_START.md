# Quick Start Guide - Morphometric Classification GUI

## Installation (5 minutes)

### 1. Install Python
- Download Python 3.9+ from [python.org](https://www.python.org)
- During installation, **check "Add Python to PATH"**

### 2. Install Dependencies
Open a terminal/command prompt and run:

```bash
cd Morphometrics
pip install -r requirements_gui.txt
```

This installs PyQt6 and all ML libraries.

## Launch the GUI

### macOS/Linux
```bash
./launch_gui.sh
```

Or directly:
```bash
python3 morphometrics_gui.py
```

### Windows
```bash
python morphometrics_gui.py
```

The GUI window will open in a few seconds.

## Run Your First Analysis (30 minutes)

1. **Select a small dataset to test**
   - Go to "Datasets" tab
   - Uncheck all datasets except "Papionins" (smallest, ~20 min)

2. **Keep default settings**
   - Go to "Settings" tab
   - Leave all settings as default (don't change anything)

3. **Start analysis**
   - Click "Run Analysis" button
   - Watch progress in "Console Output" tab
   - You'll see: "Processing 1/1: Papionins"

4. **Wait for completion**
   - Takes ~20-30 minutes on a modern computer
   - Status bar shows: "✓ Script completed successfully!"
   - Results tab shows generated files

5. **View results**
   - Click "Open Results Folder"
   - Look for `Advanced_Classification_Results.xlsx`
   - Open with Excel, Numbers, or Google Sheets

## What You'll See

### Console Output
```
======================================================================
  02_ADVANCED MORPHOMETRIC CLASSIFICATION
  State-of-the-Art Ensemble Methods
======================================================================

  Output directory: .../02_Advanced_Morphometric_Classification_outputs

  Processing 1 datasets one at a time...

===============================================
  Processing dataset 1/1: Papionins
===============================================

  Loaded: 93 specimens, 31 landmarks
  
  [1] INDIVIDUAL MODELS (5-fold stratified CV on full dataset):
  --------------------------------------------------
    XGBoost: 0.9462 (12.3s)
    LightGBM: 0.9355 (5.1s)
    CatBoost: 0.9139 (8.2s)
    ...
```

### Excel Results
The `.xlsx` file contains:
- **Model Scores**: Accuracy of all 14 classifiers
- **Dataset Summary**: Number of specimens, landmarks, classes
- **Best Models**: Which ensemble performed best
- **Confusion Matrices**: Detailed classification results

### Confusion Matrix Image
PNG files show which classes were confused with each other.

## Processing All Datasets

Once you've verified it works with one dataset:

1. Go to "Datasets" tab
2. Check all datasets you want to process
3. Click "Run Analysis"
4. **WARNING**: This takes 2-5 days on a local computer!

**Recommendation**: Run overnight or on a powerful machine.

## Stopping Analysis

If you need to stop:
1. Click "Stop" button (appears when running)
2. Or close the window
3. Results processed so far are saved

## Troubleshooting

### "Python not found"
- Install Python 3.9+
- During installation, check "Add Python to PATH"
- Restart your terminal/command prompt

### "ModuleNotFoundError: No module named 'PyQt6'"
```bash
pip install -r requirements_gui.txt
```

### "Script not found"
- Make sure `02_Advanced_Morphometric_Classification.py` is in `Materials/` folder
- GUI should be in `Morphometrics/` directory

### Analysis runs very slowly
- First dataset is slower (initialization)
- Close other programs to free memory
- This is normal!

### Results folder empty
- Check status bar shows "✓ Completed"
- If error, check Console tab for messages
- May need to wait longer

## Next Steps

1. ✅ **First run**: Test with Papionins (20 min)
2. ✅ **Check results**: Open the Excel file
3. ✅ **Try other datasets**: Process one at a time
4. ✅ **Full analysis**: Process all 7 datasets (~2-5 days)

## Dataset Overview

| Name | Time | Size | Best For |
|------|------|------|----------|
| Papionins | 20 min | Small | Testing (START HERE) |
| Hominids | 15 min | Small | Quick test |
| Bears | 10 min | Very small | Quick test |
| Canids | 20 min | Medium | Good test |
| Wolves | 20 min | Medium | Full analysis |
| Quolls | 25 min | Medium | Full analysis |
| Aariz | 30 min | Large | Full analysis |

## Tips

💡 **Test first**: Always test with Papionins before full analysis  
💡 **Check settings**: Review "Settings" tab to understand what each parameter does  
💡 **Save output**: Copy the Excel results somewhere safe  
💡 **Read the logs**: `run.log.txt` has detailed timing information  
💡 **Hardware matters**: More RAM and SSD = faster processing  

## Need Help?

1. Check console output for error messages
2. Read `GUI_README.md` for detailed documentation
3. See `run.log.txt` in results folder for full logs
4. Verify all data files are present in `Materials/[Dataset]/raw_data/`

## What Gets Generated?

After analysis completes, you get:

```
02_Advanced_Morphometric_Classification_outputs/
├── Advanced_Classification_Results.xlsx     ← Open this!
├── Papionins_Confusion_Matrix_Best_Overall.png
├── run.log.txt
└── weighted_voting_tuned_params.json
```

**Open the Excel file to see all results!**

---

**Ready?** Click "Run Analysis" and watch your first morphometric classification! 🎯