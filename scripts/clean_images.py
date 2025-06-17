#!/usr/bin/env python3

from pathlib import Path

def clean_images():
    """Clean the images/ tree while preserving structure.
    
    Removes generated assets (.png, .jpg, .jpeg, .mp4) from:
    - Root of images/ directory
    - Non-critical subdirectories (completely)
    - Critical directories (only media files, keeping JSONs)
    """
    CRITICAL_DIRS = {'approved', 'ranked', 'selected_for_video', 'pending', 'rejected'}
    
    images_path = Path('images')
    if not images_path.exists():
        print("Images directory does not exist")
        return
    
    files_removed = 0
    
    for p in images_path.iterdir():
        if p.is_file() and p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.mp4'}:
            print(f"Removing file: {p}")
            p.unlink()
            files_removed += 1
        elif p.is_dir():
            if p.name not in CRITICAL_DIRS:
                print(f"Removing non-critical directory: {p}")
                # Remove entire non-critical directory
                import shutil
                shutil.rmtree(p)
            else:
                # Inside critical dirs, remove generated assets but keep jsons
                print(f"Cleaning critical directory: {p}")
                for f in p.rglob('*'):
                    if f.is_file() and f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.mp4'}:
                        print(f"  Removing: {f}")
                        f.unlink()
                        files_removed += 1
    
    print(f"\nCleaning complete. Removed {files_removed} files.")

if __name__ == "__main__":
    clean_images()

