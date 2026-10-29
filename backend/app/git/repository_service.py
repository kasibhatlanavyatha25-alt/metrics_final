import os
import re
import shutil
import hashlib
import logging
import datetime
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set
import git

logger = logging.getLogger("software_dna.repository_service")

# Error Codes
class RepositoryErrorCode:
    INVALID_REPOSITORY_URL = "INVALID_REPOSITORY_URL"
    REPOSITORY_NOT_FOUND = "REPOSITORY_NOT_FOUND"
    PRIVATE_REPOSITORY = "PRIVATE_REPOSITORY"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    GIT_NOT_INSTALLED = "GIT_NOT_INSTALLED"
    NETWORK_ERROR = "NETWORK_ERROR"
    GIT_OPERATION_TIMEOUT = "GIT_OPERATION_TIMEOUT"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    CLONE_FAILED = "CLONE_FAILED"
    INVALID_GIT_REPOSITORY = "INVALID_GIT_REPOSITORY"
    EMPTY_REPOSITORY = "EMPTY_REPOSITORY"
    NO_SUPPORTED_SOURCE_FILES = "NO_SUPPORTED_SOURCE_FILES"
    UNSUPPORTED_REPOSITORY = "UNSUPPORTED_REPOSITORY"
    INTERNAL_ERROR = "INTERNAL_ERROR"

# Base directory for cloned repositories
DEFAULT_WORKSPACE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "repositories")
)
os.makedirs(DEFAULT_WORKSPACE_DIR, exist_ok=True)

# Language extension definitions
LANGUAGE_EXTENSIONS = {
    # Core Analyzable / Supported
    ".java": "Java",
    ".py": "Python",
    ".pyw": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".c": "C/C++",
    ".h": "C/C++",
    ".cpp": "C/C++",
    ".hpp": "C/C++",
    ".cc": "C/C++",
    ".cxx": "C/C++",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".rb": "Ruby",
    ".php": "PHP",
    # Scripting / Markup / Config
    ".sh": "Shell",
    ".bash": "Shell",
    ".ps1": "PowerShell",
    ".bat": "Batch",
    ".cmd": "Batch",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".sass": "CSS",
    ".less": "CSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".xml": "XML",
    ".sql": "SQL",
    ".md": "Markdown",
    ".markdown": "Markdown",
}

SOURCE_CODE_LANGUAGES = {
    "Java", "Python", "JavaScript", "TypeScript", "C/C++", "C#", "Go",
    "Rust", "Kotlin", "Scala", "Ruby", "PHP", "Shell", "PowerShell", "SQL"
}

ANALYZER_SUPPORTED_LANGUAGES = {
    "Java", "Python", "JavaScript", "TypeScript"
}

IGNORED_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "venv", ".venv", "env",
    "__pycache__", "target", "build", "dist", "out", ".idea", ".vscode",
    ".gradle", ".mvn", ".next", ".nuxt", "coverage", "vendor", "bin", "obj"
}


def sanitize_input_for_logging(val: str) -> str:
    """Removes user passwords, tokens, or sensitive credentials from URLs."""
    if not val:
        return ""
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", val)


def check_git_installed() -> bool:
    """Checks if git binary is present and runnable in the system PATH."""
    try:
        res = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        return res.returncode == 0
    except Exception:
        return False


def normalize_repository_url(url_or_path: str) -> Tuple[bool, str, str]:
    """
    Determines if input is a remote URL or local path, normalizes it, and extracts repository name.
    Returns: (is_remote, normalized_identifier, repo_name)
    """
    cleaned = url_or_path.strip().strip('"').strip("'")
    
    # Check if remote URL
    is_remote = (
        cleaned.startswith("http://") or 
        cleaned.startswith("https://") or 
        cleaned.startswith("git://") or 
        cleaned.startswith("git@") or
        cleaned.startswith("ssh://")
    )
    
    if is_remote:
        # Strip trailing slashes
        norm_url = re.sub(r"/+$", "", cleaned)
        # Extract repo name
        parts = norm_url.split("/")
        repo_name = parts[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        if not repo_name and len(parts) > 1:
            repo_name = parts[-2]
        if not repo_name:
            repo_name = "repository"
        return True, norm_url, repo_name
    else:
        # Local path
        abs_path = os.path.abspath(os.path.normpath(cleaned))
        repo_name = os.path.basename(abs_path) or "local_repository"
        return False, abs_path, repo_name


def classify_git_error(stderr_str: str, default_code: str = RepositoryErrorCode.CLONE_FAILED) -> Tuple[str, str, str]:
    """
    Classifies git stderr into structured error_code, user-friendly message, and suggestion.
    """
    low = stderr_str.lower()
    
    if "not found" in low or "repository not found" in low or "could not read from remote" in low:
        return (
            RepositoryErrorCode.REPOSITORY_NOT_FOUND,
            "Repository not found on remote host.",
            "Verify that the URL is spelled correctly and that the repository exists and is public."
        )
    elif "authentication failed" in low or "permission denied" in low or "could not read username" in low or "terminal prompts disabled" in low:
        return (
            RepositoryErrorCode.AUTHENTICATION_REQUIRED,
            "Authentication required or repository is private.",
            "Please ensure the repository is public or credentials are provided."
        )
    elif "could not resolve host" in low or "failed to connect" in low or "network is unreachable" in low or "connection refused" in low:
        return (
            RepositoryErrorCode.NETWORK_ERROR,
            "Network connectivity failure while reaching remote repository.",
            "Check your internet connection or proxy/DNS configuration."
        )
    elif "timed out" in low or "operation timed out" in low:
        return (
            RepositoryErrorCode.GIT_OPERATION_TIMEOUT,
            "Git operation timed out.",
            "The repository may be very large or network speed is constrained. Try again or use a smaller repository."
        )
    else:
        return (
            default_code,
            "Git operation failed.",
            "Check that the repository is accessible and Git is functioning correctly."
        )


def check_remote_repository(url: str, timeout: int = 20) -> Dict[str, Any]:
    """
    Probes remote repository reachability and inspects HEAD reference without cloning full history.
    """
    sanitized = sanitize_input_for_logging(url)
    logger.info(f"[GIT_REMOTE_CHECK] Checking remote reachability: {sanitized}")
    
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    
    try:
        proc = subprocess.run(
            ["git", "ls-remote", "--symref", url, "HEAD"],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
    except subprocess.TimeoutExpired:
        logger.warning(f"[GIT_REMOTE_CHECK] Timeout ({timeout}s) probing remote: {sanitized}")
        return {
            "success": False,
            "error_code": RepositoryErrorCode.NETWORK_TIMEOUT,
            "message": f"Connection to remote repository timed out after {timeout} seconds.",
            "details": f"git ls-remote timed out after {timeout}s",
            "suggestion": "Check your internet connection or verify repository responsiveness."
        }
    except Exception as e:
        logger.error(f"[GIT_REMOTE_CHECK] Exception probing remote {sanitized}: {e}")
        return {
            "success": False,
            "error_code": RepositoryErrorCode.NETWORK_ERROR,
            "message": "Unable to execute Git remote probe.",
            "details": str(e),
            "suggestion": "Ensure Git is installed and network connectivity is active."
        }
    
    if proc.returncode != 0:
        err_code, msg, sug = classify_git_error(proc.stderr, RepositoryErrorCode.REPOSITORY_NOT_FOUND)
        logger.warning(f"[GIT_REMOTE_CHECK] Probe failed for {sanitized}: code={err_code}, stderr={proc.stderr.strip()}")
        return {
            "success": False,
            "error_code": err_code,
            "message": msg,
            "details": proc.stderr.strip() or proc.stdout.strip(),
            "suggestion": sug
        }
    
    # Parse output to find default branch and HEAD sha
    head_sha = ""
    default_branch = "main"
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("ref: refs/heads/"):
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "HEAD":
                default_branch = parts[0].replace("ref: refs/heads/", "")
        elif line.endswith("HEAD"):
            parts = line.split()
            if len(parts) >= 1:
                head_sha = parts[0]
                
    return {
        "success": True,
        "head_sha": head_sha,
        "default_branch": default_branch,
        "raw_output": proc.stdout
    }


def get_deterministic_workspace_path(normalized_url_or_path: str, repo_name: str, base_dir: str = DEFAULT_WORKSPACE_DIR) -> str:
    """Generates a secure, deterministic workspace directory preventing path traversal."""
    safe_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', repo_name)[:30]
    hasher = hashlib.sha256(normalized_url_or_path.encode('utf-8')).hexdigest()[:12]
    dir_name = f"repo_{safe_slug}_{hasher}"
    target = os.path.abspath(os.path.join(base_dir, dir_name))
    
    # Security check: must reside inside base_dir
    if not target.startswith(os.path.abspath(base_dir)):
        raise ValueError(f"Path traversal detected: {target}")
    return target


def clone_repository(url: str, target_dir: str, timeout: int = 180) -> Dict[str, Any]:
    """
    Clones a remote repository into target_dir safely with timeout and progress capturing.
    """
    sanitized = sanitize_input_for_logging(url)
    logger.info(f"[GIT_CLONE] Cloning {sanitized} into {target_dir} (timeout={timeout}s)")
    
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    
    # If target dir already exists with valid git repo, verify and fetch
    if os.path.exists(target_dir) and os.path.exists(os.path.join(target_dir, ".git")):
        try:
            logger.info(f"[GIT_CLONE] Existing repository found at {target_dir}. Verifying...")
            repo = git.Repo(target_dir)
            if not repo.bare and repo.head.is_valid():
                return {"success": True, "target_dir": target_dir, "reused": True}
        except Exception as ex:
            logger.warning(f"[GIT_CLONE] Existing directory invalid, cleaning: {ex}")
            cleanup_workspace(target_dir)
            
    os.makedirs(target_dir, exist_ok=True)
    
    try:
        # Clone full commit history with timeout
        cmd = ["git", "clone", url, target_dir]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
    except subprocess.TimeoutExpired:
        logger.error(f"[GIT_CLONE] Timeout ({timeout}s) cloning {sanitized}")
        cleanup_workspace(target_dir)
        return {
            "success": False,
            "error_code": RepositoryErrorCode.GIT_OPERATION_TIMEOUT,
            "message": f"Cloning repository exceeded timeout of {timeout} seconds.",
            "details": f"Command '{' '.join(cmd)}' timed out after {timeout}s",
            "suggestion": "The repository may be very large. Try cloning a specific shallow branch or check network stability."
        }
    except Exception as e:
        logger.error(f"[GIT_CLONE] Failed to execute git clone for {sanitized}: {e}")
        cleanup_workspace(target_dir)
        return {
            "success": False,
            "error_code": RepositoryErrorCode.INTERNAL_ERROR,
            "message": f"System error executing git clone: {str(e)}",
            "details": str(e),
            "suggestion": "Check server permissions and disk space."
        }
        
    if proc.returncode != 0:
        cleanup_workspace(target_dir)
        err_code, msg, sug = classify_git_error(proc.stderr, RepositoryErrorCode.CLONE_FAILED)
        logger.warning(f"[GIT_CLONE] Clone failed: code={err_code}, stderr={proc.stderr.strip()}")
        return {
            "success": False,
            "error_code": err_code,
            "message": msg,
            "details": proc.stderr.strip() or proc.stdout.strip(),
            "suggestion": sug
        }
        
    logger.info(f"[GIT_CLONE] Successfully cloned {sanitized} to {target_dir}")
    return {"success": True, "target_dir": target_dir, "reused": False}


def open_repository(path: str) -> Tuple[bool, Optional[git.Repo], Optional[Dict[str, Any]]]:
    """Opens a local Git repository safely using GitPython."""
    if not os.path.exists(path):
        return False, None, {
            "error_code": RepositoryErrorCode.INVALID_REPOSITORY_URL,
            "message": f"Specified path '{path}' does not exist on disk.",
            "details": "Local directory not found.",
            "suggestion": "Verify that the local path exists and is readable."
        }
    try:
        repo = git.Repo(path)
        if repo.bare:
            return False, None, {
                "error_code": RepositoryErrorCode.INVALID_GIT_REPOSITORY,
                "message": "The repository is bare (no working directory).",
                "details": "Bare git repository detected.",
                "suggestion": "Provide a working tree repository clone."
            }
        return True, repo, None
    except git.InvalidGitRepositoryError:
        return False, None, {
            "error_code": RepositoryErrorCode.INVALID_GIT_REPOSITORY,
            "message": f"Directory '{path}' is not a valid Git repository.",
            "details": "Missing .git directory or corrupted git metadata.",
            "suggestion": "Ensure the directory was initialized with Git ('git init' or 'git clone')."
        }
    except Exception as e:
        return False, None, {
            "error_code": RepositoryErrorCode.INTERNAL_ERROR,
            "message": f"Error opening repository at '{path}': {str(e)}",
            "details": str(e),
            "suggestion": "Check repository file permissions."
        }


def get_default_branch(repo: git.Repo) -> str:
    """Detects active or default branch of repository."""
    try:
        if not repo.head.is_detached:
            return repo.active_branch.name
    except Exception:
        pass
        
    try:
        for ref in repo.references:
            if ref.name in ('main', 'master', 'origin/main', 'origin/master'):
                return ref.name.split('/')[-1]
    except Exception:
        pass
        
    return "main"


def get_head_commit(repo: git.Repo) -> Dict[str, Any]:
    """Extracts metadata from HEAD commit."""
    try:
        commit = repo.head.commit
        return {
            "sha": commit.hexsha,
            "short_sha": commit.hexsha[:7],
            "message": commit.message.strip(),
            "author": f"{commit.author.name} <{commit.author.email}>",
            "date": datetime.datetime.fromtimestamp(commit.committed_date).isoformat(),
            "timestamp": commit.committed_date
        }
    except Exception as ex:
        logger.warning(f"Error extracting HEAD commit: {ex}")
        return {
            "sha": "",
            "short_sha": "",
            "message": "",
            "author": "",
            "date": "",
            "timestamp": 0
        }


def get_commit_history(repo: git.Repo, max_commits: int = 100) -> List[Dict[str, Any]]:
    """Retrieves commit history list."""
    commits = []
    try:
        for c in repo.iter_commits(max_count=max_commits):
            commits.append({
                "sha": c.hexsha,
                "short_sha": c.hexsha[:7],
                "message": c.message.strip().split("\n")[0],
                "author": c.author.name,
                "date": datetime.datetime.fromtimestamp(c.committed_date).isoformat(),
                "timestamp": c.committed_date
            })
    except Exception as ex:
        logger.warning(f"Error iterating commit history: {ex}")
    return commits


def get_changed_files(repo: git.Repo, commit_sha: Optional[str] = None) -> List[str]:
    """Gets list of changed files for a given commit or HEAD."""
    try:
        commit = repo.commit(commit_sha) if commit_sha else repo.head.commit
        if commit.parents:
            diffs = commit.parents[0].diff(commit)
            return [d.b_path or d.a_path for d in diffs if d.b_path or d.a_path]
        else:
            return list(commit.stats.files.keys())
    except Exception:
        return []


def detect_languages(repo_dir: str) -> Dict[str, Any]:
    """
    Recursively scans the repository directory to detect programming languages, file counts, and source breakdown.
    """
    logger.info(f"[LANGUAGE_DETECTION] Scanning languages in {repo_dir}")
    
    lang_counts: Dict[str, int] = {}
    source_file_count = 0
    total_files = 0
    sample_files: Dict[str, List[str]] = {}
    java_files_count = 0
    python_files_count = 0
    js_ts_files_count = 0
    analyzable_files: List[str] = []
    supported_analyzers_set: Set[str] = set()
    
    SUPPORTED_EXTS = {
        ".java": "Java",
        ".py": "Python",
        ".pyw": "Python",
        ".js": "JavaScript/TypeScript",
        ".jsx": "JavaScript/TypeScript",
        ".ts": "JavaScript/TypeScript",
        ".tsx": "JavaScript/TypeScript",
        ".mjs": "JavaScript/TypeScript"
    }

    for root, dirs, files in os.walk(repo_dir):
        # Prune ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith('.')]
        
        for f in files:
            total_files += 1
            ext = os.path.splitext(f)[1].lower()
            lang = LANGUAGE_EXTENSIONS.get(ext)
            
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
                if lang in SOURCE_CODE_LANGUAGES:
                    source_file_count += 1
                    if lang not in sample_files:
                        sample_files[lang] = []
                    if len(sample_files[lang]) < 5:
                        rel = os.path.relpath(os.path.join(root, f), repo_dir)
                        sample_files[lang].append(rel)
                        
                if lang == "Java":
                    java_files_count += 1
                elif lang == "Python":
                    python_files_count += 1
                elif lang in ("JavaScript", "TypeScript"):
                    js_ts_files_count += 1
                    
            if ext in SUPPORTED_EXTS:
                analyzable_files.append(os.path.join(root, f))
                supported_analyzers_set.add(SUPPORTED_EXTS[ext])
                    
    # Sort languages by file count
    sorted_languages = sorted(lang_counts.keys(), key=lambda k: lang_counts[k], reverse=True)
    primary_language = sorted_languages[0] if sorted_languages else "Unknown"
    
    has_analyzable = len(analyzable_files) > 0
    supported_analyzers_list = sorted(list(supported_analyzers_set))
    sample_classes = [os.path.basename(f) for f in analyzable_files[:10]]
    
    return {
        "languages": sorted_languages,
        "language_breakdown": lang_counts,
        "detected_languages": lang_counts,
        "primary_language": primary_language,
        "source_file_count": source_file_count,
        "total_files": total_files,
        "total_java_files": java_files_count,
        "total_python_files": python_files_count,
        "total_js_ts_files": js_ts_files_count,
        "has_java_files": java_files_count > 0,
        "analyzable_files": analyzable_files,
        "analyzable_files_count": len(analyzable_files),
        "has_analyzable_files": has_analyzable,
        "sample_classes": sample_classes,
        "sample_files": sample_files,
        "supported": has_analyzable or source_file_count > 0,
        "supported_analyzers": supported_analyzers_list
    }



def cleanup_workspace(target_dir: str) -> bool:
    """Safely cleans up repository directory."""
    if not os.path.exists(target_dir):
        return True
    try:
        # On Windows, git files might be read-only
        def handle_remove_readonly(func, path, exc):
            import stat
            os.chmod(path, stat.S_IWRITE)
            func(path)
            
        shutil.rmtree(target_dir, onerror=handle_remove_readonly)
        return True
    except Exception as ex:
        logger.warning(f"Error cleaning up workspace {target_dir}: {ex}")
        return False


def validate_repository_input(
    input_str: str, 
    workspace_base: str = DEFAULT_WORKSPACE_DIR,
    timeout: int = 120
) -> Dict[str, Any]:
    """
    Comprehensive repository validation pipeline supporting both Public GitHub URLs and Local Git Repositories.
    
    Returns structured JSON meeting all validation and UI requirements.
    """
    sanitized_input = sanitize_input_for_logging(input_str)
    logger.info(f"[REPOSITORY_VALIDATION] Starting validation for input: '{sanitized_input}'")
    
    if not input_str or not input_str.strip():
        logger.warning("[VALIDATION_FAILURE] Empty repository input")
        return {
            "valid": False,
            "is_valid": False,
            "error_code": RepositoryErrorCode.INVALID_REPOSITORY_URL,
            "message": "Repository URL or local path cannot be empty.",
            "error_reason": "Repository URL or local path cannot be empty.",
            "details": "Empty input string received.",
            "repository": input_str,
            "suggestion": "Please provide a valid GitHub repository URL (e.g., https://github.com/owner/repo) or local folder path."
        }
        
    # Check Git binary availability
    if not check_git_installed():
        logger.error("[VALIDATION_FAILURE] Git is not installed or not in PATH")
        return {
            "valid": False,
            "is_valid": False,
            "error_code": RepositoryErrorCode.GIT_NOT_INSTALLED,
            "message": "Git executable is not installed or not accessible in system PATH.",
            "error_reason": "Git executable is not installed or not accessible in system PATH.",
            "details": "git --version failed to execute.",
            "repository": sanitized_input,
            "suggestion": "Install Git (https://git-scm.com/) and ensure it is available in system PATH."
        }

    # 1. Normalize Input
    is_remote, normalized_id, repo_name = normalize_repository_url(input_str)
    logger.info(f"[URL_NORMALIZATION] Normalized '{sanitized_input}' -> '{sanitize_input_for_logging(normalized_id)}' (is_remote={is_remote}, repo_name={repo_name})")
    
    # 2. Remote URL Handling
    if is_remote:
        # Check basic URL syntax
        if not re.match(r'^(https?://|git://|git@|ssh://)', normalized_id):
            return {
                "valid": False,
                "is_valid": False,
                "error_code": RepositoryErrorCode.INVALID_REPOSITORY_URL,
                "message": "Invalid repository URL format.",
                "error_reason": "Invalid repository URL format.",
                "details": f"URL '{sanitized_input}' does not start with supported protocol.",
                "repository": sanitized_input,
                "suggestion": "Ensure URL starts with https://, http://, or git@."
            }
            
        # Fast remote reachability check using git ls-remote
        remote_check = check_remote_repository(normalized_id, timeout=20)
        if not remote_check["success"]:
            logger.warning(f"[VALIDATION_FAILURE] Remote check failed for {sanitized_input}: {remote_check['error_code']}")
            return {
                "valid": False,
                "is_valid": False,
                "error_code": remote_check["error_code"],
                "message": remote_check["message"],
                "error_reason": remote_check["message"],
                "details": remote_check["details"],
                "repository": sanitized_input,
                "suggestion": remote_check["suggestion"]
            }
            
        # Determine workspace directory
        try:
            workspace_dir = get_deterministic_workspace_path(normalized_id, repo_name, base_dir=workspace_base)
        except Exception as ex:
            return {
                "valid": False,
                "is_valid": False,
                "error_code": RepositoryErrorCode.INTERNAL_ERROR,
                "message": "Failed to allocate workspace directory.",
                "error_reason": str(ex),
                "details": str(ex),
                "repository": sanitized_input,
                "suggestion": "Check file system permissions."
            }
            
        # Clone repository
        clone_res = clone_repository(normalized_id, workspace_dir, timeout=timeout)
        if not clone_res["success"]:
            logger.warning(f"[VALIDATION_FAILURE] Clone failed for {sanitized_input}: {clone_res['error_code']}")
            return {
                "valid": False,
                "is_valid": False,
                "error_code": clone_res["error_code"],
                "message": clone_res["message"],
                "error_reason": clone_res["message"],
                "details": clone_res["details"],
                "repository": sanitized_input,
                "suggestion": clone_res["suggestion"]
            }
            
        repo_dir = workspace_dir
        repo_url = normalized_id
        local_path = workspace_dir
    else:
        # Local repository path handling
        repo_dir = normalized_id
        repo_url = None
        local_path = normalized_id
        
    # 3. Inspect Repository
    logger.info(f"[GIT_INSPECTION] Inspecting repository at {repo_dir}")
    opened, repo, open_err = open_repository(repo_dir)
    if not opened or repo is None:
        logger.warning(f"[VALIDATION_FAILURE] Open repository failed for {repo_dir}: {open_err}")
        return {
            "valid": False,
            "is_valid": False,
            "error_code": open_err["error_code"],
            "message": open_err["message"],
            "error_reason": open_err["message"],
            "details": open_err["details"],
            "repository": sanitized_input,
            "suggestion": open_err["suggestion"]
        }
        
    # Commit history & branch detection
    commits = get_commit_history(repo, max_commits=100)
    commit_count = len(commits)
    
    if commit_count == 0:
        logger.warning(f"[VALIDATION_FAILURE] Empty repository at {repo_dir}")
        return {
            "valid": False,
            "is_valid": False,
            "error_code": RepositoryErrorCode.EMPTY_REPOSITORY,
            "message": "Repository contains zero commits.",
            "error_reason": "Repository contains zero commits.",
            "details": "No commits found in active branch history.",
            "repository": sanitized_input,
            "suggestion": "Make at least one commit in the repository before analyzing."
        }
        
    head_info = get_head_commit(repo)
    default_branch = get_default_branch(repo)
    
    # 4. Language & Source File Detection
    lang_info = detect_languages(repo_dir)
    
    if lang_info["total_files"] == 0:
        logger.warning(f"[VALIDATION_FAILURE] No files in repository at {repo_dir}")
        return {
            "valid": False,
            "is_valid": False,
            "error_code": RepositoryErrorCode.NO_SUPPORTED_SOURCE_FILES,
            "message": "Repository contains no files in working tree.",
            "error_reason": "Repository contains no files in working tree.",
            "details": "Empty working tree directory.",
            "repository": sanitized_input,
            "suggestion": "Add source files to the repository."
        }
        
    first_commit_date = datetime.datetime.fromtimestamp(commits[-1]["timestamp"]) if commits else None
    latest_commit_date = datetime.datetime.fromtimestamp(commits[0]["timestamp"]) if commits else None
    
    # Check for analyzability
    has_analyzable_files = lang_info["has_analyzable_files"]
    analyzable_count = lang_info["analyzable_files_count"]
    sample_classes = lang_info["sample_classes"]
    warning_msg = None
    if not has_analyzable_files:
        warning_msg = "Repository validated successfully, but no compatible analyzer is currently available for this language."
    elif not lang_info["has_java_files"] and lang_info["total_python_files"] == 0 and lang_info["total_js_ts_files"] == 0:
        warning_msg = f"Primary language is {lang_info['primary_language']}. Core AST engine is optimized for Java, Python, and JavaScript/TypeScript."


    logger.info(
        f"[VALIDATION_SUCCESS] Validated repository '{repo_name}': "
        f"branch={default_branch}, commits={commit_count}, "
        f"languages={lang_info['languages'][:3]}, source_files={lang_info['source_file_count']}"
    )

    return {
        # Standard Structured Schema
        "valid": True,
        "is_valid": True,
        "repository_url": repo_url,
        "repo_url": repo_url,
        "repository_name": repo_name,
        "repo_name": repo_name,
        "default_branch": default_branch,
        "branch": default_branch,
        "head_commit": head_info["sha"],
        "head_commit_short": head_info["short_sha"],
        "head_commit_message": head_info["message"],
        "head_commit_author": head_info["author"],
        "head_commit_date": head_info["date"],
        "commit_count": commit_count,
        "total_commits": commit_count,
        "total_versions": min(commit_count, 10),
        "first_commit_date": first_commit_date,
        "latest_commit_date": latest_commit_date,
        "first_commit_date_iso": commits[-1]["date"] if commits else None,
        "latest_commit_date_iso": commits[0]["date"] if commits else None,

        "languages": lang_info["languages"],
        "language_breakdown": lang_info["language_breakdown"],
        "detected_languages": lang_info["detected_languages"],
        "primary_language": lang_info["primary_language"],
        "source_file_count": lang_info["source_file_count"],
        "total_files": lang_info["total_files"],
        "total_java_files": lang_info["total_java_files"],
        "has_java_files": lang_info["has_java_files"],
        "has_analyzable_files": has_analyzable_files,
        "analyzable_files_count": analyzable_count,
        "sample_classes": sample_classes,
        "supported": lang_info["supported"],
        "supported_analyzers": lang_info["supported_analyzers"],
        "sample_files": lang_info["sample_files"],
        "local_path": local_path,
        "warning_message": warning_msg,
        "error_reason": None
    }



class RepositoryService:
    """Service facade providing repository operations."""
    
    @staticmethod
    def validate_repository_input(input_str: str, timeout: int = 120) -> Dict[str, Any]:
        return validate_repository_input(input_str, timeout=timeout)

    @staticmethod
    def normalize_repository_url(url_or_path: str) -> Tuple[bool, str, str]:
        return normalize_repository_url(url_or_path)

    @staticmethod
    def check_remote_repository(url: str, timeout: int = 20) -> Dict[str, Any]:
        return check_remote_repository(url, timeout=timeout)

    @staticmethod
    def clone_repository(url: str, target_dir: str, timeout: int = 180) -> Dict[str, Any]:
        return clone_repository(url, target_dir, timeout=timeout)

    @staticmethod
    def open_repository(path: str) -> Tuple[bool, Optional[git.Repo], Optional[Dict[str, Any]]]:
        return open_repository(path)

    @staticmethod
    def get_default_branch(repo: git.Repo) -> str:
        return get_default_branch(repo)

    @staticmethod
    def get_head_commit(repo: git.Repo) -> Dict[str, Any]:
        return get_head_commit(repo)

    @staticmethod
    def get_commit_history(repo: git.Repo, max_commits: int = 100) -> List[Dict[str, Any]]:
        return get_commit_history(repo, max_commits=max_commits)

    @staticmethod
    def get_changed_files(repo: git.Repo, commit_sha: Optional[str] = None) -> List[str]:
        return get_changed_files(repo, commit_sha=commit_sha)

    @staticmethod
    def detect_languages(repo_dir: str) -> Dict[str, Any]:
        return detect_languages(repo_dir)

    @staticmethod
    def cleanup_workspace(target_dir: str) -> bool:
        return cleanup_workspace(target_dir)
