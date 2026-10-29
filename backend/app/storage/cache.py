import logging
from typing import Dict, Tuple, Any, Optional

logger = logging.getLogger("software_dna.cache")


class ASTCache:
    """
    Incremental AST cache keyed by (repository, file_path, commit_sha).
    Reuses parsed AST trees for unchanged files across commit boundaries.
    """

    def __init__(self):
        self._cache: Dict[Tuple[str, str, str], Any] = {}
        self._file_content_hash: Dict[Tuple[str, str], str] = {}
        self.hits: int = 0
        self.misses: int = 0

    def make_key(self, repo: str, file_path: str, commit_sha: str) -> Tuple[str, str, str]:
        # Normalize paths
        norm_path = file_path.replace("\\", "/").lstrip("/")
        return (repo, norm_path, commit_sha)

    def get(self, repo: str, file_path: str, commit_sha: str) -> Optional[Any]:
        key = self.make_key(repo, file_path, commit_sha)
        if key in self._cache:
            self.hits += 1
            logger.debug(f"[AST Cache HIT] {file_path} @ {commit_sha[:7]}")
            return self._cache[key]
        self.misses += 1
        logger.debug(f"[AST Cache MISS] {file_path} @ {commit_sha[:7]}")
        return None

    def put(self, repo: str, file_path: str, commit_sha: str, ast_tree: Any) -> None:
        key = self.make_key(repo, file_path, commit_sha)
        self._cache[key] = ast_tree

    def find_latest_ast_for_file(self, repo: str, file_path: str) -> Optional[Any]:
        """Lookup prior commit AST if file content hasn't changed."""
        norm_path = file_path.replace("\\", "/").lstrip("/")
        for (r, f, _sha), tree in reversed(list(self._cache.items())):
            if r == repo and f == norm_path:
                return tree
        return None

    def clear(self) -> None:
        self._cache.clear()
        self._file_content_hash.clear()
        self.hits = 0
        self.misses = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return round((self.hits / total) * 100, 1) if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "cached_entries": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": self.hit_rate
        }


# Global singleton instance
ast_cache = ASTCache()
