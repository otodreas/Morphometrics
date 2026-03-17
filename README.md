# Advanced Morphometric Classification
Interactive morphometrics interface

## Requirements
- Python>=3.14.2 TODO: ask Sara what python version she used
- `requirements.txt`
  - ```pip install -r requirements_linux.txt``` OR ```pip install -r requirements_mac.txt```
- MacOS:
  - OpenMP
    - ```brew install libomp```

## Summary
Advanced Morphometric Classification (AMC) is a Streamlit-based local host app built around Sara Behnamian's ML framework for species classification from Morphologika data.

## Download and run
1. Ensure Python is installed on the system
2. Install the latest release from GitHub
3. Create and activate viritual environment (recommended)
```sh
python -m venv .venv
source .venv/bin/activate
```
4. Install requirements
```sh
pip install -r requirements_linux.txt
# OR
pip install -r requirements_mac.txt
```
5. Launch the app
```sh
streamlit run amc.py
```

## Usage
AMC makes some assumptions about your data
1. It is a Morphologika file or multiple Morphologika files with consistent Morphologika headers
2. Species names are defined with binomial nomenclature split by space or underscore in the `[names]` section of the Morphologika file (i.e. `Homo Sapiens`, `homo_sapiens`, `H. Sapiens`, etc.)

It can also run for a long time and be demanding on the system. The progress can be tracked in the terminal from which the app was launched.

## Current features
AMC contains many useful features

### Parameter selection
The user may select values for parameters
- **random seed**
- **test size**: size of the test set relative to the size of the whole dataset
- **minimum number of samples**: minimum number of rows in the `[names]` section for a species
- **n_splits**: number of CV folds used

### Robust cancel button
Since the process can be slow and resource intensive, it is important to be able to cancel the runs from the app UI if the user realizes that they have passed too many Morphologika files to the program, for instance.

## Planned features

### Improve installation experience
Write a shell script that is installed straight from the most recent release that builds and activates an environment, installs dependencies, and runs the app right away. With more time, accommodate Docker build.

### "Intelligent" species selection
Rather than defining species as the first two words in the `[names]` section, a goal is to create logical partitions of the entries in `[names]` based on its contents. If not, accomodating user input for custom species partitioning is an alternative.

### Loading screen
A separate loading screen with a progress bar will visually highlight that a process is running.

### More parameter choices
Accommodation for more parameters to be chosen by the user can improve flexibility of AMC for differing research aims.

### Upload external configuration files
In the original script, the author used an external CSV file to aid in classification for certain Morphologika files. Accommodating this in AMC would allow for a wider range of analyses.

## Development notes

### Implementation of original script
We elected to call a modified version of Sara Behnamian's original script with `subprocess.Popen()` so that the program could be run similarly to how it was run by the author with minimal changes. Hardcoded variables were changed to commandline arguments. Lines that were removed from the original script are commented out in `src/classification.py` rather than deleted for clarity. A goal for the future is to clean up `src/classification.py` and provide a diff file to highlight the differences between the original classification script and the AMC-adapted script.

### Temporary directories
Files are copied over to a temporary directory and read from there since Streamlit cannot read files directly from the user's disk. The output files are also written to the same temporary directory, and the files are subsequently written to a zip archive to accommodate easy downloading. The temporary directory is always deleted.

### Reproducibility
Everything is reproducible thanks to the seeding, `XGBoost` and `MLP` currently run slightly differently in the app than with the standalone script. It is likely a seeding issue, since it's consistent across app runs and standalone script runs.
