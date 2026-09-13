# SANJEEVNI ML Models Directory

Place the trained model file here:
`Sanjeevni_FINAL_Stress_Model.pkl`

## Model Contract:
- **Input**: 1D array of 44 features extracted across the 30-second rolling window at 25 Hz.
- **Expected Features**: See `app.ml.metadata.FEATURE_NAMES`.
- **Output**: Predicts stress class ("LOW", "MODERATE", "HIGH") or continuous stress probability/score (0.0 to 100.0).

If the model file is not present, the backend cleanly signals:
`MODEL_UNAVAILABLE`
without failing or generating fake predictions.
