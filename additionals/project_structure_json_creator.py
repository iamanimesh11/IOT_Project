import os
import json

# Folder names to ignore regardless of location
IGNORED_FOLDERS = {
    "config.loki_data",
    "grafana_data",
    "loki_data",
    "postgres_data",
    ".git",
    "__pycache__"
}

# Specific relative paths (from root) to ignore
IGNORED_PATHS = {
    "pipelines/airflow/logs"
}

def get_structure(path):
    structure = {}
    for root, dirs, files in os.walk(path):
        # Relative path from the root
        rel_path = os.path.relpath(root, path).replace("\\", "/")
        
        # Check if this entire path should be skipped
        if rel_path in IGNORED_PATHS:
            dirs[:] = []  # Don't go deeper
            continue
        
        # Filter out unwanted directories
        dirs[:] = [d for d in dirs if d not in IGNORED_FOLDERS and f"{rel_path}/{d}".strip("./") not in IGNORED_PATHS]
        
        structure[rel_path if rel_path != "." else "."] = files
    return structure

def write_structure_to_json(path, output_file="project_structure.json"):
    structure = get_structure(path)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(structure, f, indent=4)
    print(f"✅ Project structure saved to {output_file}")

def generate_tree_markdown(structure):
    def add_entry(path, files, tree_lines, prefix=""):
        parts = path.strip("./").split("/") if path != "." else []
        curr_indent = ""
        for depth, part in enumerate(parts):
            curr_path = "/".join(parts[:depth+1])
            tree_line = f"{'│   ' * depth}├── {part}"
            if tree_line not in tree_lines:
                tree_lines.append(tree_line)
        for idx, file in enumerate(files):
            branch = "└──" if idx == len(files) - 1 else "├──"
            tree_lines.append(f"{'│   ' * len(parts)}{branch} {file}")

    tree_lines = ["."]
    for path, files in sorted(structure.items()):
        add_entry(path, files, tree_lines)
    return "\n".join(tree_lines)
# Example usage:
if __name__ == "__main__":
    project_path = "."  # Your project root path
    project_path = os.path.dirname(os.getcwd())
    write_structure_to_json(project_path)
    with open("project_structure.json", "r", encoding="utf-8") as f:
        structure = json.load(f)
    tree_markdown = generate_tree_markdown(structure)
    with open("PROJECT_STRUCTURE.md", "w", encoding="utf-8") as f:
        f.write(tree_markdown)
    print("✅ Markdown-style tree saved to PROJECT_STRUCTURE.md")
