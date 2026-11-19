#!/usr/bin/env bash
# Rebuild the whole project from scratch
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-$(command -v python3 || command -v python)}"
"$PY" scripts/generate_data.py
"$PY" scripts/clean_data.py
"$PY" scripts/run_sql.py > /dev/null
jupyter nbconvert --to notebook --execute --inplace notebooks/sales_analysis.ipynb
"$PY" scripts/build_excel_report.py
"$PY" scripts/build_powerbi_model.py
"$PY" scripts/build_dashboard.py
echo "Done."
