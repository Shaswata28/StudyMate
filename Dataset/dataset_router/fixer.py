import json
import sys
import os

def fix_jsonl_file(file_path):
    # Create a new filename for the output (e.g., data.jsonl -> data_fixed.jsonl)
    base, ext = os.path.splitext(file_path)
    output_path = f"{base}_fixed{ext}"

    try:
        with open(file_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:

            count = 0
            for line_number, line in enumerate(infile, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    modified = False

                    # 1. Handle if "Level" is a top-level dictionary key
                    if "Level" in data:
                        data["grade"] = data.pop("Level")
                        modified = True

                    # 2. Handle if "Level" is inside the "messages" list (Common in OpenAI/Chat formats)
                    if "messages" in data and isinstance(data["messages"], list):
                        for msg in data["messages"]:
                            if "content" in msg and isinstance(msg["content"], str):
                                # Replace "- Level:" with "- grade:" specifically
                                if "- Level:" in msg["content"]:
                                    msg["content"] = msg["content"].replace("- Level:", "- grade:")
                                    modified = True
                                # Fallback: simplistic replacement if the format isn't strictly "- Level:"
                                elif "Level" in msg["content"] and "grade" not in msg["content"]:
                                    # Be careful here not to replace random words containing "Level"
                                    # This replaces explicitly "Level: "
                                    if "Level: " in msg["content"]:
                                        msg["content"] = msg["content"].replace("Level: ", "grade: ")
                                        modified = True

                    # Write the line to the new file
                    outfile.write(json.dumps(data) + '\n')
                    if modified:
                        count += 1

                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON on line {line_number}")

        print(f"Success! Processed {file_path}")
        print(f"Modified {count} lines.")
        print(f"Output saved to: {output_path}")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_jsonl.py <filename.jsonl>")
    else:
        # Process every file provided in arguments
        for f in sys.argv[1:]:
            fix_jsonl_file(f)
