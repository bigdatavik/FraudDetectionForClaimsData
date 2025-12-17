#!/usr/bin/env python3
"""
Update notebook version and timestamp automatically before deployment.

This script:
1. Reads the current version from notebooks/01_fraud_agent.py
2. Increments the version (or uses git info)
3. Updates the date to current date
4. Updates the notebook file

Usage:
    python update_notebook_version.py [--bump-version] [--use-git]
"""

import re
import sys
from datetime import datetime
from pathlib import Path
import subprocess

def get_git_commit_date():
    """Get the last commit date from git"""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cd', '--date=format:%B %d, %Y'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return None

def get_current_date():
    """Get current date in format: December 14, 2024"""
    return datetime.now().strftime("%B %d, %Y")

def increment_version(version_str):
    """Increment version number: 2.1 -> 2.2"""
    match = re.match(r'(\d+)\.(\d+)', version_str)
    if match:
        major, minor = int(match.group(1)), int(match.group(2))
        return f"{major}.{minor + 1}"
    return version_str

def update_notebook_version(notebook_path, bump_version=False, use_git=False):
    """Update version and date in the notebook"""
    
    notebook_file = Path(notebook_path)
    if not notebook_file.exists():
        print(f"❌ Error: Notebook not found at {notebook_path}")
        return False
    
    # Read notebook content
    content = notebook_file.read_text()
    
    # Get current date
    if use_git:
        new_date = get_git_commit_date() or get_current_date()
    else:
        new_date = get_current_date()
    
    # Extract current version
    version_pattern = r'# MAGIC # ✨✨✨ VERSION ([\d.]+) - CREATED ([^✨]+)✨✨✨'
    match = re.search(version_pattern, content)
    
    if not match:
        print("❌ Error: Could not find version pattern in notebook")
        return False
    
    current_version = match.group(1)
    current_date = match.group(2).strip()
    
    # Determine new version
    if bump_version:
        new_version = increment_version(current_version)
    else:
        new_version = current_version
    
    # Update the version header
    old_header = f"# MAGIC # ✨✨✨ VERSION {current_version} - CREATED {current_date} ✨✨✨"
    new_header = f"# MAGIC # ✨✨✨ VERSION {new_version} - CREATED {new_date} ✨✨✨"
    
    content = content.replace(old_header, new_header)
    
    # Update the "Last Updated" field
    last_updated_pattern = r'# MAGIC \*\*📅 Last Updated:\*\* [^\n]+'
    new_last_updated = f'# MAGIC **📅 Last Updated:** {new_date}'
    content = re.sub(last_updated_pattern, new_last_updated, content)
    
    # Update the version field
    version_field_pattern = r'# MAGIC \*\*🔧 Version:\*\* [^\n]+'
    new_version_field = f'# MAGIC **🔧 Version:** {new_version} - WITH ARCHITECTURE DIAGRAMS'
    content = re.sub(version_field_pattern, new_version_field, content)
    
    # Write updated content
    notebook_file.write_text(content)
    
    print("=" * 70)
    print("✅ NOTEBOOK VERSION UPDATED")
    print("=" * 70)
    print(f"📓 Notebook: {notebook_path}")
    if bump_version and new_version != current_version:
        print(f"🔢 Version: {current_version} → {new_version}")
    else:
        print(f"🔢 Version: {new_version} (unchanged)")
    print(f"📅 Date: {current_date} → {new_date}")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Update notebook version and date')
    parser.add_argument('--bump-version', action='store_true', 
                        help='Increment the version number')
    parser.add_argument('--use-git', action='store_true',
                        help='Use git commit date instead of current date')
    parser.add_argument('--notebook', default='notebooks/01_fraud_agent.py',
                        help='Path to notebook file (default: notebooks/01_fraud_agent.py)')
    
    args = parser.parse_args()
    
    success = update_notebook_version(
        args.notebook,
        bump_version=args.bump_version,
        use_git=args.use_git
    )
    
    sys.exit(0 if success else 1)

