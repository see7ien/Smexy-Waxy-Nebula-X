# Smexy Waxy — NebulaX 2026, Problem Statement 3 (Train Condition Monitoring)

**Live app: https://smexy-waxy-nebula-x-ps3-232746490322.asia-southeast1.run.app**

One web app covering all four PS3 subsystems. Pick a subsystem, upload your raw data
(a file, several files, or a zipped folder), see the model's visualisation, and download
the predictions as a CSV in the format the spec requires.

| Subsystem | What you upload | What you get |
|---|---|---|
| **Door** | One raw door-sensor CSV (20 ms samples) | Every open/close segment classified Normal / Abnormal resistance, abnormal rate by Open vs Close, `door_predictions.csv` |
| **ACV** | One or more ACV telemetry workbooks (`.xlsx`) | Cars ranked from most- to least-likely to have the refrigerant leak, `acv_predictions.csv` |
| **Rail Corrugation** | Raw axle-box vibration/shock CSVs | Each file classified Normal / Side I / Side II, distribution chart, `rail_predictions.csv` |
| **SHM** | Raw stress time-series CSVs | Predicted cumulative fatigue damage per file, `shm_predictions.csv` |

Any filename is accepted — files are checked by content, not by name.

## Using the app

1. Open the live app and choose a subsystem from the home page.
2. Upload your data. For Rail Corrugation, press **Run predictions** once the files have
   finished uploading.
3. Review the charts and the **Predictions Preview** table.
4. Press the red **Download predictions.csv** button.

## Repository layout

```
Smexy Waxy/
├── app/              # the Streamlit app (source, models, Dockerfile) -- see app/README.md
├── Optional_Items/   # write-ups and fitted model artifacts, per subsystem
├── predictions.zip   # our submitted prediction CSVs
└── README.md         # overview of the submission folder
```

## Run it yourself

```bash
cd "Smexy Waxy/app"
pip install -r requirements.txt
streamlit run app.py
```

Deployment to Google Cloud Run is covered in [`Smexy Waxy/app/README.md`](Smexy%20Waxy/app/README.md).
