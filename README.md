# 🏃 Ultra Endurance Training Analysis

This project provides an end-to-end pipeline for analysing endurance training data from Garmin `.fit` files. It extracts raw activity data, builds structured summaries, and generates an interactive HTML report with insights into training load, fatigue, and running mechanics.

---

## 📂 Project Structure

├── preprocessing/   # Data extraction, cleaning, and orchestration
├── analysis/        # Core analytics (Foster load, ACWR, long run metrics)
├── reporting/       # HTML report generation
├── experiments/     # Experimental / exploratory analyses (e.g. recovery)
├── conda_envs/      # Conda environment specification
├── ../workouts/     # 📥 Place raw Garmin `.fit` files here
└── ../out/          # 📤 Auto-generated outputs (data + reports)

---

## 🚀 Quick Start

### 1. Add Your Data

Place your Garmin `.fit` files in:
`# 🏃 Ultra Endurance Training Analysis

This project provides an end-to-end pipeline for analysing endurance training data from Garmin `.fit` files. It extracts raw activity data, builds structured summaries, and generates an interactive HTML report with insights into training load, fatigue, and running mechanics.

---

## 📂 Project Structure

- `preprocessing/` → Data extraction, cleaning, and orchestration  
- `analysis/` → Core analytics (Foster load, ACWR, long run metrics)  
- `reporting/` → HTML report generation  
- `experiments/` → Experimental and exploratory analyses (e.g. recovery)  
- `conda_envs/` → Environment specification  
- `../workouts/` → **Place your raw `.fit` files here**  
- `../out/` → Generated outputs (intermediate + final report)

---

## 🚀 Quick Start

### 1. Add Your Data

Place your Garmin `.fit` files in:
`# 🏃 Ultra Endurance Training Analysis

This project provides an end-to-end pipeline for analysing endurance training data from Garmin `.fit` files. It extracts raw activity data, builds structured summaries, and generates an interactive HTML report with insights into training load, fatigue, and running mechanics.

---

## 📂 Project Structure

- `preprocessing/` → Data extraction, cleaning, and orchestration  
- `analysis/` → Core analytics (Foster load, ACWR, long run metrics)  
- `reporting/` → HTML report generation  
- `experiments/` → Experimental and exploratory analyses (e.g. recovery)  
- `conda_envs/` → Environment specification  
- `../workouts/` → **Place your raw `.fit` files here**  
- `../out/` → Generated outputs (intermediate + final report)

---

## 🚀 Quick Start

### 1. Add Your Data

Place your Garmin `.fit` files in:
`../workouts/`

---

### 2. Set Up Environment

Using the provided Makefile:

```bash
make setup-all
```
**This will:**

- Create or update the conda environment
- Install project dependencies in editable mode

### 3. Process Data

```bash
make process
```
**This step:**

- Extracts `.fit` files
- Builds structured activity data
- Generates a master summary dataset

### 4. Generate Report

```bash
make report
```
**This produces:**

`../out/training_report.html`

The report includes:

- Training load (Foster’s Strain)
- ACWR (Acute:Chronic Workload Ratio)
- Long run efficiency (Vertical Ratio)
- Cadence dynamics
- Integrated mechanics & physiology analysis

---

### 🧪 Experimental Analysis (Optional)

```bash
make recovery
```
This runs exploratory recovery analysis, including:

- Heart rate recovery curves
- Universal stitched recovery modelling
- Event-based (e.g. race day) comparisons

Outputs are visual (matplotlib) and intended for research, not reporting.

---

### 🧰 Environment Details

The project uses a conda environment defined in:

`conda_envs/garmin-fit.yml`

**Key dependencies:**
- Python 3.11
- pandas, numpy, scipy
- matplotlib, plotly
- garmin-fit-sdk
- h3

---

###  ⚙️ Non-Conda Setup (Alternative)

If you prefer not to use conda:

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```
2. Install dependencies manually:
```bash
pip install pandas numpy scipy matplotlib plotly openpyxl seaborn h3 garmin-fit-sdk
```
3. Install the project in editable mode:
```bash
pip install -e .
```
---

### 📊 Output Overview

After running the pipeline:

- `../out/master_workout_summary.tsv` → Cleaned activity summary
- `../out/<activity_id>/` → Per-activity processed data
- `../out/training_report.html` → Final interactive report
- `../out/global_pauses_capped/` → Recovery analysis snapshots

---

### Notes

- The pipeline is designed for ultra-endurance training analysis
- Metrics are most meaningful when interpreted together (load + mechanics + physiology)
- Experimental modules may change and are not guaranteed to be stable

---

### ✅ Recommended Workflow

```bash
make setup-all
make process
make report
# optional
make recovery
```