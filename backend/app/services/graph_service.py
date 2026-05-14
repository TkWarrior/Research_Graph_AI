"""
Service for managing the Knowledge Graph using Neo4j.

Supports document-scoped graphs: each node and edge is tagged with a
document_id so graphs from different documents can coexist in the same
Neo4j database and be queried independently.
"""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from loguru import logger

from app.config import get_settings
from app.services.extraction_service import Entity, Relationship

settings = get_settings()


class GraphService:
    """Handles all interactions with the Neo4j database."""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        self._create_constraints()

    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()

    def _create_constraints(self):
        """Create indexes for efficient document-scoped queries."""
        queries = [
            # Composite index on name + document_id for fast lookups
            "CREATE INDEX entity_doc_idx IF NOT EXISTS FOR (e:Entity) ON (e.name, e.document_id)",
            # Index on document_id alone for full-document queries
            "CREATE INDEX entity_docid_idx IF NOT EXISTS FOR (e:Entity) ON (e.document_id)",
        ]
        try:
            with self.driver.session() as session:
                for q in queries:
                    session.run(q)
        except Exception as e:
            print(f"Note on index creation: {e}")

    # ─────────────────────────────────────────────────────────────────
    # LLM-extracted entity/relationship storage
    # ─────────────────────────────────────────────────────────────────

    def create_entities(self, entities: List[Entity], document_id: str = None) -> None:
        """Create or merge multiple entities into the graph, scoped by document_id."""
        if not entities:
            return

        query = """
        UNWIND $entities AS e
        MERGE (n:Entity {name: e.name, document_id: e.document_id})
        SET n.type = e.type, n.description = e.description
        """
        
        entities_data = [
            {
                "name": ent.name,
                "type": ent.type,
                "description": ent.description,
                "document_id": document_id or "global",
            }
            for ent in entities
        ]

        with self.driver.session() as session:
            session.run(query, entities=entities_data)

    def create_relationships(self, relationships: List[Relationship], document_id: str = None) -> None:
        """Create relationships between entities within the same document scope."""
        if not relationships:
            return

        doc_id = document_id or "global"

        query = """
        UNWIND $rels AS r
        MATCH (source:Entity {name: r.source, document_id: $doc_id})
        MATCH (target:Entity {name: r.target, document_id: $doc_id})
        MERGE (source)-[rel:RELATED_TO {type: r.type}]->(target)
        SET rel.description = r.description, rel.document_id = $doc_id
        """
        
        rels_data = [
            {
                "source": r.source,
                "target": r.target,
                "type": r.type.upper().replace(" ", "_"),
                "description": r.description,
            }
            for r in relationships
        ]

        with self.driver.session() as session:
            session.run(query, rels=rels_data, doc_id=doc_id)

    # ─────────────────────────────────────────────────────────────────
    # Query methods (document-scoped)
    # ─────────────────────────────────────────────────────────────────

    def query_subgraph(self, entity_name: str, depth: int = 1, document_id: str = None) -> Dict[str, Any]:
        """Retrieve the neighborhood graph around a specific entity."""
        if document_id:
            query = f"""
            MATCH path = (e:Entity {{name: $name, document_id: $doc_id}})-[*1..{int(depth)}]-(connected)
            WHERE connected.document_id = $doc_id
            RETURN path
            """
            params = {"name": entity_name, "doc_id": document_id}
        else:
            query = f"""
            MATCH path = (e:Entity {{name: $name}})-[*1..{int(depth)}]-(connected)
            RETURN path
            """
            params = {"name": entity_name}

        with self.driver.session() as session:
            result = session.run(query, **params)
            return self._format_graph_result(result)

    def search_entities(self, search_term: str, limit: int = 10, document_id: str = None) -> List[Dict[str, Any]]:
        """Search for entities matching a term in their name or description."""
        if document_id:
            query = """
            MATCH (e:Entity {document_id: $doc_id})
            WHERE toLower(e.name) CONTAINS toLower($term) 
               OR toLower(e.description) CONTAINS toLower($term)
            RETURN e.name AS name, e.type AS type, e.description AS description
            LIMIT $limit
            """
            params = {"term": search_term, "limit": limit, "doc_id": document_id}
        else:
            query = """
            MATCH (e:Entity)
            WHERE toLower(e.name) CONTAINS toLower($term) 
               OR toLower(e.description) CONTAINS toLower($term)
            RETURN e.name AS name, e.type AS type, e.description AS description
            LIMIT $limit
            """
            params = {"term": search_term, "limit": limit}

        with self.driver.session() as session:
            result = session.run(query, **params)
            return [record.data() for record in result]

    def get_full_graph(self, limit: int = 500, document_id: str = None) -> Dict[str, Any]:
        """
        Retrieve the graph for frontend visualization.
        If document_id is provided, only return nodes/edges for that document.
        Otherwise, return the entire graph.
        """
        if document_id:
            query = """
            MATCH (n:Entity {document_id: $doc_id})
            OPTIONAL MATCH (n)-[r]-(m:Entity {document_id: $doc_id})
            RETURN n, r, m
            LIMIT $limit
            """
            params = {"limit": limit, "doc_id": document_id}
        else:
            query = """
            MATCH (n:Entity)
            OPTIONAL MATCH (n)-[r]-(m:Entity)
            RETURN n, r, m
            LIMIT $limit
            """
            params = {"limit": limit}

        with self.driver.session() as session:
            result = session.run(query, **params)
            return self._format_graph_result(result)

    def get_graph_stats(self, document_id: str = None) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        if document_id:
            query_nodes = "MATCH (n:Entity {document_id: $doc_id}) RETURN count(n) as node_count"
            query_edges = "MATCH (a:Entity {document_id: $doc_id})-[r]-(b:Entity {document_id: $doc_id}) RETURN count(r) as edge_count"
            query_top = """
            MATCH (n:Entity {document_id: $doc_id})-[r]-() 
            RETURN n.name as name, count(r) as degree 
            ORDER BY degree DESC LIMIT 5
            """
            params = {"doc_id": document_id}
        else:
            query_nodes = "MATCH (n:Entity) RETURN count(n) as node_count"
            query_edges = "MATCH ()-[r]->() RETURN count(r) as edge_count"
            query_top = """
            MATCH (n:Entity)-[r]-() 
            RETURN n.name as name, count(r) as degree 
            ORDER BY degree DESC LIMIT 5
            """
            params = {}

        stats = {}
        with self.driver.session() as session:
            stats["node_count"] = session.run(query_nodes, **params).single()["node_count"]
            stats["edge_count"] = session.run(query_edges, **params).single()["edge_count"]
            stats["most_connected"] = [record.data() for record in session.run(query_top, **params)]
            
        return stats

    def cypher_query(self, query: str, parameters: dict = None) -> List[Dict[str, Any]]:
        """Run arbitrary Cypher for advanced queries by agents."""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def delete_document_graph(self, document_id: str) -> Dict[str, int]:
        """Delete all nodes and relationships for a specific document."""
        query = """
        MATCH (n:Entity {document_id: $doc_id})
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """
        with self.driver.session() as session:
            result = session.run(query, doc_id=document_id)
            record = result.single()
            count = record["deleted_count"] if record else 0
            logger.info(f"Deleted {count} nodes for document {document_id}")
            return {"deleted_nodes": count}

    # ─────────────────────────────────────────────────────────────────
    # Co-occurrence graph storage (InfraNodus-style)
    # ─────────────────────────────────────────────────────────────────

    def create_cooccurrence_nodes(self, nodes: List[Dict[str, Any]], document_id: str = None) -> None:
        """
        Create or merge co-occurrence word nodes into the graph.
        Each node is scoped to a document_id.
        """
        if not nodes:
            return

        doc_id = document_id or "global"

        query = """
        UNWIND $nodes AS n
        MERGE (e:Entity {name: n.name, document_id: $doc_id})
        SET e.frequency = COALESCE(e.frequency, 0) + n.frequency,
            e.type = COALESCE(e.type, 'CONCEPT')
        """

        with self.driver.session() as session:
            session.run(query, nodes=nodes, doc_id=doc_id)
            logger.info(f"Merged {len(nodes)} co-occurrence nodes for doc {doc_id}")

    def create_cooccurrence_edges(self, edges: List[Dict[str, Any]], document_id: str = None) -> None:
        """
        Create or merge co-occurrence edges with cumulative weights.
        Edges are scoped to the same document_id.
        """
        if not edges:
            return

        doc_id = document_id or "global"

        query = """
        UNWIND $edges AS e
        MATCH (source:Entity {name: e.source, document_id: $doc_id})
        MATCH (target:Entity {name: e.target, document_id: $doc_id})
        MERGE (source)-[r:CO_OCCURS]-(target)
        SET r.weight = COALESCE(r.weight, 0) + e.weight,
            r.type = 'CO_OCCURS',
            r.document_id = $doc_id
        """

        with self.driver.session() as session:
            session.run(query, edges=edges, doc_id=doc_id)
            logger.info(f"Merged {len(edges)} co-occurrence edges for doc {doc_id}")

    # ─────────────────────────────────────────────────────────────────
    # Formatting helper
    # ─────────────────────────────────────────────────────────────────

    def _format_graph_result(self, neo4j_result) -> Dict[str, Any]:
        """Helper to format Neo4j paths/nodes into standard node/edge lists for frontend."""
        nodes = {}        # element_id -> node dict
        raw_edges = []     # edges with element_id references
        id_to_name = {}    # element_id -> node name (for resolving edges)

        for record in neo4j_result:
            for key in record.keys():
                item = record[key]
                if item is None:
                    continue
                
                # Check if it's a Path
                if hasattr(item, "nodes") and hasattr(item, "relationships"):
                    for n in item.nodes:
                        name = n.get("name")
                        id_to_name[n.element_id] = name
                        nodes[n.element_id] = {
                            "id": name,
                            "name": name,
                            "type": n.get("type"),
                            "description": n.get("description"),
                            "frequency": n.get("frequency"),
                            "document_id": n.get("document_id"),
                        }
                    for r in item.relationships:
                        raw_edges.append({
                            "source_eid": r.start_node.element_id,
                            "target_eid": r.end_node.element_id,
                            "type": r.get("type", r.type),
                            "weight": r.get("weight", 1),
                            "description": r.get("description", ""),
                        })
                # Check if it's a Node
                elif hasattr(item, "labels"):
                    name = item.get("name")
                    id_to_name[item.element_id] = name
                    nodes[item.element_id] = {
                        "id": name,
                        "name": name,
                        "type": item.get("type"),
                        "description": item.get("description"),
                        "frequency": item.get("frequency"),
                        "document_id": item.get("document_id"),
                    }
                # Check if it's a Relationship
                elif hasattr(item, "type"):
                    raw_edges.append({
                        "source_eid": item.start_node.element_id,
                        "target_eid": item.end_node.element_id,
                        "type": item.get("type", item.type),
                        "weight": item.get("weight", 1),
                        "description": item.get("description", ""),
                    })

        # Resolve edge element_ids to node names
        edges = []
        for e in raw_edges:
            src_name = id_to_name.get(e["source_eid"])
            tgt_name = id_to_name.get(e["target_eid"])
            if src_name and tgt_name:
                edges.append({
                    "source": src_name,
                    "target": tgt_name,
                    "type": e["type"],
                    "weight": e["weight"],
                    "description": e["description"],
                })

        # Deduplicate edges
        unique_edges = {f"{e['source']}-{e['target']}-{e['type']}": e for e in edges}

        return {
            "nodes": list(nodes.values()),
            "edges": list(unique_edges.values())
        }

