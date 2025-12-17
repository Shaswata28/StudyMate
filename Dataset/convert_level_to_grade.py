#!/usr/bin/env python3
"""
Script to convert 'Level:' to 'grade:' in all dataset files.

This updates the dataset format to match the backend terminology:
- Changes "Level: Bachelor" to "grade: Bachelor"
- Changes "Level: Masters" to "grade: Masters"

Usage:
    python convert_level_to_grade.py
"""

import json
import os
from pathlib import Path
import shutil
from datetime import datetime

# Configuration
DATASET_DIR = Path("dataset_core")
BACKUP_DIR = Path("dataset_core_backup")
DRY_RUN = False  # Set to True to preview changes without modifying files

def backup_datasets():
    """Create a backup of the dataset directory."""
    if BACKUP_DIR.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        old_backup = Path(f"dataset_core_backup_{timestamp}")
        shutil.move(str(BACKUP_DIR), str(old_backup))
        print(f"📦 Moved old backup to: {old_backup}")
    
    shutil.copytree(DATASET_DIR, BACKUP_DIR)
    print(f"✅ Created backup at: {BACKUP_DIR}")

def convert_line(line: str) -> tuple[str, bool]:
    """
    Convert a single line from Level to grade format.
    
    Returns:
        tuple: (converted_line, was_modified)
    """
    original = line
    
    # Replace "Level:" with "grade:" (case-sensitive)
    if "- Level:" in line:
        line = line.replace("- Level:", "- grade:")
        return line, True
    
    return line, False

def process_file(filepath: Path) -> dict:
    """
    Process a single JSONL file and convert Level to grade.
    
    Returns:
        dict: Statistics about the conversion
    """
    stats = {
        "total_lines": 0,
        "modified_lines": 0,
        "errors": 0
    }
    
    print(f"\n📄 Processing: {filepath.name}")
    
    try:
        # Read all lines
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        stats["total_lines"] = len(lines)
        modified_lines = []
        
        # Process each line
        for i, line in enumerate(lines, 1):
            try:
                # Parse JSON
                data = json.loads(line.strip())
                
                # Check if this is a valid message structure
                if "messages" not in data:
                    print(f"  ⚠️  Line {i}: No 'messages' field found")
                    modified_lines.append(line)
                    continue
                
                # Process each message in the conversation
                modified = False
                for msg in data["messages"]:
                    if msg.get("role") == "system" and "content" in msg:
                        original_content = msg["content"]
                        
                        # Convert Level to grade
                        if "- Level:" in original_content:
                            msg["content"] = original_content.replace("- Level:", "- grade:")
                            modified = True
                            stats["modified_lines"] += 1
                
                # Write back as JSON
                modified_lines.append(json.dumps(data, ensure_ascii=False) + "\n")
                
                if modified:
                    print(f"  ✓ Line {i}: Converted 'Level' to 'grade'")
                
            except json.JSONDecodeError as e:
                print(f"  ❌ Line {i}: JSON decode error - {e}")
                stats["errors"] += 1
                modified_lines.append(line)  # Keep original on error
            except Exception as e:
                print(f"  ❌ Line {i}: Unexpected error - {e}")
                stats["errors"] += 1
                modified_lines.append(line)  # Keep original on error
        
        # Write back to file (unless dry run)
        if not DRY_RUN:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(modified_lines)
            print(f"  💾 Saved changes to {filepath.name}")
        else:
            print(f"  🔍 DRY RUN - No changes written")
        
    except Exception as e:
        print(f"  ❌ Failed to process file: {e}")
        stats["errors"] += 1
    
    return stats

def main():
    """Main conversion process."""
    print("=" * 60)
    print("🔄 Dataset Conversion: Level → grade")
    print("=" * 60)
    
    # Check if dataset directory exists
    if not DATASET_DIR.exists():
        print(f"❌ Error: Dataset directory not found: {DATASET_DIR}")
        print(f"   Current directory: {os.getcwd()}")
        return
    
    # Find all JSONL files
    jsonl_files = list(DATASET_DIR.glob("*.jsonl"))
    
    if not jsonl_files:
        print(f"❌ Error: No .jsonl files found in {DATASET_DIR}")
        return
    
    print(f"\n📂 Found {len(jsonl_files)} dataset files:")
    for f in jsonl_files:
        print(f"   - {f.name}")
    
    # Create backup (unless dry run)
    if not DRY_RUN:
        print("\n" + "=" * 60)
        backup_datasets()
    else:
        print("\n🔍 DRY RUN MODE - No backups or changes will be made")
    
    # Process each file
    print("\n" + "=" * 60)
    print("🔧 Converting files...")
    print("=" * 60)
    
    total_stats = {
        "files_processed": 0,
        "total_lines": 0,
        "modified_lines": 0,
        "errors": 0
    }
    
    for filepath in sorted(jsonl_files):
        stats = process_file(filepath)
        total_stats["files_processed"] += 1
        total_stats["total_lines"] += stats["total_lines"]
        total_stats["modified_lines"] += stats["modified_lines"]
        total_stats["errors"] += stats["errors"]
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 CONVERSION SUMMARY")
    print("=" * 60)
    print(f"Files processed:    {total_stats['files_processed']}")
    print(f"Total lines:        {total_stats['total_lines']}")
    print(f"Lines modified:     {total_stats['modified_lines']}")
    print(f"Errors:             {total_stats['errors']}")
    
    if DRY_RUN:
        print("\n🔍 This was a DRY RUN - no files were modified")
        print("   Set DRY_RUN = False to apply changes")
    else:
        print(f"\n✅ Conversion complete!")
        print(f"   Backup saved at: {BACKUP_DIR}")
        print(f"   Original files updated in: {DATASET_DIR}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
