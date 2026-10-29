import os
import shutil
import tempfile
import subprocess
import pytest
from unittest.mock import patch, MagicMock
import git

from backend.app.git.repository_service import (
    RepositoryService,
    validate_repository_input,
    normalize_repository_url,
    check_remote_repository,
    clone_repository,
    open_repository,
    detect_languages,
    RepositoryErrorCode,
)


@pytest.fixture
def temp_workspace():
    tmp_dir = tempfile.mkdtemp(prefix="test_repo_workspace_")
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def local_git_repo():
    repo_dir = tempfile.mkdtemp(prefix="test_local_git_")
    repo = git.Repo.init(repo_dir)
    
    # Add files
    file1 = os.path.join(repo_dir, "App.java")
    with open(file1, "w") as f:
        f.write("public class App { public static void main(String[] args) {} }")
        
    file2 = os.path.join(repo_dir, "script.py")
    with open(file2, "w") as f:
        f.write("print('hello world')")
        
    repo.index.add(["App.java", "script.py"])
    repo.index.commit("Initial commit with Java and Python")
    
    # Second commit
    file3 = os.path.join(repo_dir, "index.ts")
    with open(file3, "w") as f:
        f.write("export const val: number = 42;")
    repo.index.add(["index.ts"])
    repo.index.commit("Add TypeScript module")
    
    yield repo_dir
    shutil.rmtree(repo_dir, ignore_errors=True)


@pytest.fixture
def empty_git_repo():
    repo_dir = tempfile.mkdtemp(prefix="test_empty_git_")
    git.Repo.init(repo_dir)
    yield repo_dir
    shutil.rmtree(repo_dir, ignore_errors=True)


# 1. Test Valid Public GitHub URL
def test_valid_public_github_url(temp_workspace):
    url = "https://github.com/kasibhatlanavyatha25-alt/Script.git"
    res = validate_repository_input(url, workspace_base=temp_workspace)
    assert res["valid"] is True
    assert res["is_valid"] is True
    assert res["repository_name"] == "Script"
    assert res["default_branch"] in ("main", "master")
    assert res["commit_count"] >= 1
    assert "Python" in res["languages"]
    assert res["source_file_count"] > 0
    assert res["supported"] is True


# 2. Test GitHub URL without .git
def test_github_url_without_git(local_git_repo):
    url = "https://github.com/kasibhatlanavyatha25-alt/Script"
    is_remote, norm_url, repo_name = normalize_repository_url(url)
    assert is_remote is True
    assert norm_url == "https://github.com/kasibhatlanavyatha25-alt/Script"
    assert repo_name == "Script"
    
    # Test local URL without .git extension
    is_rem_local, norm_local, repo_name_local = normalize_repository_url(local_git_repo)
    assert is_rem_local is False
    res = validate_repository_input(norm_local)
    assert res["valid"] is True
    assert res["repository_name"] == os.path.basename(local_git_repo)



# 3. Test Malformed / Empty URL
def test_malformed_or_empty_url():
    res_empty = validate_repository_input("")
    assert res_empty["valid"] is False
    assert res_empty["error_code"] == RepositoryErrorCode.INVALID_REPOSITORY_URL

    res_invalid = validate_repository_input("htp://invalid format")
    assert res_invalid["valid"] is False


# 4. Test Nonexistent Repository
def test_nonexistent_repository(temp_workspace):
    url = "https://github.com/nonexistent-user-1234567890/nonexistent-repo-9876543210.git"
    res = validate_repository_input(url, workspace_base=temp_workspace)
    assert res["valid"] is False
    assert res["error_code"] in (
        RepositoryErrorCode.REPOSITORY_NOT_FOUND, 
        RepositoryErrorCode.AUTHENTICATION_REQUIRED,
        RepositoryErrorCode.CLONE_FAILED
    )
    assert res["message"] is not None
    assert res["suggestion"] is not None


# 5. Test Local Valid Git Repository
def test_local_valid_git_repository(local_git_repo):
    res = validate_repository_input(local_git_repo)
    assert res["valid"] is True
    assert res["is_valid"] is True
    assert res["commit_count"] == 2
    assert "Java" in res["languages"]
    assert "Python" in res["languages"]
    assert "TypeScript" in res["languages"]
    assert res["source_file_count"] == 3
    assert res["supported"] is True


# 6. Test Invalid Local Path
def test_invalid_local_path():
    fake_path = os.path.abspath("C:/nonexistent_folder_abc_123_xyz")
    res = validate_repository_input(fake_path)
    assert res["valid"] is False
    assert res["error_code"] in (
        RepositoryErrorCode.INVALID_REPOSITORY_URL,
        RepositoryErrorCode.INVALID_GIT_REPOSITORY
    )


# 7. Test Empty Git Repository (Zero Commits)
def test_empty_git_repository(empty_git_repo):
    res = validate_repository_input(empty_git_repo)
    assert res["valid"] is False
    assert res["error_code"] == RepositoryErrorCode.EMPTY_REPOSITORY
    assert "zero commits" in res["message"].lower() or "no commits" in res["message"].lower()


# 8. Test Git Not Installed Scenario
def test_git_not_installed():
    with patch("backend.app.git.repository_service.check_git_installed", return_value=False):
        res = validate_repository_input("https://github.com/owner/repo.git")
        assert res["valid"] is False
        assert res["error_code"] == RepositoryErrorCode.GIT_NOT_INSTALLED
        assert "git" in res["message"].lower()


# 9. Test Network Timeout Scenario
def test_network_timeout():
    with patch("backend.app.git.repository_service.check_git_installed", return_value=True):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="git ls-remote", timeout=20)):
            res = validate_repository_input("https://github.com/owner/repo.git")
            assert res["valid"] is False
            assert res["error_code"] in (
                RepositoryErrorCode.NETWORK_TIMEOUT,
                RepositoryErrorCode.GIT_OPERATION_TIMEOUT
            )
            assert "timed out" in res["message"].lower()


# 10. Test Clone Failure Scenario
def test_clone_failure(temp_workspace):
    # Mock check_remote_repository returning success, but clone_repository failing with error
    mock_remote_success = {
        "success": True,
        "head_sha": "abc1234",
        "default_branch": "main",
        "raw_output": "ref: refs/heads/main HEAD"
    }
    
    mock_clone_proc = MagicMock()
    mock_clone_proc.returncode = 128
    mock_clone_proc.stderr = "fatal: early EOF\nfatal: fetch-pack: invalid index-pack output"
    mock_clone_proc.stdout = ""
    
    with patch("backend.app.git.repository_service.check_git_installed", return_value=True):
        with patch("backend.app.git.repository_service.check_remote_repository", return_value=mock_remote_success):
            with patch("subprocess.run", return_value=mock_clone_proc):
                res = validate_repository_input("https://github.com/owner/large-repo.git", workspace_base=temp_workspace)
                assert res["valid"] is False
                assert res["error_code"] == RepositoryErrorCode.CLONE_FAILED
                assert "early EOF" in res["details"]

