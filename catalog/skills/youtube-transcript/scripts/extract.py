#!/usr/bin/env python3
import sys
import subprocess
import shutil
import re
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract.py <youtube_url>")
        sys.exit(1)
        
    url = sys.argv[1]
    
    # 1. Check if yt-dlp is installed
    if not shutil.which("yt-dlp"):
        print("Error: yt-dlp is not installed. Please install it using 'pip install yt-dlp' or your package manager.")
        sys.exit(1)
        
    # Temporary directory for download
    work_dir = Path.cwd()
    
    # 2. Run yt-dlp
    cmd = [
        "yt-dlp",
        "--write-subs",
        "--write-auto-subs",
        "--skip-download",
        "--sub-lang", "ko,en",
        "--sub-format", "vtt",
        "-o", "%(id)s.%(ext)s",
        url
    ]
    
    try:
        result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        if "Private video" in e.stderr or "Video unavailable" in e.stderr:
            print("Error: The video is private or unavailable.")
        else:
            print(f"Error extracting subtitle: {e.stderr.strip()}")
        sys.exit(1)
        
    # Find the downloaded .vtt file
    vtt_files = list(work_dir.glob("*.vtt"))
    if not vtt_files:
        print("Error: No subtitles were found for this video.")
        sys.exit(1)
        
    # Use the first one
    vtt_file = vtt_files[0]
    
    # Parse VTT
    content = vtt_file.read_text(encoding="utf-8")
    
    # Simple VTT cleanup
    lines = content.splitlines()
    clean_lines = []
    for line in lines:
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line:
            continue
        if not line.strip():
            continue
        # Remove timestamps like <00:00:00.000>
        line = re.sub(r'<[^>]+>', '', line)
        clean_lines.append(line.strip())
        
    # Deduplicate sequential lines (common in youtube auto-generated VTT)
    dedup = []
    for line in clean_lines:
        if not dedup or dedup[-1] != line:
            dedup.append(line)
            
    print(" ".join(dedup))
    
    # Cleanup
    for f in vtt_files:
        f.unlink()

if __name__ == "__main__":
    main()
