# Smexy-Waxy-LTA-Nebula-Hackathon

hello

## Setup

1. Clone the repository and open it in VS Code.
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