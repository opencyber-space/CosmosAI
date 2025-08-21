import pandas as pd
import os

xlsx_path = "pod_metrics.xlsx"  # Replace with your actual file path
output_dir = "pod_metrics"  # Directory to save markdown files

os.makedirs(output_dir, exist_ok=True)

excel_file = pd.ExcelFile(xlsx_path)
for sheet_name in excel_file.sheet_names:
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    # Clean sheet name for filename
    safe_sheet_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in sheet_name).strip()
    md_filename = os.path.join(output_dir, f"{safe_sheet_name}.md")
    with open(md_filename, "w") as f:
        f.write(f"# {sheet_name}\n\n")
        f.write(df.to_markdown(index=False))