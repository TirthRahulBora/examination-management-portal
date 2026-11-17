import os
import sys
import re
import zipfile
from pathlib import Path

def get_pdf_page_count(pdf_path):
    with open(pdf_path, 'rb') as f:
        content = f.read()
    # Find all /Type /Page (excluding /Pages)
    pages = re.findall(rb'/Type\s*/Page\b', content)
    return len(pages)

def package_submission(project_dir, zip_destinations):
    project_dir = Path(project_dir).resolve()
    top_folder_name = "examination-management-portal"

    # Exclusion patterns
    EXCLUDE_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', '.idea', '.vscode'}
    EXCLUDE_EXTS = {'.pyc', '.pyo', '.pyd'}
    EXCLUDE_FILES = {'emp.db', '.DS_Store'}

    # Collect files
    files_to_pack = []
    for root, dirs, files in os.walk(project_dir):
        rel_root = Path(root).relative_to(project_dir)
        
        # Modify dirs in-place to avoid descending into excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        # Check if root is inside an excluded directory
        parts = rel_root.parts
        if any(p in EXCLUDE_DIRS for p in parts):
            continue

        for f in files:
            file_path = Path(root) / f
            rel_file = file_path.relative_to(project_dir)

            # Skip exclude files/extensions
            if file_path.suffix in EXCLUDE_EXTS:
                continue
            if f in EXCLUDE_FILES:
                continue
            if 'instance' in parts and file_path.suffix == '.db':
                continue
            if f.endswith('.zip') and ('Submission' in f or 'portal' in f):
                # Skip existing zip archives
                continue

            arcname = f"{top_folder_name}/{rel_file.as_posix()}"
            files_to_pack.append((file_path, arcname))

    print(f"[PACKAGE] Found {len(files_to_pack)} clean files to archive.")

    for dest in zip_destinations:
        dest_path = Path(dest).resolve()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if dest_path.exists():
            dest_path.unlink()

        with zipfile.ZipFile(dest_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path, arcname in files_to_pack:
                zf.write(file_path, arcname)

        size_mb = dest_path.stat().st_size / (1024 * 1024)
        print(f"[PACKAGE] Successfully created archive: {dest_path} ({size_mb:.2f} MB)")

def audit_zip(zip_path):
    print(f"\n[AUDIT] Validating archive: {zip_path}")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        infolist = zf.infolist()
        total_files = len(infolist)
        total_size = sum(info.file_size for info in infolist) / (1024 * 1024)
        compressed_size = sum(info.compress_size for info in infolist) / (1024 * 1024)

        top_levels = set()
        violations = []

        for info in infolist:
            name = info.filename
            parts = name.split('/')
            if parts:
                top_levels.add(parts[0])

            # Check for forbidden artifacts
            if any(forbidden in name for forbidden in ['.git/', '.venv/', 'venv/', '__pycache__/', '.pytest_cache/']):
                violations.append(f"Forbidden directory in archive: {name}")
            if name.endswith('.pyc') or name.endswith('.db'):
                violations.append(f"Forbidden binary/cached file in archive: {name}")

        print(f"  • Total archived files: {total_files}")
        print(f"  • Uncompressed size: {total_size:.2f} MB")
        print(f"  • Compressed ZIP size: {compressed_size:.2f} MB")
        print(f"  • Top-level folders detected: {top_levels}")

        if len(top_levels) != 1 or "examination-management-portal" not in top_levels:
            print("  [ERROR] Archive must contain exactly one top-level directory named 'examination-management-portal'!")
            return False

        if violations:
            print(f"  [ERROR] Detected {len(violations)} rule violations in archive:")
            for v in violations[:10]:
                print(f"    - {v}")
            return False

        print("  [AUDIT PASS] Single top-level folder confirmed. Zero forbidden files detected.")
        return True

if __name__ == '__main__':
    project_root = Path(__file__).resolve().parent.parent
    pdf_file = project_root / 'EMP_Final_Submission_Report.pdf'

    print("==================================================")
    print("  EMP Final Submission Packaging & Verification   ")
    print("==================================================")

    # 1. PDF Verification
    if pdf_file.exists():
        pages = get_pdf_page_count(pdf_file)
        print(f"[PDF AUDIT] Document: {pdf_file.name}")
        print(f"[PDF AUDIT] Total Page Count: {pages}")
        if pages <= 5:
            print(f"[PDF AUDIT PASS] Complies with IIT Madras page limit (<= 5 pages). Current: {pages} pages.")
        else:
            print(f"[PDF AUDIT WARNING] Exceeds 5 pages limit: {pages} pages.")
    else:
        print("[PDF AUDIT ERROR] Report PDF not found!")

    # 2. Package Zip
    downloads_dir = Path(os.environ.get('USERPROFILE', 'C:/Users/tirth')) / 'Downloads'
    destinations = [
        project_root / 'EMP_Final_Submission.zip',
        downloads_dir / 'EMP_Final_Submission.zip'
    ]

    package_submission(project_root, destinations)

    # 3. Audit primary archive
    audit_ok = audit_zip(destinations[0])
    if audit_ok:
        print("\n[SUCCESS] Final submission package is fully compliant and ready.")
    else:
        print("\n[FAILURE] Submission packaging audit failed.")
