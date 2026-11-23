#!/usr/bin/env python3
"""
Verification script to check if Level → grade conversion was successful.

This script:
1. Checks for any remaining "Level:" references
2. Verifies "grade:" is present
3. Validates JSON structure
4. Provides detailed statistics

Usage:
    python verify_conversion.py
"""

import json
from pathlib import Path
from collections import defaultdict

DATASET_DIR = Path("dataset_core")

def verify_file(filepath: Path) -> dict:
    """
    Verify a single JSONL file for proper conversion.
    
    Returns:
        dict: Verification results
    """
    results = {
        "filename": filepath.name,
        "total_lines": 0,
        "has_grade": 0,
        "has_level": 0,
        "has_profile": 0,
        "valid_json": 0,
        "invalid_json": 0,
        "issues": []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        results["total_lines"] = len(lines)
        
        for i, line in enumerate(lines, 1):
            try:
                # Parse JSON
                data = json.loads(line.strip())
                results["valid_json"] += 1
                
                # Check messages
                if "messages" in data:
                    for msg in data["messages"]:
                        if msg.get("role") == "system" and "content" in msg:
                            content = msg["content"]
                            
                            # Check for PROFILE section
                            if "[PROFILE]" in content:
                                results["has_profile"] += 1
                                
                                # Check for grade (good)
                                if "- grade:" in content:
                                    results["has_grade"] += 1
                                
                                # Check for Level (bad - should be converted)
                                if "- Level:" in content:
                                    results["has_level"] += 1
                                    results["issues"].append(
                                        f"Line {i}: Still contains '- Level:' (not converted)"
                                    )
                
            except json.JSONDecodeError:
                results["invalid_json"] += 1
                results["issues"].append(f"Line {i}: Invalid JSON")
            except Exception as e:
                results["issues"].append(f"Line {i}: Error - {e}")
    
    except Exception as e:
        results["issues"].append(f"File error: {e}")
    
    return results

def print_file_results(results: dict):
    """Print results for a single file."""
    print(f"\n📄 {results['filename']}")
    print(f"   Total lines:        {results['total_lines']}")
    print(f"   Valid JSON:         {results['valid_json']}")
    print(f"   Has [PROFILE]:      {results['has_profile']}")
    print(f"   Has 'grade:':       {results['has_grade']} ✅")
    print(f"   Has 'Level:':       {results['has_level']} {'❌' if results['has_level'] > 0 else '✅'}")
    
    if results["invalid_json"] > 0:
        print(f"   Invalid JSON:       {results['invalid_json']} ❌")
    
    if results["issues"]:
        print(f"\n   ⚠️  Issues found:")
        for issue in results["issues"][:5]:  # Show first 5 issues
            print(f"      - {issue}")
        if len(results["issues"]) > 5:
            print(f"      ... and {len(results['issues']) - 5} more")

def main():
    """Main verification process."""
    print("=" * 60)
    print("🔍 Dataset Verification: Level → grade")
    print("=" * 60)
    
    # Check if dataset directory exists
    if not DATASET_DIR.exists():
        print(f"❌ Error: Dataset directory not found: {DATASET_DIR}")
        return
    
    # Find all JSONL files
    jsonl_files = list(DATASET_DIR.glob("*.jsonl"))
    
    if not jsonl_files:
        print(f"❌ Error: No .jsonl files found in {DATASET_DIR}")
        return
    
    print(f"\n📂 Verifying {len(jsonl_files)} dataset files...")
    
    # Verify each file
    all_results = []
    total_stats = defaultdict(int)
    
    for filepath in sorted(jsonl_files):
        results = verify_file(filepath)
        all_results.append(results)
        
        # Aggregate stats
        for key in ["total_lines", "has_grade", "has_level", "has_profile", 
                    "valid_json", "invalid_json"]:
            total_stats[key] += results[key]
        total_stats["total_issues"] += len(results["issues"])
        
        print_file_results(results)
    
    # Print overall summary
    print("\n" + "=" * 60)
    print("📊 OVERALL SUMMARY")
    print("=" * 60)
    print(f"Files verified:         {len(jsonl_files)}")
    print(f"Total lines:            {total_stats['total_lines']}")
    print(f"Valid JSON:             {total_stats['valid_json']}")
    print(f"Invalid JSON:           {total_stats['invalid_json']}")
    print(f"\nProfile sections:       {total_stats['has_profile']}")
    print(f"Using 'grade:':         {total_stats['has_grade']} ✅")
    print(f"Still using 'Level:':   {total_stats['has_level']} {'❌' if total_stats['has_level'] > 0 else '✅'}")
    print(f"\nTotal issues:           {total_stats['total_issues']}")
    
    # Final verdict
    print("\n" + "=" * 60)
    if total_stats['has_level'] == 0 and total_stats['total_issues'] == 0:
        print("✅ VERIFICATION PASSED")
        print("   All 'Level:' references converted to 'grade:'")
        print("   No issues found")
    elif total_stats['has_level'] > 0:
        print("❌ VERIFICATION FAILED")
        print(f"   Found {total_stats['has_level']} unconverted 'Level:' references")
        print("   Run the conversion script again")
    else:
        print("⚠️  VERIFICATION COMPLETED WITH WARNINGS")
        print(f"   Conversion successful but {total_stats['total_issues']} issues found")
    print("=" * 60)

if __name__ == "__main__":
    main()
