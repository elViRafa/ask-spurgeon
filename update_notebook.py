import json
from pathlib import Path

notebook_path = "fine_tuning/notebooks/Spurgeon_1500_Training_Colab.ipynb"
cells_path = "fine_tuning/notebooks/merge_cells.json"

# Load notebook
with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Load new cells
with open(cells_path, "r", encoding="utf-8") as f:
    new_cells = json.load(f)

# Append the new cells
nb["cells"].extend(new_cells)

# Save updated notebook
with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print(f"Successfully added {len(new_cells)} new cells to the notebook.")
print(f"Total cells now: {len(nb['cells'])}")
print("Notebook saved at:", notebook_path)
