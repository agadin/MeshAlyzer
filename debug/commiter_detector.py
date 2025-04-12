import subprocess
import datetime
import re
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.sankey import Sankey


# ---------- Step 1: Extract Commit Data ----------
def get_git_commit_data(n_commits=50):
    """
    Get the latest n_commits from your git log.
    Uses a custom pretty format: commit SHA, author name, commit date (ISO), and commit message.
    """
    try:
        # Use --date=iso so we get ISO-formatted date strings (e.g., 2025-04-01 12:34:56 +0000)
        cmd = ["git", "log", f"-n{n_commits}", "--pretty=format:%H|%an|%ad|%s", "--date=iso"]
        output = subprocess.check_output(cmd).decode("utf-8", errors="replace")
    except Exception as e:
        print("Error running git log. Make sure you're in a git repository.")
        raise e

    commits = []
    for line in output.strip().split("\n"):
        # Expecting 4 parts separated by "|"
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        sha, author, date_str, message = parts
        try:
            # date_str may contain a timezone offset; fromisoformat can handle it in Python 3.7+
            dt = datetime.datetime.fromisoformat(date_str.strip())
        except Exception as e:
            dt = None
        commits.append({
            "sha": sha,
            "author": author,
            "date": dt,
            "message": message.strip()
        })
    return commits


# Get the latest 100 commits
commits = get_git_commit_data(100)

# ---------- Step 2: Print Commits in a Better Format ----------
print("Recent Commits:")
for commit in commits:
    date_formatted = commit["date"].strftime("%Y-%m-%d %H:%M:%S") if commit["date"] else "N/A"
    print(f"{commit['sha'][:7]} | {commit['author']} | {date_formatted} | {commit['message']}")

# ---------- Step 3: Aggregate Data for Visualizations ----------

# (a) Number of commits per author
author_commit_counts = defaultdict(int)
for commit in commits:
    author_commit_counts[commit["author"]] += 1


# (b) Categorize commits based on a simple heuristic.
#     You can modify this if you use a specific commit message convention.
def categorize_commit(message):
    msg_lower = message.lower()
    if msg_lower.startswith("feat"):
        return "Feature"
    elif msg_lower.startswith("fix"):
        return "Fix"
    elif msg_lower.startswith("docs"):
        return "Documentation"
    elif msg_lower.startswith("chore"):
        return "Chore"
    elif msg_lower.startswith("refactor"):
        return "Refactor"
    else:
        return "Other"


# Build a nested dictionary: {author: {commit_type: count}}
author_type_counts = defaultdict(lambda: defaultdict(int))
for commit in commits:
    category = categorize_commit(commit["message"])
    author_type_counts[commit["author"]][category] += 1

# ---------- Step 4: Visualize the Data ----------

# (a) Bar Chart: Number of Commits per Author
plt.figure(figsize=(10, 6))
authors = list(author_commit_counts.keys())
counts = [author_commit_counts[a] for a in authors]
plt.bar(authors, counts)
plt.xlabel("Author")
plt.ylabel("Number of Commits")
plt.title("Commits per Author")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# (b) Timeline Scatter Plot: Commit Times by Author
plt.figure(figsize=(12, 6))
for commit in commits:
    if commit["date"]:
        plt.scatter(commit["date"], commit["author"], alpha=0.7)
plt.xlabel("Commit Time")
plt.ylabel("Author")
plt.title("Commit Timeline by Author")
plt.gcf().autofmt_xdate()
plt.tight_layout()
plt.show()

# (c) Sankey/Flow Diagram: Breakdown of Commit Types per Author
# This simple example creates a separate Sankey diagram for each author.
# The diagram shows how many commits of each type the author has.
for author, type_counts in author_type_counts.items():
    flows = []  # Flow values are just the counts of each commit type.
    labels = []  # Labels include type and count.
    for commit_type, count in type_counts.items():
        flows.append(count)
        labels.append(f"{commit_type}: {count}")

    # Note: Matplotlib’s Sankey is fairly basic; here we create one sankey diagram per author.
    sankey = Sankey(unit=None, scale=1.0, offset=0.2)
    # The flows array here is for outflows (all positive)
    # We wrap it in a list so we can set it on one sankey diagram.
    sankey.add(flows=flows, labels=labels, orientations=[0] * len(flows), trunklength=2.0)
    sankey.finish()
    plt.title(f"Commit Type Breakdown for {author}")
    plt.tight_layout()
    plt.show()
