
import os
import re
from pathlib import Path

PROJECT_ROOT = Path("/home/jamest/Desktop/dev/mycraft")

def get_md_files():
    return list(PROJECT_ROOT.rglob("*.md"))

def verify_file_exists(ref_path, source_file):
    # Handle absolute file:// paths
    if ref_path.startswith("file://"):
        path = Path(ref_path.replace("file://", ""))
    # Handle absolute paths starting with /
    elif ref_path.startswith("/"):
        path = Path(ref_path)
    # Handle relative paths
    else:
        path = (source_file.parent / ref_path).resolve()
    
    if not path.exists():
        print(f"❌ BROKEN LINK: {source_file.relative_to(PROJECT_ROOT)} -> {ref_path}")
        return False
    return True

def scan_file(file_path):
    content = file_path.read_text()
    # Match [text](path)
    links = re.findall(r'\[.*?\]\((.*?)\)', content)
    
    broken_count = 0
    for link in links:
        # Skip http/https links
        if link.startswith("http"):
            continue
        # Skip anchor links
        if link.startswith("#"):
            continue
            
        # Strip anchors from file paths
        clean_link = link.split('#')[0]
        if not clean_link:
            continue
            
        if not verify_file_exists(clean_link, file_path):
            broken_count += 1
            
    return broken_count

def main():
    print("🔍 Verifying documentation links...")
    files = get_md_files()
    total_broken = 0
    
    for file in files:
        if "venv" in str(file):  # Skip venv
            continue
        total_broken += scan_file(file)
        
    if total_broken == 0:
        print("✅ All internal links are valid!")
        exit(0)
    else:
        print(f"❌ Found {total_broken} broken links.")
        exit(1)

if __name__ == "__main__":
    main()
