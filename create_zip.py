import zipfile
import os

files_to_zip = [
    "backend.py",
    "streamlit_app.py",
    "requirements.txt",
    ".env",
    "README.md",
    "start_project.bat"
]

zip_filename = "rag_project_complete.zip"

print(f"Creating {zip_filename}...")
with zipfile.ZipFile(zip_filename, 'w') as zipf:
    for file in files_to_zip:
        if os.path.exists(file):
            print(f"Adding {file}...")
            zipf.write(file)
        else:
            print(f"Warning: {file} not found!")

print("Zip created successfully.")
