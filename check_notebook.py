import json

notebook_path = "fine_tuning/notebooks/Spurgeon_1500_Training_Colab.ipynb"

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
print()
print("Last 5 cells (to check GGUF section):")
for i, cell in enumerate(nb['cells'][-5:]):
    src = "".join(cell.get("source", []))
    title = src.split("\n")[0][:85] if src else "(empty)"
    print(f"{len(nb['cells']) - 5 + i}. {title}")
