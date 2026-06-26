import numpy as np
import re
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, CrossEncoder

class GroundingDetector:
    def __init__(self):
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.nli_model = CrossEncoder("cross-encoder/nli-deberta-v3-small")
        
    def _split_sentences(self, text: str) -> List[str]:
        text = re.sub(r'\[\d+\]', '', text)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]

    def _cosine_similarity(self, a, b):
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0: return 0.0
        return np.dot(a, b) / (norm_a * norm_b)

    def evaluate(self, answer: str, chunks: List[str]) -> Dict[str, Any]:
        sentences = self._split_sentences(answer)
        if not sentences or not chunks:
            return {
                "overall_score": 1.0,
                "ungrounded_sentences": [],
                "contradictions": [],
                "verdict": "uncertain",
                "sentence_details": []
            }
            
        chunk_embeddings = self.embed_model.encode(chunks)
        
        sentence_details = []
        ungrounded_sentences = []
        contradictions = []
        total_score = 0
        
        for sent in sentences:
            sent_emb = self.embed_model.encode(sent)
            sims = [self._cosine_similarity(sent_emb, ce) for ce in chunk_embeddings]
            max_sim = max(sims)
            
            top_indices = np.argsort(sims)[-2:]
            
            nli_results = []
            for idx in top_indices:
                scores = self.nli_model.predict([chunks[idx], sent])
                label_idx = np.argmax(scores)
                # nli-deberta-v3-small mapping: 0: contradiction, 1: entailment, 2: neutral
                if label_idx == 0: label = "contradiction"
                elif label_idx == 1: label = "entailment"
                else: label = "neutral"
                nli_results.append((label, idx))
                
            best_label = "neutral"
            contradiction_idx = -1
            if any(l == "entailment" for l, _ in nli_results):
                best_label = "entailment"
            elif any(l == "contradiction" for l, _ in nli_results):
                best_label = "contradiction"
                contradiction_idx = [i for l, i in nli_results if l == "contradiction"][0]
                
            grounded = (max_sim >= 0.35) and (best_label == "entailment")
            
            sentence_details.append({
                "sentence": sent,
                "cosine_sim": float(max_sim),
                "nli_label": best_label,
                "grounded": grounded
            })
            
            if not grounded:
                ungrounded_sentences.append(sent)
                
            if best_label == "contradiction":
                contradictions.append({"sentence": sent, "chunk_index": int(contradiction_idx)})
                total_score += 0.0
            elif best_label == "entailment":
                total_score += 1.0
            else:
                total_score += 0.5
                
        overall = total_score / len(sentences)
        if contradictions:
            verdict = "hallucinated"
        elif overall >= 0.8:
            verdict = "grounded"
        else:
            verdict = "uncertain"
            
        return {
            "overall_score": float(overall),
            "ungrounded_sentences": ungrounded_sentences,
            "contradictions": contradictions,
            "verdict": verdict,
            "sentence_details": sentence_details
        }
