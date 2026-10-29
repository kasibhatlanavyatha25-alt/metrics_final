import os
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import git
from app.models.schemas import CommitInfo

logger = logging.getLogger("software_dna.git")


SUPPORTED_EXTENSIONS = (".java", ".py", ".ts", ".tsx", ".js")


class GitInterceptor:
    """
    Inspects Git commits and pull request events to determine changed files
    and commit metadata.
    """

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path
        self._repo: Optional[git.Repo] = None
        if repo_path and Path(repo_path).exists():
            try:
                self._repo = git.Repo(repo_path)
            except Exception as e:
                logger.warning(f"Could not initialize git repo at {repo_path}: {e}")

    def set_repo_path(self, repo_path: str) -> None:
        self.repo_path = repo_path
        self._repo = git.Repo(repo_path)

    def get_repo(self) -> git.Repo:
        if not self._repo:
            if self.repo_path and Path(self.repo_path).exists():
                self._repo = git.Repo(self.repo_path)
            else:
                raise ValueError(f"Git repository not available at: {self.repo_path}")
        return self._repo

    def get_commit_history(self) -> List[CommitInfo]:
        """Returns ordered list of commits from initial to latest."""
        repo = self.get_repo()
        commits = list(repo.iter_commits("HEAD"))
        commits.reverse()  # Chronological order (V1 -> V5)

        results: List[CommitInfo] = []
        for idx, c in enumerate(commits):
            v_label = f"V{idx + 1}"
            changed_files = self.get_changed_files_for_commit(c)
            
            # Formatted timestamp
            ts_str = datetime.fromtimestamp(c.committed_date).strftime("%Y-%m-%d %H:%M:%S")

            results.append(
                CommitInfo(
                    sha=c.hexsha,
                    short_sha=c.hexsha[:7],
                    version_label=v_label,
                    message=c.message.strip(),
                    author=c.author.name or "Software DNA Agent",
                    timestamp=ts_str,
                    changed_files=changed_files,
                    parent_sha=c.parents[0].hexsha if c.parents else None,
                )
            )

        return results

    def get_changed_files_for_commit(self, commit: git.Commit) -> List[str]:
        """Calculates changed source files in this specific commit."""
        changed: List[str] = []
        if not commit.parents:
            # Initial commit: all tracked files are added
            for item in commit.tree.traverse():
                if item.type == "blob" and item.path.endswith(SUPPORTED_EXTENSIONS):
                    changed.append(item.path.replace("\\", "/"))
        else:
            parent = commit.parents[0]
            diffs = parent.diff(commit)
            for diff in diffs:
                path = diff.b_path or diff.a_path
                if path and path.endswith(SUPPORTED_EXTENSIONS):
                    changed.append(path.replace("\\", "/"))

        return sorted(list(set(changed)))

    def get_file_content_at_commit(self, file_path: str, commit_sha: str) -> str:
        """Retrieves raw content of a file at a specific commit SHA."""
        repo = self.get_repo()
        norm_path = file_path.replace("\\", "/").lstrip("/")
        try:
            commit = repo.commit(commit_sha)
            blob = commit.tree / norm_path
            return blob.data_stream.read().decode("utf-8", errors="replace")
        except Exception as ex:
            logger.error(f"Error reading {file_path} at commit {commit_sha}: {ex}")
            # Fallback to local disk file if in work tree
            disk_path = Path(repo.working_tree_dir) / norm_path
            if disk_path.exists():
                return disk_path.read_text(encoding="utf-8", errors="replace")
            return ""

    def get_all_java_files_at_commit(self, commit_sha: str) -> List[str]:
        """List all source files present in repository tree at commit_sha."""
        repo = self.get_repo()
        commit = repo.commit(commit_sha)
        files: List[str] = []
        for item in commit.tree.traverse():
            if item.type == "blob" and item.path.endswith(SUPPORTED_EXTENSIONS):
                files.append(item.path.replace("\\", "/"))
        return sorted(files)
