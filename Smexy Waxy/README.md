# Smexy Waxy — NebulaX 2026, Problem Statement 3

Team **Smexy Waxy**'s submission for PS3 (Train Condition Monitoring). All four subsystems
attempted: Door, ACV, Rail Corrugation, and SHM.

## What's in this folder

```
Smexy Waxy/
├── predictions.zip          # Item 2: door/acv/rail/shm_predictions.csv, one per subsystem
├── app/                      # Item 3: the app itself -- see app/README.md for setup & deploy
└── Optional_Items/           # Not required for scoring, but shows our work
    ├── <Subsystem>_Write_up.<md|pdf|docx>   # one write-up per subsystem
    └── <Subsystem>/model/     # the fitted model artifact for that subsystem
```

## The app

One Streamlit app (`app/`) covering all four subsystems, each behind its own page: upload
a raw data file (or several, or a zipped folder of them), see the model's visualization,
download a `*_predictions.csv` in the schema the spec requires. See `app/README.md` for
local setup and Google Cloud Run deployment instructions.

## Subsystem status

| Subsystem | Model | Notes |
|---|---|---|
| ACV | Single-feature logistic regression (`app/acv_features.py`, `app/acv_model.joblib`) | Retrained/validated in `app/acv_eda.ipynb`; see `Optional_Items/ACV_Write_up.md` |
| Door | Firth-penalised logistic regression (`app/door_features.py`) | Fitted artifact in `Optional_Items/Door/model/door_model.py`; see `Optional_Items/Door_Write_up.pdf` |
| Rail Corrugation | Embedded classifier (`app/rail_predict.py`) | Same file duplicated in `Optional_Items/Rail_Corrugation/model/`; see `Optional_Items/Rail_Corrugation_Write_up.docx` |
| SHM | Rainflow fatigue proxy + learned constant (`app/shm_features.py`) | Fitted artifact in `Optional_Items/SHM/model/shm_model.py`; see `Optional_Items/SHM_Write_up.pdf` |

## Not included here

Per the submission instructions, we did not include the organizers' raw datasets or the
`04_Example_Submission/` folder contents -- only our own code, models, and outputs.
