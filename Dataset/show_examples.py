#!/usr/bin/env python3
"""
Show example conversions from the dataset.

This script displays random examples from each dataset file
to verify the conversion visually.

Usage:
    python show_examples.py
"""

import json
import random
from pathlib import Path

DATASET_DIR = Path("dataset_core")

def show_example(filepath: Path, num_examples: int = 2):
    """Show random examples from a file."""
    print(f"\n{'='*60}")
    print(f"📄 {filepath.name}")
    print('='*60)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Get random samples
        sample_lines = random.sample(lines, min(num_examples, len(lines)))
        
        for i, line in enumerate(sample_lines, 1):
            try:
                data = json.loads(line.strip())
                
                if "messages" in data:
                    system_msg = data["messages"][0]
                    if system_msg.get("role") == "system":
                        content = system_msg["content"]
                        
                        # Extract just the PROFILE section
                        if "[PROFILE]" in content:
                            profile_start = content.find("[PROFILE]")
                            profile_end = content.find("\n\n", profile_start)
                            if profile_end == -1:
                                profile_end = content.find("[COURSE MATERIALS]", profile_start)
                            
                            profile_section = content[profile_start:profile_end].strip()
                            
                            print(f"\nExample {i}:")
                            print("-" * 40)
                            print(profile_section)
                            
                            # Highlight the grade field
                            if "- grade:" in profile_section:
                                print("\n✅ Contains 'grade:' (converted)")
                            if "- Level:" in profile_section:
                                print("\n❌ Still contains 'Level:' (NOT converted)")
                        else:
                            print(f"\nExample {i}: No [PROFILE] section")
                
            except Exception as e:
                print(f"\nExample {i}: Error - {e}")
    
    except Exception as e:
        print(f"Error reading file: {e}")

def main():
    """Main function."""
    print("=" * 60)
    print("🔍 Dataset Conversion Examples")
    print("=" * 60)
    print("\nShowing random examples from each dataset file...")
    print("Look for '- grade:' instead of '- Level:'")
    
    # Find all JSONL files
    jsonl_files = sorted(DATASET_DIR.glob("*.jsonl"))
    
    if not jsonl_files:
        print(f"\n❌ No .jsonl files found in {DATASET_DIR}")
        return
    
    # Show examples from each file
    for filepath in jsonl_files:
        show_example(filepath, num_examples=2)
    
    print("\n" + "=" * 60)
    print("✅ Examples displayed")
    print("=" * 60)
    print("\nKey points to verify:")
    print("  ✓ All examples should show '- grade:' not '- Level:'")
    print("  ✓ Format should be: '- grade: Bachelor' or '- grade: Masters'")
    print("  ✓ JSON structure should be intact")
    print("\nRun 'python verify_conversion.py' for full validation")
    print("=" * 60)

if __name__ == "__main__":
    main()
