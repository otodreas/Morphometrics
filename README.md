# Morphometrics
Interactive morphometrics interface

## Requirements
- Python 3.x TODO: ask Sara what python version she used
- `requirements.txt`
  - ```pip install -r requirements.txt```
- MacOS:
  - OpenMP
    - ```brew install libomp```

## Notes
`XGBoost` and `MLP` currently run slightly differently in the app than with the standalone script. It is likely a seeding issue, since it's consistent across app runs and standalone script runs.
