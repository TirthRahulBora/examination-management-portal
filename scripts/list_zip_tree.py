import zipfile
from pathlib import Path

def print_zip_tree(zip_path):
    print(f"\nArchive: {Path(zip_path).name}")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        namelist = sorted(zf.namelist())
        
        # Categorize
        directories = set()
        files = []
        for name in namelist:
            p = Path(name)
            for parent in p.parents:
                if str(parent) != '.':
                    directories.add(str(parent).replace('\\', '/'))
            files.append(name)
            
        print("Total files inside ZIP:", len(files))
        print("\nPrimary Directory Structure:")
        top_dirs = sorted({name.split('/')[0] for name in namelist})
        print(f"Top-level directory: {top_dirs}")
        
        print("\nSubdirectories and representative entries:")
        sub_dirs = sorted({"/".join(name.split('/')[:2]) for name in namelist if '/' in name})
        for sd in sub_dirs:
            count = len([f for f in namelist if f.startswith(sd + '/')])
            print(f"  └── {sd}/ ({count} files)")

if __name__ == '__main__':
    project_root = Path(__file__).resolve().parent.parent
    print_zip_tree(project_root / 'EMP_24f3002455.zip')
