# Changelog

All notable changes to this project following v1.0.6 will be documented in this file

## [v1.1.0] - 2026-03-23

TODO:
- Reproducibility fix: DONE
- Parameter logging to output
- README rewrite
- Progress streaming to UI: DONE
- Advanced config panel
- Screenshots for README

### Added

- `amc.py`: Classification run timer implemented. Shows run time, updates each second
- `amc.py`: Live log streaming during classification. Program polls `run.log.txt` every second and displays the last 5 lines in the UI
- `amc.py`: Cancel button now returns user to the start page immediately via `st.rerun()` instead of requiring a second interaction
- `amc.py`: Status indicators (running, complete, error) and a two-column layout for status and cancel button

### Changed

- `amc.py`: Crash message reflects the time after which `src/classification.py` crashed.
- `src/classification.py`: Arranged labels in alphabetical order in `get_species()` to ensure XGBoost and MLP produce identical results when the script is run standalone and with Streamlit
- `src/utils.py`: Merged stderr into stdout in `start_classification()` (`stderr=subprocess.PIPE` -> `stdout=subprocess.PIPE, stderr=subprocess.STDOUT`) so all subprocess output flows through a single pipe and is captured in `run.log.txt`

### Removed

- `amc.py`, `src/utils.py`, `src/classification.py`: Removed test size slider since the variable `TEST_SIZE` was not used anywhere in the classification script
