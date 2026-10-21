"""Build and save BM25 and Dense retrieval indexes from processed corpus."""

import argparse
import logging
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval.bm25 import BM25Retriever
from src.retrieval.corpus import CorpusManager
from src.retrieval.dense import DenseRetriever
from src.utils.config import load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def build_indexes(config_path: str = "configs/default.yaml") -> None:
    config = load_config(config_path)
    retrieval_cfg = config.get("retrieval", {})

    corpus_path = Path(retrieval_cfg.get("corpus_path", "data/processed/corpus.jsonl"))
    bm25_index_path = Path(retrieval_cfg.get("bm25_index_path", "data/indexes/bm25.pkl"))
    dense_index_path = Path(retrieval_cfg.get("dense_index_path", "data/indexes/dense_index.pt"))
    dense_model_name = retrieval_cfg.get("dense_model_name", "sentence-transformers/all-MiniLM-L6-v2")
    device = retrieval_cfg.get("device", "auto")

    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus not found at {corpus_path}. Run prepare_data.py first.")

    logger.info(f"Loading corpus from {corpus_path}...")
    corpus_manager = CorpusManager(corpus_path)
    logger.info(f"Loaded {len(corpus_manager)} documents.")

    # 1. Build and save BM25 index
    logger.info(f"Building BM25 index...")
    bm25_retriever = BM25Retriever(corpus_manager)
    bm25_retriever.save_index(bm25_index_path)
    logger.info(f"BM25 index saved to {bm25_index_path}")

    # 2. Build and save Dense index
    logger.info(f"Building Dense index using model '{dense_model_name}' on device '{device}'...")
    dense_retriever = DenseRetriever(corpus_manager, model_name=dense_model_name, device=device)
    dense_retriever.build_index()
    dense_retriever.save_index(dense_index_path)
    logger.info(f"Dense index saved to {dense_index_path}")

    logger.info("Indexing completed successfully.")


def main():
    parser = argparse.ArgumentParser(description="Build retrieval indexes")
    parser.add_argument("--config", type=str, default="configs/default.yaml", help="Path to config file")
    args = parser.parse_args()
    build_indexes(args.config)


if __name__ == "__main__":
    main()
