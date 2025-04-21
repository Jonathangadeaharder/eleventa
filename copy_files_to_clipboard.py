import os
from pathlib import Path
import pyperclip

# Set the root directory (current working directory)
root_dir = Path(os.getcwd())

# Define folders to ignore
ignore_dirs = {'venv', '__pycache__', 'alembic'}

def is_ignored(path: Path):
    parts = set(path.parts)
    return bool(parts & ignore_dirs)

# Collect all .py and .md files, ignoring specified folders
file_paths = [
    f for f in root_dir.rglob('*')
    if f.suffix in {'.py', '.md'} and not is_ignored(f.relative_to(root_dir))
]

print(f"Found {len(file_paths)} files.")

sections = []

for file_path in sorted(file_paths):
    rel_path = file_path.relative_to(root_dir)
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        content = f"[Error reading file: {e}]"
    section = f"## {rel_path}\n\n" + content + "\n\n"
    sections.append(section)

final_text = '\n'.join(sections)

try:
    pyperclip.copy(final_text)
    print("Copied to clipboard successfully.")
except Exception as e:
    print(f"Failed to copy to clipboard: {e}")

# Always save to a file as a fallback
with open("collected_files_output.txt", "w", encoding="utf-8") as f:
    f.write(final_text)
print("Saved output to collected_files_output.txt")
