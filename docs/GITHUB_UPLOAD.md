# GitHub upload and first local launch (Mac)

1. Download and unzip `energy-trading-intelligence-github-ready.zip`.
2. Open Terminal and run `cd` followed by a space. Drag the unzipped `energy-trading-intelligence` folder into Terminal and press Enter.
3. Initialise and push to GitHub:

```bash
git init
git add .
git commit -m "Add energy trading intelligence project"
git branch -M main
gh auth status
gh repo create energy-trading-intelligence --public --source=. --remote=origin --push
```

If `gh auth status` says you are logged out, run `gh auth login` before the last command.

## Local dashboard

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL displayed by Streamlit.

## Rebuild the Excel analysis

```bash
python -m scripts.build_excel
```

Then open `excel/Energy_Risk_Analysis.xlsx` in Microsoft Excel. Edit yellow cells
on the `Assumptions` tab. All downstream formula outputs should recalculate.

## Learn it later

Read `docs/learning_path.md`, beginning with the price CSV and `src/analytics.py`.
Avoid claiming it is a live trading system, a futures-pricing model, or a forecast.
