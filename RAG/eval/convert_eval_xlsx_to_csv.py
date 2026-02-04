import pandas as pd
from pathlib import Path

# -----------------------------
# CONFIG
# -----------------------------
XLSX_PATH = Path(r"C:\Users\prast\Downloads\eval.xlsx")   # adjust if needed
OUTPUT_CSV = Path("strategy_eval.csv")

MESSAGE_COL = "message"
STRATEGY_COL = "strategy"

# -----------------------------
# LOAD EXCEL
# -----------------------------
xlsx = pd.ExcelFile(XLSX_PATH)

rows = []

for sheet in xlsx.sheet_names:
    # Only participant sheets (P1–P13)
    if not sheet.startswith("P"):
        continue

    df = pd.read_excel(xlsx, sheet_name=sheet)

    if MESSAGE_COL not in df.columns or STRATEGY_COL not in df.columns:
        print(f"Skipping sheet {sheet}: missing required columns")
        continue

    for _, row in df.iterrows():
        message = str(row[MESSAGE_COL]).strip()
        strategy = str(row[STRATEGY_COL]).strip()

        if not message or message.lower() == "nan":
            continue

        rows.append({
            "participant": sheet,
            "message": message,
            "gold_strategy": strategy
        })

# -----------------------------
# SAVE CSV
# -----------------------------
out_df = pd.DataFrame(rows)
out_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

print(f"Saved {len(out_df)} labeled messages to {OUTPUT_CSV}")
