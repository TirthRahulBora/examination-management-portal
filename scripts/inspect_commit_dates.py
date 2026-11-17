import subprocess
from collections import Counter

res = subprocess.run(
    ["git", "log", "--pretty=format:%ad", "--date=short"],
    capture_output=True,
    text=True,
    check=True
)

dates = res.stdout.strip().split("\n")
counts = Counter(dates)

print("Commit Date Histogram (from earliest to latest):")
for d in sorted(counts.keys()):
    print(f"  {d}: {counts[d]} commits")

print(f"\nTotal commits: {len(dates)}")
