import json
from pathlib import Path

notebook_path = "fine_tuning/notebooks/Spurgeon_1500_Training_Colab.ipynb"
new_cells_path = "fine_tuning/notebooks/new_gguf_cells.json"

# Load the notebook
with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Load the new cells we want to append
with open(new_cells_path, "r", encoding="utf-8") as f:
    new_cells = json.load(f)

# Append them
nb["cells"].extend(new_cells)

# Save the updated notebook
with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print(f"Successfully added GGUF conversion section.")
print(f"Total cells in notebook now: {len(nb['cells'])}")
print(f"Notebook saved to: {notebook_path}")