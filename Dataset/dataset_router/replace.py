import random
import re

# The files you want to process
file_names = ['contextual.jsonl']

def randomize_level_match(match):
    """
    Callback function. 
    It takes the matched string (e.g., 'grade=High School' or 'grade=Casual')
    and returns 'grade=Bachelor' or 'grade=Masters' randomly.
    """
    new_level = random.choice(['Bachelor', 'Masters'])
    # match.group(1) preserves the "grade=" part
    return f"{match.group(1)}{new_level}"

for file_name in file_names:
    output_name = f"modified_{file_name}"
    
    try:
        with open(file_name, 'r', encoding='utf-8') as infile, \
             open(output_name, 'w', encoding='utf-8') as outfile:
            
            print(f"Processing {file_name}...")
            
            content = infile.read()
            
            # Regex Explanation:
            # (grade\s*=\s*)  -> Group 1: Matches 'grade=' with optional spaces.
            # [^.,;}\n"]+     -> Matches the value until a dot, comma, newline, etc.
            # This captures 'grade=High School', 'grade=Casual', 'grade=PhD', etc.
            regex_pattern = r'(grade\s*=\s*)[^.,;}\n"]+'
            
            modified_content = re.sub(regex_pattern, randomize_level_match, content)
            
            outfile.write(modified_content)
            
            print(f"Success! Created {output_name}")

    except FileNotFoundError:
        print(f"Error: Could not find {file_name}. Please check the file name and location.")