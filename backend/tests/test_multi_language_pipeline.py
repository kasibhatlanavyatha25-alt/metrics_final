import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal, init_db
from backend.models import Project, Version, ClassMetric, ESDIResult, DNAProfile, Mutation
from backend.app.core.analyzer_adapters import (
    default_registry, JavaAnalyzer, PythonAnalyzer, JavaScriptTypeScriptAnalyzer
)
from backend.repo_manager import RepoManager
from backend.analyzer import RepositoryAnalyzer
from git import Repo

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()


def create_mock_git_repo(directory: str, files_by_commit: list):
    """Creates a local Git repository with specified commit files."""
    repo = Repo.init(directory)
    for idx, (msg, files) in enumerate(files_by_commit):
        for fpath, content in files.items():
            full_path = os.path.join(directory, fpath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            repo.index.add([fpath])
        repo.index.commit(msg)
    return repo


def test_adapters_metric_extraction():
    """Unit test each language analyzer directly."""
    # 1. Java
    java_code = """
    package com.example.service;
    public class OrderProcessor {
        private String orderId;
        private int totalAmount;
        
        public void process(int count) {
            if (count > 0 && totalAmount > 100) {
                for (int i = 0; i < count; i++) {
                    System.out.println("Processing: " + orderId);
                }
            }
        }
    }
    """
    java_metrics = JavaAnalyzer().analyze_source("OrderProcessor.java", java_code)
    assert len(java_metrics) == 1
    assert java_metrics[0].class_name == "OrderProcessor"
    assert java_metrics[0].wmc >= 3
    assert java_metrics[0].language == "Java"

    # 2. Python
    py_code = """
import os
import sys

class PaymentManager:
    def __init__(self, key: str):
        self.key = key
        self.balance = 0

    def charge(self, amount: int) -> bool:
        if amount > 0 and self.balance >= amount:
            self.balance -= amount
            return True
        elif amount <= 0:
            return False
        return False
"""
    py_metrics = PythonAnalyzer().analyze_source("payment.py", py_code)
    assert len(py_metrics) == 1
    assert py_metrics[0].class_name == "PaymentManager"
    assert py_metrics[0].wmc >= 3
    assert py_metrics[0].cbo >= 2
    assert py_metrics[0].language == "Python"

    # 3. JavaScript / TypeScript
    ts_code = """
import { HttpClient } from './http';

export class UserService {
    private client: HttpClient;
    private users: string[] = [];

    constructor(client: HttpClient) {
        this.client = client;
    }

    public async getUser(id: string): Promise<string> {
        if (!id) {
            throw new Error("Invalid id");
        }
        return this.users.find(u => u === id) || "";
    }
}
"""
    ts_metrics = JavaScriptTypeScriptAnalyzer().analyze_source("user.service.ts", ts_code)
    assert len(ts_metrics) == 1
    assert ts_metrics[0].class_name == "UserService"
    assert ts_metrics[0].wmc >= 2


def test_testcase_1_python_only_repo():
    """
    TEST 1: Python-only Git repository
    Expected:
    - Repository validation = PASS
    - Python detected correctly
    - Java files = 0
    - Python analyzer runs
    - Software DNA generated
    - Mutation analysis generated
    - ESDI generated
    """
    temp_dir = tempfile.mkdtemp(prefix="test_py_repo_")
    try:
        commits = [
            ("Initial Python commit", {
                "calculator.py": "class Calculator:\n    def add(self, a, b):\n        return a + b\n",
                "utils.py": "def format_num(n):\n    return f'{n:.2f}'\n"
            }),
            ("Add multiplication & complexity", {
                "calculator.py": "class Calculator:\n    def add(self, a, b):\n        return a + b\n    def multiply(self, a, b):\n        res = 0\n        if b > 0:\n            for _ in range(b): res += a\n        return res\n"
            }),
            ("Add divide & branch mutation", {
                "calculator.py": "class Calculator:\n    def add(self, a, b):\n        return a + b\n    def multiply(self, a, b):\n        res = 0\n        if b > 0:\n            for _ in range(b): res += a\n        return res\n    def divide(self, a, b):\n        if b == 0:\n            raise ValueError('Zero division')\n        return a / b\n"
            })
        ]
        create_mock_git_repo(temp_dir, commits)

        # 1. Validation check
        mgr = RepoManager(temp_dir)
        val = mgr.validate_repository()
        assert val["is_valid"] is True
        assert val["total_java_files"] == 0
        assert val["has_java_files"] is False
        assert "Python" in val["detected_languages"]
        assert val["analyzable_files_count"] >= 2
        assert "Python" in val["supported_analyzers"]

        # 2. Run Analysis pipeline
        db = SessionLocal()
        try:
            analyzer = RepositoryAnalyzer(db, temp_dir)
            result = analyzer.run_full_analysis()
            assert result["success"] is True
            assert result["project_id"] is not None
            assert result["total_versions"] == 3
            assert result["esdi_score"] >= 0.0

            # Query database to verify Software DNA, mutations, and ESDI generated
            p_id = result["project_id"]
            proj = db.query(Project).get(p_id)
            assert proj.language == "Python"
            
            esdis = db.query(ESDIResult).filter_by(project_id=p_id).all()
            assert len(esdis) >= 1
            
            dnas = db.query(DNAProfile).join(Version).filter(Version.project_id == p_id).all()
            assert len(dnas) == 3
            
            mutations = db.query(Mutation).join(Version, Mutation.version_id == Version.id).filter(Version.project_id == p_id).all()
            assert len(mutations) >= 1
            
            # Check Python classes
            cms = db.query(ClassMetric).join(Version).filter(Version.project_id == p_id).all()
            class_names = {cm.class_name for cm in cms}
            assert "Calculator" in class_names
        finally:
            db.close()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_testcase_2_java_only_repo():
    """
    TEST 2: Java-only Git repository
    Expected:
    - Repository validation = PASS
    - Java detected correctly
    - Java analyzer runs
    - Software DNA generated
    - Mutation analysis generated
    - ESDI generated
    """
    temp_dir = tempfile.mkdtemp(prefix="test_java_repo_")
    try:
        commits = [
            ("Initial Java commit", {
                "src/Service.java": "package com.app;\npublic class Service {\n    public void doWork() {}\n}\n"
            }),
            ("Evolve Java commit", {
                "src/Service.java": "package com.app;\npublic class Service {\n    public void doWork() {\n        for (int i=0; i<10; i++) { if (i%2 == 0) System.out.println(i); }\n    }\n}\n"
            })
        ]
        create_mock_git_repo(temp_dir, commits)

        mgr = RepoManager(temp_dir)
        val = mgr.validate_repository()
        assert val["is_valid"] is True
        assert val["total_java_files"] == 1
        assert "Java" in val["detected_languages"]
        assert "Java" in val["supported_analyzers"]

        db = SessionLocal()
        try:
            analyzer = RepositoryAnalyzer(db, temp_dir)
            result = analyzer.run_full_analysis()
            assert result["success"] is True
            assert result["project_id"] is not None
            assert result["total_versions"] == 2
            assert result["esdi_score"] >= 0.0

            p_id = result["project_id"]
            proj = db.query(Project).get(p_id)
            assert proj.language == "Java"
            
            dnas = db.query(DNAProfile).join(Version).filter(Version.project_id == p_id).all()
            assert len(dnas) == 2
            
            cms = db.query(ClassMetric).join(Version).filter(Version.project_id == p_id).all()
            assert any(cm.class_name == "Service" for cm in cms)
        finally:
            db.close()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_testcase_3_mixed_java_python_repo():
    """
    TEST 3: Mixed Java + Python repository
    Expected:
    - Repository validation = PASS
    - Both languages detected correctly
    - Corresponding analyzers run
    - Unified Software DNA generated
    - Mutation analysis generated
    - ESDI generated
    """
    temp_dir = tempfile.mkdtemp(prefix="test_mixed_repo_")
    try:
        commits = [
            ("Initial mixed commit", {
                "backend/Server.java": "package com.mixed;\npublic class Server { public void start() {} }\n",
                "scripts/deploy.py": "class Deployer:\n    def deploy(self):\n        pass\n"
            }),
            ("Evolve both Java and Python", {
                "backend/Server.java": "package com.mixed;\npublic class Server {\n    public void start() {\n        if (true) { System.out.println('running'); }\n    }\n}\n",
                "scripts/deploy.py": "class Deployer:\n    def deploy(self):\n        for step in [1, 2, 3]:\n            if step > 1: print(step)\n"
            })
        ]
        create_mock_git_repo(temp_dir, commits)

        mgr = RepoManager(temp_dir)
        val = mgr.validate_repository()
        assert val["is_valid"] is True
        assert "Java" in val["detected_languages"]
        assert "Python" in val["detected_languages"]
        assert "Java" in val["supported_analyzers"]
        assert "Python" in val["supported_analyzers"]

        db = SessionLocal()
        try:
            analyzer = RepositoryAnalyzer(db, temp_dir)
            result = analyzer.run_full_analysis()
            assert result["success"] is True
            assert result["project_id"] is not None
            assert result["total_versions"] == 2
            assert result["esdi_score"] >= 0.0
            
            # Verify unified class metrics contain both Server and Deployer
            p_id = result["project_id"]
            cms = db.query(ClassMetric).join(Version).filter(Version.project_id == p_id).all()
            class_names = {cm.class_name for cm in cms}
            assert "Server" in class_names
            assert "Deployer" in class_names
        finally:
            db.close()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_testcase_4_unsupported_language_repo():
    """
    TEST 4: Unsupported-language repository (e.g. Rust / Go repo)
    Expected:
    - Repository validation = PASS
    - Language detected
    - Clear message that no compatible analyzer is currently available
    - No fabricated metrics
    - No fabricated DNA
    - No fabricated mutation results
    """
    temp_dir = tempfile.mkdtemp(prefix="test_rust_repo_")
    try:
        commits = [
            ("Initial Rust commit", {
                "main.rs": "fn main() { println!(\"Hello, world!\"); }\n",
                "lib.rs": "pub fn add(a: i32, b: i32) -> i32 { a + b }\n"
            }),
            ("Add function", {
                "lib.rs": "pub fn add(a: i32, b: i32) -> i32 { a + b }\npub fn mul(a: i32, b: i32) -> i32 { a * b }\n"
            })
        ]
        create_mock_git_repo(temp_dir, commits)

        mgr = RepoManager(temp_dir)
        val = mgr.validate_repository()
        
        # 1. Repository must still be accepted / PASS validation
        assert val["is_valid"] is True
        # 2. Detected language shown
        assert "Rust" in val["detected_languages"]
        assert val["detected_languages"]["Rust"] == 2
        # 3. Compatible analyzer unavailable
        assert val["has_analyzable_files"] is False
        assert val["analyzable_files_count"] == 0
        assert val["warning_message"] is not None
        assert "no compatible analyzer is currently available" in val["warning_message"]

        # 4. Attempting analysis fails cleanly with error message and no fabricated DNA/metrics
        db = SessionLocal()
        try:
            analyzer = RepositoryAnalyzer(db, temp_dir)
            res = analyzer.run_full_analysis()
            assert res["success"] is False
            assert "no compatible analyzer is currently available" in res["error"]
        finally:
            db.close()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
