# 🏍️ MotoGP Performance Analyzer

Desktop application to download, clean and visualize public MotoGP results data, built in Python as a data analysis and machine learning portfolio project.

![Top 10 MotoGP riders by points, 2025](visualizations/2025/top10_points_MotoGP_2025.png)

![MotoGP Performance Analyzer](docs/screenshot.png)

---

## 📌 Overview

MotoGP Performance Analyzer collects public results data (seasons from 1949 to today, older seasons have limited data), turns it into clean tables with Pandas and shows rider, constructor and reliability charts in a desktop application.

Machine learning models for performance prediction are the next step of the project.

---

## ✨ Features

- Season selector from the current year back to 1949
- Parallel download with progress bar, cancel button, automatic retries and resume (files already downloaded are skipped)
- One-click conversion of the raw JSON files into a clean CSV
- Three charts for each category (MotoGP, Moto2, Moto3):
  - top riders by points, coloured by constructor
  - points by constructor
  - race non-finishes by team
- Official session documents (classifications, analysis, ...) opened on demand from the official website
- Local data management: delete the JSON or CSV files of one season, or of all seasons
- Machine learning section (coming soon)

---

## 🎯 Objectives

- [x] Collect public MotoGP data through an API
- [x] Clean and transform raw data using Pandas
- [x] Analyze rider, constructor and team performance
- [x] Create meaningful data visualizations
- [x] Build a desktop application to explore the results
- [ ] Identify performance patterns across circuits and races
- [ ] Develop machine learning models for performance prediction

---

## 🛠️ Technologies

- Python 3.12
- PySide6 (desktop interface)
- Pandas and NumPy (data cleaning and analysis)
- Matplotlib (charts)
- Requests (API access, with parallel downloads)
- Git & GitHub
- Planned: Scikit-learn (machine learning)

---

## 🚀 Getting started

### Windows

1. Install Python 3.12 from [python.org](https://www.python.org/downloads/) and tick **Add python.exe to PATH** in the installer.
2. Download or clone this repository.
3. Double-click `start.bat`. The first run creates a virtual environment and installs the libraries (it can take a few minutes, PySide6 is a large download). Later runs start immediately.

### Using the app

1. Choose a season in the left panel and press **Download JSON**.
2. When the download finishes, press **Convert JSON to CSV**.
3. Pick a category and explore the charts. The **PDF** button opens the official documents of a session.

The `data/` folders are created automatically on first use and are not versioned.

### Other systems (not tested)

`start.bat` is Windows-only. On other systems you can run the app from source:

```bash
python -m venv .venv
# activate the virtual environment, then:
pip install -r requirements.txt
python src/app/main.py
```

---

## 🧭 How it works

```text
MotoGP API  →  JSON files  →  Pandas cleaning  →  CSV files  →  charts in the app
               data/raw/<year>/                  data/processed/
```

- Downloads use up to 4 parallel requests with short delays and automatic retries.
- Each session is saved as one JSON file; the CSV of a season is built from all of them.

### Data cleaning decisions

- Test sessions and the MotoE category are excluded.
- `session_number` is missing for sessions without a number (practice, warm-up, sprint, race) and is kept as a real missing value.
- `position` is a nullable integer: riders who did not finish have no position.
- Speeds equal to `0` mean "not available" and become missing values.
- `best_lap_seconds` is parsed from the `MM:SS.mmm` text format.
- `points` stays a decimal number because shortened races award half points.

---

## 📂 Project Structure

```text
motogp-performance-analyzer/
│
├── src/
│   ├── app/                  # desktop application (PySide6)
│   └── visualization/
│       └── charts.py         # chart functions (Matplotlib)
│
├── visualizations/           # example charts (PNG)
├── data/                     # created automatically, not versioned
│   ├── raw/                  # downloaded JSON files
│   └── processed/            # clean CSV files
│
├── start.bat                 # one-click launcher (Windows)
├── requirements.txt
└── README.md
```

---

## ⚠️ Data source and disclaimer

- Data comes from an undocumented API used by the official MotoGP website. It is unofficial and may change or stop working without notice.
- This is an educational, non-commercial portfolio project, not affiliated with or endorsed by MotoGP or its rights holders.
- All data and documents belong to their rights holders. Downloaded files stay on your computer and are not part of this repository. Official PDF documents are opened from the official website on demand.

---

## Known limitations

- Seasons before 2002 have limited data: some charts may be empty.
- "Constructors" shows the sum of all riders' points per manufacturer, not the official constructors' standings.
- Non-finishes are absolute counts: teams with more riders have more chances to appear.
- Only finished events are downloaded.