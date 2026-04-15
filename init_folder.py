import os

folders = [
    "Python_Basic",
    "GIS_Tools",
    "Remote_Sensing",
    "AI_Learning",
    "Project",
    "Notes"
]
for folder in folders:
    os.makedirs(folder, exist_ok=True)

print("All folders created successfully.")
