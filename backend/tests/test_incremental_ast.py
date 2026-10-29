import pytest
from app.storage.cache import ASTCache
from app.core.metrics_engine import parse_and_extract_metrics


def test_ast_cache_reuse():
    cache = ASTCache()
    repo = "test_repo"
    file_path = "src/PaymentService.java"
    commit1 = "sha_v1"
    commit2 = "sha_v2"

    source = "package com.test; public class PaymentService { public void pay() {} }"
    tree, _ = parse_and_extract_metrics(source, file_path)

    cache.put(repo, file_path, commit1, tree)

    # Reused lookup
    cached = cache.find_latest_ast_for_file(repo, file_path)
    assert cached is not None
    assert cache.hits == 0  # find_latest does not increment direct hit

    # Direct get
    direct = cache.get(repo, file_path, commit1)
    assert direct is not None
    assert cache.hits == 1

    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["cached_entries"] == 1
