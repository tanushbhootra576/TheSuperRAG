"""
reranker.py -- Cross-Encoder Re-ranking Module for TheSuperRAG.

After hybrid retrieval fetches N candidates, the cross-encoder re-scores
each (query, passage) pair with full attention, producing much more accurate
relevance scores than the bi-encoder used for ANN retrieval.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2
  - ~70MB, downloads once from HuggingFace on first use
  - Fast inference (~10ms/pair on CPU)
  - Trained on the MS-MARCO passage ranking dataset
"""
import math
from typing import List, Tuple
from langchain_core.documents import Document


class CrossEncoderReranker:
    """
    Re-ranks retrieved documents using a cross-encoder model.
    Retrieves K candidates then re-ranks to the best top_k.
    """

    MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, model_name: str = None):
        model = model_name or self.MODEL_NAME
        print(f"  [>] Loading cross-encoder re-ranker: {model}...")
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model)
        print("  [OK] Re-ranker ready.")

    def rerank(
        self,
        query: str,
        docs: List[Document],
        top_k: int = 4
    ) -> Tuple[List[Document], List[float]]:
        """
        Re-rank documents by relevance to query.

        Args:
            query:  The user's search query.
            docs:   List of candidate documents from hybrid retrieval.
            top_k:  Number of top documents to return after re-ranking.

        Returns:
            (reranked_docs, scores) -- top_k docs sorted by descending score.
        """
        if not docs:
            return [], []

        # Build (query, passage) pairs for the cross-encoder
        pairs = [(query, doc.page_content) for doc in docs]
        raw_scores = self.model.predict(pairs)

        # Sort descending by score and take top_k
        scored = sorted(zip(raw_scores, docs), key=lambda x: x[0], reverse=True)
        top_docs = [doc for _, doc in scored[:top_k]]
        top_scores = [float(score) for score, _ in scored[:top_k]]

        return top_docs, top_scores

    def score_to_confidence(self, scores: List[float]) -> dict:
        """
        Converts cross-encoder raw scores to a human-readable confidence dict.

        Cross-encoder logit scores generally range from ~-10 to ~+10.
        We use tanh normalization to map to a 1-10 scale.

        Returns:
            {"score": int, "label": str, "emoji": str}
        """
        if not scores:
            return {"score": 0, "label": "Unknown", "emoji": "⚪"}

        best = max(scores)

        # tanh maps ℝ -> (-1, 1); scale to 1–10
        normalized = round(math.tanh(best / 5.0) * 4.5 + 5.5)
        normalized = max(1, min(10, normalized))

        if normalized >= 7:
            label, emoji = "High", "🟢"
        elif normalized >= 4:
            label, emoji = "Medium", "🟡"
        else:
            label, emoji = "Low", "🔴"

        return {"score": normalized, "label": label, "emoji": emoji}
