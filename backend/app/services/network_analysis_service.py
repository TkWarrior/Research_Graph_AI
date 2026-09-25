"""
Network Analysis Service — InfraNodus-style graph analytics.

Computes structural metrics on the co-occurrence / knowledge graph:
  • Betweenness Centrality  — most influential bridge nodes
  • Community Detection     — topical clusters (Louvain modularity)
  • Structural Gaps         — weakly connected cluster pairs (blind spots)
  • PageRank               — global importance ranking
  • Network Statistics      — density, clustering coefficient, diameter
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from loguru import logger

import networkx as nx

try:
    from community import community_louvain  # python-louvain
except ImportError:
    community_louvain = None
    logger.warning(
        "python-louvain not installed. "
        "Run: pip install python-louvain"
    )


# ── Predefined cluster color palette ────────────────────────────────
CLUSTER_COLORS = [
    "#4D96FF",  # Blue
    "#FF6B6B",  # Coral
    "#4ECDC4",  # Teal
    "#FFE66D",  # Yellow
    "#A29BFE",  # Lavender
    "#FF9F1C",  # Orange
    "#10AC84",  # Green
    "#F368E0",  # Pink
    "#00D2D3",  # Cyan
    "#EE5A24",  # Red-Orange
    "#C4E538",  # Lime
    "#FDA7DF",  # Light Pink
]


class NetworkAnalysisService:
    """Performs graph analytics on a node/edge structure."""

    # ─────────────────────────────────────────────────────────────────
    # Graph construction from raw data
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_nx_graph(
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> nx.Graph:
        """
        Convert our standard node/edge dicts into a NetworkX Graph.
        Supports both co-occurrence graphs (weight) and knowledge graphs.
        """
        G = nx.Graph()
        for n in nodes:
            name = n.get("name") or n.get("id")
            G.add_node(name, **n)
        for e in edges:
            src = e.get("source")
            tgt = e.get("target")
            weight = e.get("weight", 1)
            # Only pass weight, not the full dict (which also contains weight)
            G.add_edge(src, tgt, weight=weight)
        return G

    # ─────────────────────────────────────────────────────────────────
    # Full analysis (single call)
    # ─────────────────────────────────────────────────────────────────

    def full_analysis(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Run every available metric and return a combined result dict.
        This is the main entry-point for the analytics API.
        """
        G = self._build_nx_graph(nodes, edges)

        if G.number_of_nodes() == 0:
            return {
                "centrality": [],
                "communities": {"clusters": [], "modularity": 0},
                "gaps": [],
                "pagerank": [],
                "stats": self._empty_stats(),
            }

        centrality = self.betweenness_centrality(G)
        communities = self.detect_communities(G)
        gaps = self.find_structural_gaps(G, communities)
        pagerank = self.compute_pagerank(G)
        stats = self.network_stats(G)

        return {
            "centrality": centrality,
            "communities": communities,
            "gaps": gaps,
            "pagerank": pagerank,
            "stats": stats,
        }

    # ─────────────────────────────────────────────────────────────────
    # Individual metrics
    # ─────────────────────────────────────────────────────────────────

    def betweenness_centrality(
        self, G: nx.Graph, top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Betweenness centrality — nodes that act as bridges between
        different parts of the graph.  High centrality = high influence.
        """
        bc = nx.betweenness_centrality(G, weight="weight")
        ranked = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [
            {"name": name, "centrality": round(score, 4)}
            for name, score in ranked
        ]

    def detect_communities(self, G: nx.Graph) -> Dict[str, Any]:
        """
        Louvain community detection — groups nodes into topical clusters.
        Returns cluster assignments + modularity score.
        """
        if community_louvain is None:
            logger.warning("python-louvain not available, skipping community detection")
            return {"clusters": [], "modularity": 0, "node_communities": {}}

        if G.number_of_nodes() < 2:
            return {"clusters": [], "modularity": 0, "node_communities": {}}

        # Louvain partition
        partition = community_louvain.best_partition(G, weight="weight")
        modularity = community_louvain.modularity(partition, G, weight="weight")

        # Group nodes by cluster
        clusters_map: Dict[int, List[str]] = defaultdict(list)
        for node, cluster_id in partition.items():
            clusters_map[cluster_id].append(node)

        clusters = []
        for cluster_id, members in sorted(clusters_map.items()):
            color = CLUSTER_COLORS[cluster_id % len(CLUSTER_COLORS)]
            clusters.append({
                "id": cluster_id,
                "color": color,
                "members": members,
                "size": len(members),
            })

        return {
            "clusters": clusters,
            "modularity": round(modularity, 4),
            "node_communities": partition,  # {node_name: cluster_id}
        }

    def find_structural_gaps(
        self,
        G: nx.Graph,
        communities: Dict[str, Any],
        max_gaps: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Structural gaps — cluster pairs with very few or zero inter-cluster
        edges.  These represent 'blind spots' where new connections or
        research questions could be formed.
        """
        node_communities = communities.get("node_communities", {})
        clusters = communities.get("clusters", [])

        if len(clusters) < 2:
            return []

        # Count inter-cluster edges
        inter_edges: Dict[tuple, int] = defaultdict(int)
        for u, v in G.edges():
            cu = node_communities.get(u)
            cv = node_communities.get(v)
            if cu is not None and cv is not None and cu != cv:
                pair = tuple(sorted([cu, cv]))
                inter_edges[pair] += 1

        # Build all possible cluster pairs
        cluster_ids = [c["id"] for c in clusters]
        all_pairs = []
        for i, a in enumerate(cluster_ids):
            for b in cluster_ids[i + 1:]:
                pair = tuple(sorted([a, b]))
                count = inter_edges.get(pair, 0)
                all_pairs.append((pair, count))

        # Sort by fewest inter-edges (weakest connections first)
        all_pairs.sort(key=lambda x: x[1])

        # Format output
        cluster_lookup = {c["id"]: c for c in clusters}
        gaps = []
        for (ca, cb), edge_count in all_pairs[:max_gaps]:
            cluster_a = cluster_lookup[ca]
            cluster_b = cluster_lookup[cb]

            # Pick representative nodes (top by degree within each cluster)
            reps_a = self._top_nodes_in_cluster(G, cluster_a["members"], n=3)
            reps_b = self._top_nodes_in_cluster(G, cluster_b["members"], n=3)

            gaps.append({
                "cluster_a": {"id": ca, "color": cluster_a["color"], "top_nodes": reps_a},
                "cluster_b": {"id": cb, "color": cluster_b["color"], "top_nodes": reps_b},
                "inter_edges": edge_count,
                "gap_strength": "strong" if edge_count == 0 else "weak",
            })

        return gaps

    def compute_pagerank(
        self, G: nx.Graph, top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """PageRank — global importance based on link structure."""
        pr = nx.pagerank(G, weight="weight")
        ranked = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [
            {"name": name, "pagerank": round(score, 6)}
            for name, score in ranked
        ]

    def network_stats(self, G: nx.Graph) -> Dict[str, Any]:
        """High-level network statistics."""
        stats = {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "density": round(nx.density(G), 4),
            "avg_clustering": round(nx.average_clustering(G, weight="weight"), 4),
            "connected_components": nx.number_connected_components(G),
        }

        # Diameter only for connected graphs (expensive for large ones)
        if nx.is_connected(G) and G.number_of_nodes() <= 500:
            stats["diameter"] = nx.diameter(G)
        else:
            stats["diameter"] = None

        # Average degree
        degrees = [d for _, d in G.degree()]
        stats["avg_degree"] = round(sum(degrees) / len(degrees), 2) if degrees else 0

        return stats

    # ─────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _top_nodes_in_cluster(
        G: nx.Graph, members: List[str], n: int = 3
    ) -> List[str]:
        """Return top-n nodes in a cluster ranked by weighted degree."""
        scored = []
        for m in members:
            if G.has_node(m):
                scored.append((m, G.degree(m, weight="weight")))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in scored[:n]]

    @staticmethod
    def _empty_stats() -> Dict[str, Any]:
        return {
            "node_count": 0,
            "edge_count": 0,
            "density": 0,
            "avg_clustering": 0,
            "connected_components": 0,
            "diameter": None,
            "avg_degree": 0,
        }
