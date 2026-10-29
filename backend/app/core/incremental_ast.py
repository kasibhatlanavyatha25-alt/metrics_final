import logging
from typing import Dict, List, Tuple, Optional, Any
from app.models.schemas import IncrementalStats, MetricVector
from app.storage.cache import ast_cache, ASTCache
from app.core.git_interceptor import GitInterceptor
from app.core.metrics_engine import parse_and_extract_metrics, extract_metrics_from_ast

logger = logging.getLogger("software_dna.incremental_ast")


class IncrementalASTEngine:
    """
    Incrementally parses changed Java source files into AST representations,
    maintaining an AST cache keyed by (repository, file_path, commit_sha).
    Reuses cached ASTs for unchanged files to optimize performance.
    """

    def __init__(self, cache: Optional[ASTCache] = None):
        self.cache = cache or ast_cache

    def analyze_commit(
        self,
        git_interceptor: GitInterceptor,
        commit_sha: str,
        repo_name: str = "mock_repo",
    ) -> Tuple[Dict[str, Any], Dict[str, MetricVector], IncrementalStats, List[str]]:
        """
        Incrementally processes all Java files at `commit_sha`.
        Returns:
            - ast_map: Dict[file_path, AST]
            - metrics_map: Dict[class_name, MetricVector]
            - stats: IncrementalStats
            - changed_files: List[str]
        """
        all_java_files = git_interceptor.get_all_java_files_at_commit(commit_sha)
        
        # Get commit object to find changed files
        repo = git_interceptor.get_repo()
        commit_obj = repo.commit(commit_sha)
        changed_files = git_interceptor.get_changed_files_for_commit(commit_obj)

        files_total = len(all_java_files)
        files_changed = len(changed_files)
        files_parsed = 0
        files_reused = 0

        ast_map: Dict[str, Any] = {}
        all_metrics: Dict[str, MetricVector] = {}

        for file_path in all_java_files:
            # Check if file changed in this commit
            is_changed = file_path in changed_files

            if not is_changed:
                # Attempt to retrieve existing cached AST from prior commits
                cached_ast = self.cache.find_latest_ast_for_file(repo_name, file_path)
                if cached_ast is not None:
                    ast_map[file_path] = cached_ast
                    self.cache.put(repo_name, file_path, commit_sha, cached_ast)
                    files_reused += 1
                    
                    # Extract metrics for file
                    content = git_interceptor.get_file_content_at_commit(file_path, commit_sha)
                    _, m_dict = parse_and_extract_metrics(content, file_path)
                    all_metrics.update(m_dict)
                    continue

            # If changed or not cached, read file content and parse
            source_content = git_interceptor.get_file_content_at_commit(file_path, commit_sha)
            ast_tree, metrics_dict = parse_and_extract_metrics(source_content, file_path)
            
            if ast_tree is not None:
                self.cache.put(repo_name, file_path, commit_sha, ast_tree)
                ast_map[file_path] = ast_tree
            
            all_metrics.update(metrics_dict)
            files_parsed += 1

        hit_rate = round((files_reused / files_total) * 100, 1) if files_total > 0 else 0.0

        stats = IncrementalStats(
            files_total=files_total,
            files_changed=files_changed,
            files_parsed=files_parsed,
            files_reused_from_cache=files_reused,
            cache_hit_rate=hit_rate,
        )

        logger.info(
            f"[AST] Commit {commit_sha[:7]} | Total: {files_total} | Changed: {files_changed} | "
            f"Parsed: {files_parsed} | Reused: {files_reused} | Cache Hit Rate: {hit_rate}%"
        )

        return ast_map, all_metrics, stats, changed_files
