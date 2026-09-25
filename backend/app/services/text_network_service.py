"""
Text Network Analysis Service — InfraNodus-style co-occurrence graph builder.

Converts raw text into a network graph where:
- Nodes  = meaningful words/phrases (lemmatized, stop-words removed)
- Edges  = co-occurrence within a sliding window, weighted by frequency

This replaces the LLM-based extraction as the *primary* graph construction
method.  The LLM extraction is preserved as an optional "enhanced" mode.
"""

from typing import List, Dict, Any, Tuple
from collections import Counter
from loguru import logger

try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except OSError:
    _NLP = None
    logger.warning(
        "spaCy model 'en_core_web_sm' not found. "
        "Run: python -m spacy download en_core_web_sm"
    )


# POS tags we keep — nouns, proper nouns, verbs, adjectives
_KEEP_POS = {"NOUN", "PROPN", "VERB", "ADJ"}

# Additional custom stop-words to filter out low-signal tokens
_CUSTOM_STOPS = {
    "et", "al", "fig", "table", "study", "result", "paper",
    "method", "approach", "section", "chapter", "use", "provide",
    "include", "show", "make", "also", "however", "therefore",
}


class TextNetworkService:
    """Builds a co-occurrence graph from raw text using NLP."""

    def __init__(self, window_size: int = 5, min_weight: int = 1):
        """
        Args:
            window_size: Number of tokens in the sliding co-occurrence window.
            min_weight:  Minimum co-occurrence count to keep an edge.
        """
        if _NLP is None:
            raise RuntimeError(
                "spaCy model not loaded. Run: python -m spacy download en_core_web_sm"
            )
        self.nlp = _NLP
        self.window_size = window_size
        self.min_weight = min_weight

    # ─────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────

    def build_graph_from_text(self, text: str) -> Dict[str, Any]:
        """
        Build a co-occurrence graph from a single text block.

        Returns:
            {
                "nodes": [{"name": str, "frequency": int}],
                "edges": [{"source": str, "target": str, "weight": int}]
            }
        """
        tokens = self._extract_tokens(text)
        edges = self._build_cooccurrence(tokens)
        return self._format_output(tokens, edges)

    def build_graph_from_chunks(
        self, chunks: List[str]
    ) -> Dict[str, Any]:
        """
        Build a single merged co-occurrence graph from multiple text chunks.
        Each chunk is processed independently and the results are merged
        (edge weights are summed).
        """
        all_tokens: List[str] = []
        merged_edges: Counter = Counter()

        for chunk in chunks:
            tokens = self._extract_tokens(chunk)
            all_tokens.extend(tokens)
            chunk_edges = self._build_cooccurrence(tokens)
            merged_edges.update(chunk_edges)

        return self._format_output(all_tokens, merged_edges)

    # ─────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────

    def _extract_tokens(self, text: str) -> List[str]:
        """
        Tokenize, remove stop-words, filter by POS, and lemmatize.
        Returns a flat list of cleaned token strings in document order.
        """
        doc = self.nlp(text)
        tokens = []
        for token in doc:
            # Skip stop-words, punctuation, whitespace, numbers, short tokens
            if (
                token.is_stop
                or token.is_punct
                or token.is_space
                or token.like_num
                or len(token.text) < 3
            ):
                continue

            # Keep only meaningful POS tags
            if token.pos_ not in _KEEP_POS:
                continue

            lemma = token.lemma_.lower().strip()

            # Skip custom stop-words
            if lemma in _CUSTOM_STOPS:
                continue

            tokens.append(lemma)

        return tokens

    def _build_cooccurrence(
        self, tokens: List[str]
    ) -> Counter:
        """
        Sliding-window co-occurrence.
        For every pair of tokens within the window, increment the edge weight.
        Pairs are stored as sorted tuples so (A,B) == (B,A).
        """
        edges: Counter = Counter()
        for i in range(len(tokens)):
            for j in range(i + 1, min(i + self.window_size, len(tokens))):
                if tokens[i] == tokens[j]:
                    continue  # skip self-loops
                pair = tuple(sorted([tokens[i], tokens[j]]))
                edges[pair] += 1
        return edges

    def _format_output(
        self, tokens: List[str], edges: Counter
    ) -> Dict[str, Any]:
        """
        Format tokens + edge counter into the standard node/edge dict,
        filtering out edges below the min_weight threshold.
        """
        # Count token frequencies for node sizing
        freq = Counter(tokens)

        # Filter edges
        filtered_edges = {
            pair: w for pair, w in edges.items() if w >= self.min_weight
        }

        # Collect only nodes that appear in at least one surviving edge
        active_nodes = set()
        for a, b in filtered_edges:
            active_nodes.add(a)
            active_nodes.add(b)

        nodes = [
            {"name": name, "frequency": freq.get(name, 1)}
            for name in active_nodes
        ]

        edge_list = [
            {"source": a, "target": b, "weight": w}
            for (a, b), w in filtered_edges.items()
        ]

        logger.info(
            f"Text network built: {len(nodes)} nodes, {len(edge_list)} edges "
            f"(window={self.window_size}, min_weight={self.min_weight})"
        )

        return {"nodes": nodes, "edges": edge_list}
