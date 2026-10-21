"""Unit tests for evidence retrieval (BM25, Dense, Hybrid)."""

import pytest
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.corpus import CorpusManager
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever


@pytest.fixture
def corpus_manager():
    return CorpusManager("data/processed/corpus.jsonl")


def test_bm25_retrieval(corpus_manager):
    bm25 = BM25Retriever(corpus_manager)
    results = bm25.search("Aleister Crowley occultist magician", top_k=3)
    assert len(results) > 0
    assert any("Crowley" in r.text for r in results)


def test_dense_retrieval(corpus_manager):
    dense = DenseRetriever(corpus_manager, index_path="data/indexes/dense_index.pt")
    results = dense.search("Reign Over Me American drama film", top_k=3)
    assert len(results) > 0
    assert any("Reign" in r.text for r in results)


def test_hybrid_retrieval(corpus_manager):
    bm25 = BM25Retriever(corpus_manager)
    dense = DenseRetriever(corpus_manager, index_path="data/indexes/dense_index.pt")
    hybrid = HybridRetriever(bm25, dense)
    results = hybrid.search("Margaret Thatcher British Prime Minister", top_k=3)
    assert len(results) > 0
    assert any("Thatcher" in r.text for r in results)


def test_irrelevant_evidence_handling(corpus_manager):
    bm25 = BM25Retriever(corpus_manager)
    # Query with random out-of-domain words
    results = bm25.search("xyzqwe completely unrelated nonsensical query 9999", top_k=3)
    # BM25 should either return empty or low scores
    assert len(results) == 0 or all(r.retrieval_score < 0.5 for r in results)
