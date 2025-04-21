import os

def find_text_in_files(search_text, extensions=None):
    results = []
    project_path = "."  # Your project root path
    parent_dir = os.path.dirname(os.getcwd())
    

    for root, dirs, files in os.walk(parent_dir):
        for filename in files:
            if extensions:
                if not filename.lower().endswith(tuple(extensions)):
                    continue

            file_path = os.path.join(root, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line_num, line in enumerate(lines, start=1):
                        if search_text in line:
                            results.append((file_path, line_num, line.strip()))
            except (UnicodeDecodeError, PermissionError) as e:
                print(f"Skipped: {file_path} ({e})")

    return results

# Example usage
if __name__ == "__main__":
    search_term = input("Enter the text to search for: ")

    ext_input = input("Enter file extensions to include (e.g., py,txt,log), or press Enter for all: ")
    extensions = [e.strip().lower() for e in ext_input.split(",")] if ext_input else None

    matches = find_text_in_files(search_term, extensions)

    if matches:
        print("\nMatches found:")
        for file_path, line_num, line_content in matches:
            print(f"[{file_path}] Line {line_num}: {line_content}")
    else:
        print("No matches found.")
