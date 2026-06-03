import json

notebook_path = "fine_tuning/notebooks/Spurgeon_1500_Training_Colab.ipynb"

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Total cells in notebook: {len(nb['cells'])}")
print("\n=== Last 6 cell titles (to confirm GGUF section) ===")

for i, cell in enumerate(nb["cells"][-6:]):
    source = "".join(cell.get("source", []))
    first_line = source.split("\n")[0][:90] if source else "(empty cell)"
    print(f"{len(nb['cells']) - 6 + i + 1}. {first_line}")
