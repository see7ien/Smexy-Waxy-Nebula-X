# ACV — Refrigerant-Leak Localization: Methods

- Checked the actual column headers on every file rather than assuming a schema. 5 of
  6 training files (and the real test file) share a common 8-parameter layout; one
  training file uses an entirely different ~60-parameter layout and was excluded from
  training since it doesn't carry the columns our feature needs.

- One engineered feature: for each car, mean(actual indoor temperature − its own
  cooling setpoint) while its running mode shows active cooling, with sensor-flagged
  `Invalid` rows excluded first. Refrigerant undercharge reduces cooling capacity, so a
  leaking car should sit further above its own setpoint than a healthy peer even while
  trying to cool.

- Tried a second feature (duty-cycle / time spent actively cooling) and dropped it — it
  looked fine in-sample but made validation *worse*, since duty cycle barely varies
  between cars, so tiny noise there produced large, misleading peer comparisons.

- Each car's feature value is converted to a robust peer z-score (median/MAD) against
  the other cars in the same file only, since absolute temperature levels shift with
  weather and schedule between files.

- Model: a single-feature logistic regression on that z-score, outputting a calibrated
  probability that each car is the one with the leak — used to rank the cars.

- Validated with leave-one-file-out cross-validation (5 usable files): mean rank-decay
  score of **1.000**, every held-out file ranks the true faulty car 1st.
  
- Implemented in Python with pandas and scikit-learn. The full workflow — audit,
  feature derivation, training, and validation — lives in `app/acv_eda.ipynb`, which
  also saves the fitted model as `app/acv_model.joblib` for the deployed app to load.
