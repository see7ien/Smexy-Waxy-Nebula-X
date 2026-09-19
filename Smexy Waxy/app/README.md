# Smexy-Waxy-LTA-Nebula-Hackathon

hello

## Setup

1. Clone the repository, then `cd` into this folder (`Smexy Waxy/app`) -- every command below
   (and the `Dockerfile`) assumes it's run from here.
2. Create a virtual environment:

	```powershell
	python -m venv .venv
	.\.venv\Scripts\Activate.ps1
	```

	On macOS or Linux:

	```bash
	python3 -m venv .venv
	source .venv/bin/activate
	```

3. Install Streamlit:

	```bash
	pip install streamlit
	```

4. Start the app:

	```bash
	streamlit run app.py
	```

The app will open at `http://localhost:8501`.

## Git Workflow

Create a branch before making changes:

```bash
git checkout -b feature/your-feature-name
```

Commit and push your work:

```bash
git add .
git commit -m "Describe your changes"
git push -u origin feature/your-feature-name
```

Do not commit `.venv`, cache files, or secrets.

## Deploying to Google Cloud (Cloud Run)

The app ships with a `Dockerfile` that installs `requirements.txt` and serves Streamlit
on Cloud Run's `$PORT`. From this folder (`Smexy Waxy/app`), with the
[gcloud CLI](https://cloud.google.com/sdk) authenticated against your project:

```bash
gcloud run deploy nebulax-ps3 --source . --region <your-region> --allow-unauthenticated
```

This builds the container from the `Dockerfile` and deploys it; Cloud Run gives you a
public HTTPS URL when it finishes. The bundled `data/ACV/ACV` training set ships inside
the image, so the ACV page's model trains itself on first request with no extra setup.