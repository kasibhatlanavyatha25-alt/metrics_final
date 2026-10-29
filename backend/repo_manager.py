import os
import shutil
import tempfile
import datetime
from typing import Dict, List, Any, Tuple, Optional, Set
import git
try:
    from backend.app.git.repository_service import (
        RepositoryService,
        validate_repository_input,
        normalize_repository_url,
        DEFAULT_WORKSPACE_DIR,
        RepositoryErrorCode
    )
except ImportError:
    from app.git.repository_service import (
        RepositoryService,
        validate_repository_input,
        normalize_repository_url,
        DEFAULT_WORKSPACE_DIR,
        RepositoryErrorCode
    )


CACHE_REPOS_DIR = DEFAULT_WORKSPACE_DIR
os.makedirs(CACHE_REPOS_DIR, exist_ok=True)

class RepoManager:
    def __init__(self, repo_url_or_path: str):
        self.raw_input = repo_url_or_path.strip()
        is_remote, normalized, repo_name = normalize_repository_url(self.raw_input)
        self.is_remote = is_remote
        self.normalized_input = normalized
        self.repo_name = repo_name
        self.repo_dir = ""
        self.repo: Optional[git.Repo] = None

    def prepare_repo(self) -> Tuple[bool, str]:
        """Clones or opens the repository and prepares for analysis."""
        report = self.validate_repository()
        if report.get("valid") or report.get("is_valid"):
            return True, "Successfully prepared repository."
        return False, report.get("message") or report.get("error_reason") or "Failed to prepare repository."


    def validate_repository(self) -> Dict[str, Any]:
        """Performs repository validation using RepositoryService and identifies versions."""
        report = validate_repository_input(self.raw_input)
        if not report.get("valid") and not report.get("is_valid"):
            return report

        self.repo_dir = report.get("local_path", "")
        if self.repo_dir and os.path.exists(self.repo_dir):
            try:
                self.repo = git.Repo(self.repo_dir)
            except Exception:
                pass

        # Populate legacy compatibility fields
        report["detected_languages"] = report.get("language_breakdown", {})
        report["source_file_counts"] = report.get("language_breakdown", {})
        
        # Check version candidates
        versions = self.identify_versions()
        total_commits = report.get("total_commits", 0)
        report["total_versions"] = len(versions) if len(versions) >= 2 else (total_commits if total_commits >= 2 else 1)
        report["version_strategy"] = "Git Tags/Releases" if any(v.get("is_tag") for v in versions) else "Distributed Milestone Commits"

        return report


    def identify_versions(self, max_versions: int = 6) -> List[Dict[str, Any]]:
        """Identifies historical versions from tags or distributed milestones."""
        if not self.repo:
            return []

        # 1. Check for valid tags
        tags = []
        for t in self.repo.tags:
            try:
                commit = t.commit
                tags.append({
                    "tag_name": t.name,
                    "commit_hash": commit.hexsha,
                    "commit_date": datetime.datetime.fromtimestamp(commit.committed_date),
                    "commit_message": commit.message.strip(),
                    "author": commit.author.name if commit.author else "Unknown",
                    "is_tag": True
                })
            except Exception:
                continue

        # Sort tags by commit date
        tags.sort(key=lambda x: x["commit_date"])

        if len(tags) >= 2:
            # Sample tags evenly if too many
            if len(tags) > max_versions:
                indices = [int(i * (len(tags) - 1) / (max_versions - 1)) for i in range(max_versions)]
                selected_tags = [tags[i] for i in sorted(list(set(indices)))]
            else:
                selected_tags = tags

            results = []
            for idx, tag in enumerate(selected_tags, start=1):
                results.append({
                    "version_tag": tag["tag_name"] if tag["tag_name"].startswith('v') or tag["tag_name"].startswith('V') else f"V{idx} ({tag['tag_name']})",
                    "commit_hash": tag["commit_hash"],
                    "commit_date": tag["commit_date"],
                    "order_index": idx,
                    "is_release_tag": True,
                    "commit_message": tag["commit_message"],
                    "author_name": tag["author"]
                })
            return results

        # 2. If < 2 tags, select chronologically distributed commit milestones
        commits = list(self.repo.iter_commits())
        # Chronological order: commits[-1] is earliest, commits[0] is latest
        commits.reverse() # now commits[0] is first commit, commits[-1] is latest

        total_c = len(commits)
        if total_c < 2:
            return []

        k = min(max_versions, total_c)
        # Evenly pick k commits across the lifetime
        step_indices = [int(i * (total_c - 1) / (k - 1)) for i in range(k)]
        selected_commits = [commits[i] for i in sorted(list(set(step_indices)))]

        results = []
        for idx, c in enumerate(selected_commits, start=1):
            results.append({
                "version_tag": f"V{idx}",
                "commit_hash": c.hexsha,
                "commit_date": datetime.datetime.fromtimestamp(c.committed_date),
                "order_index": idx,
                "is_release_tag": False,
                "commit_message": c.message.strip().splitlines()[0] if c.message else f"Commit {c.hexsha[:7]}",
                "author_name": c.author.name if c.author else "Unknown"
            })
        return results

    def checkout_version(self, commit_hash: str, workdir_dest: str) -> bool:
        """Extracts all repository source files at commit_hash into workdir_dest using Git tree traversal."""
        os.makedirs(workdir_dest, exist_ok=True)
        try:
            commit = self.repo.commit(commit_hash)
            # Traverse all blobs in tree
            for item in commit.tree.traverse():
                if item.type == 'blob':
                    dest_file_path = os.path.join(workdir_dest, item.path.replace('/', os.sep))
                    os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                    with open(dest_file_path, 'wb') as f:
                        f.write(item.data_stream.read())
            return True
        except Exception as e:
            print(f"Error checking out commit {commit_hash} via tree traversal: {e}")
            try:
                # Fallback to git checkout in working directory if possible
                self.repo.git.checkout(commit_hash)
                # Copy files
                for root, _, files in os.walk(self.repo_dir):
                    if '.git' in root:
                        continue
                    rel_path = os.path.relpath(root, self.repo_dir)
                    dest_dir = os.path.join(workdir_dest, rel_path)
                    os.makedirs(dest_dir, exist_ok=True)
                    for f in files:
                        shutil.copy2(os.path.join(root, f), os.path.join(dest_dir, f))
                return True
            except Exception as e2:
                print(f"Fallback checkout failed: {e2}")
                return False

    def extract_evolution_metrics_between(self, prev_commit_hash: Optional[str], curr_commit_hash: str) -> Dict[str, Any]:
        """Calculates Git evolution features (churn, modified files, commits) between two versions."""
        if not self.repo:
            return {}

        curr_commit = self.repo.commit(curr_commit_hash)
        curr_date = datetime.datetime.fromtimestamp(curr_commit.committed_date)

        if not prev_commit_hash:
            # Baseline V1
            return {
                "commit_count": 1,
                "commit_frequency": 1.0,
                "added_lines": 0,
                "deleted_lines": 0,
                "code_churn": 0,
                "modified_files_count": 0,
                "modified_classes_count": 0,
                "modified_packages_count": 0,
                "avg_time_between_commits_hours": 0.0,
                "time_since_prev_version_days": 0.0,
            }

        prev_commit = self.repo.commit(prev_commit_hash)
        prev_date = datetime.datetime.fromtimestamp(prev_commit.committed_date)
        delta_days = max(0.1, (curr_date - prev_date).total_seconds() / 86400.0)

        # Commits in range prev_commit..curr_commit
        rev_range = f"{prev_commit_hash}..{curr_commit_hash}"
        try:
            commits = list(self.repo.iter_commits(rev_range))
        except Exception:
            commits = [curr_commit]

        commit_count = max(1, len(commits))
        commit_frequency = round(commit_count / delta_days, 3)

        # Calculate diff stats
        added_lines = 0
        deleted_lines = 0
        modified_files = set()
        modified_classes = set()
        modified_packages = set()

        try:
            diff_index = prev_commit.diff(curr_commit)
            for diff_item in diff_index:
                path = diff_item.b_path or diff_item.a_path
                if path:
                    modified_files.add(path)
                    if path.endswith('.java'):
                        c_name = os.path.splitext(os.path.basename(path))[0]
                        modified_classes.add(c_name)
                        pkg = os.path.dirname(path).replace('/', '.')
                        if pkg:
                            modified_packages.add(pkg)

            # Get insertions / deletions from git diff summary
            diff_stat = self.repo.git.diff("--shortstat", prev_commit_hash, curr_commit_hash)
            # e.g. " 15 files changed, 250 insertions(+), 80 deletions(-)"
            import re
            ins_match = re.search(r'(\d+)\s+insertion', diff_stat)
            del_match = re.search(r'(\d+)\s+deletion', diff_stat)
            if ins_match:
                added_lines = int(ins_match.group(1))
            if del_match:
                deleted_lines = int(del_match.group(1))
        except Exception as e:
            added_lines = 0
            deleted_lines = 0

        code_churn = added_lines + deleted_lines
        avg_time_between_commits_hours = round((delta_days * 24.0) / max(1, commit_count), 2)

        return {
            "commit_count": commit_count,
            "commit_frequency": commit_frequency,
            "added_lines": added_lines,
            "deleted_lines": deleted_lines,
            "code_churn": code_churn,
            "modified_files_count": len(modified_files),
            "modified_classes_count": len(modified_classes),
            "modified_packages_count": len(modified_packages),
            "avg_time_between_commits_hours": avg_time_between_commits_hours,
            "time_since_prev_version_days": round(delta_days, 1),
        }
