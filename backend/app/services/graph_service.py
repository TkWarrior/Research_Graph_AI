"""
Service for managing the Knowledge Graph using Neo4j.
"""

from typing import List, Dict, Any
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
        """Create uniqueness constraints for entities to prevent duplicates."""
        query = "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE"
        try:
            with self.driver.session() as session:
                session.run(query)
        except Exception as e:
            # Constraints might already exist or require enterprise edition for some features
            print(f"Note on constraint creation: {e}")

    def create_entities(self, entities: List[Entity]) -> None:
        """Create or merge multiple entities into the graph."""
        if not entities:
            return

        query = """
        UNWIND $entities AS e
        MERGE (n:Entity {name: e.name})
        SET n.type = e.type, n.description = e.description
        """
        
        entities_data = [
            {"name": ent.name, "type": ent.type, "description": ent.description}
            for ent in entities
        ]

        with self.driver.session() as session:
            session.run(query, entities=entities_data)

    def create_relationships(self, relationships: List[Relationship]) -> None:
        """Create relationships between existing entities."""
        if not relationships:
            return

        # Cypher to safely merge relationships only if both source and target exist
        query = """
        UNWIND $rels AS r
        MATCH (source:Entity {name: r.source})
        MATCH (target:Entity {name: r.target})
        MERGE (source)-[rel:RELATED_TO {type: r.type}]->(target)
        SET rel.description = r.description
        """
        
        rels_data = [
            {
                "source": r.source,
                "target": r.target,
                "type": r.type.upper().replace(" ", "_"), # Ensure valid neo4j type format
                "description": r.description
            }
            for r in relationships
        ]

        with self.driver.session() as session:
            session.run(query, rels=rels_data)

    def query_subgraph(self, entity_name: str, depth: int = 1) -> Dict[str, Any]:
        """Retrieve the neighborhood graph around a specific entity."""
        # Note: Cypher does not support parameterization for path length bounds, 
        # so we safely format the depth integer directly into the query string.
        query = f"""
        MATCH path = (e:Entity {{name: $name}})-[*1..{int(depth)}]-(connected)
        RETURN path
        """
        with self.driver.session() as session:
            result = session.run(query, name=entity_name, depth=depth)
            return self._format_graph_result(result)

    def search_entities(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for entities matching a term in their name or description."""
        query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($term) 
           OR toLower(e.description) CONTAINS toLower($term)
        RETURN e.name AS name, e.type AS type, e.description AS description
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, term=search_term, limit=limit)
            return [record.data() for record in result]

    def get_full_graph(self, limit: int = 500) -> Dict[str, Any]:
        """Retrieve the entire graph (up to a node limit) for frontend visualization."""
        query = """
        MATCH (n:Entity)
        OPTIONAL MATCH (n)-[r]->(m:Entity)
        RETURN n, r, m
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return self._format_graph_result(result)

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        query_nodes = "MATCH (n:Entity) RETURN count(n) as node_count"
        query_edges = "MATCH ()-[r]->() RETURN count(r) as edge_count"
        query_top = """
        MATCH (n:Entity)-[r]-() 
        RETURN n.name as name, count(r) as degree 
        ORDER BY degree DESC LIMIT 5
        """
        
        stats = {}
        with self.driver.session() as session:
            stats["node_count"] = session.run(query_nodes).single()["node_count"]
            stats["edge_count"] = session.run(query_edges).single()["edge_count"]
            stats["most_connected"] = [record.data() for record in session.run(query_top)]
            
        return stats

    def cypher_query(self, query: str, parameters: dict = None) -> List[Dict[str, Any]]:
        """Run arbitrary Cypher for advanced queries by agents."""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def _format_graph_result(self, neo4j_result) -> Dict[str, Any]:
        """Helper to format Neo4j paths/nodes into standard node/edge lists for frontend."""
        nodes = {}
        edges = []

        for record in neo4j_result:
            for key in record.keys():
                item = record[key]
                if item is None:
                    continue
                
                # Check if it's a Path
                if hasattr(item, "nodes") and hasattr(item, "relationships"):
                    for n in item.nodes:
                        nodes[n.element_id] = {"id": n.element_id, "name": n.get("name"), "type": n.get("type"), "description": n.get("description")}
                    for r in item.relationships:
                        edges.append({
                            "id": r.element_id,
                            "source": r.start_node.element_id,
                            "target": r.end_node.element_id,
                            "type": r.get("type", r.type),
                            "description": r.get("description", "")
                        })
                # Check if it's a Node
                elif hasattr(item, "labels"):
                    nodes[item.element_id] = {"id": item.element_id, "name": item.get("name"), "type": item.get("type"), "description": item.get("description")}
                # Check if it's a Relationship
                elif hasattr(item, "type"):
                    edges.append({
                        "id": item.element_id,
                        "source": item.start_node.element_id,
                        "target": item.end_node.element_id,
                        "type": item.get("type", item.type),
                        "description": item.get("description", "")
                    })

        # Deduplicate edges
        unique_edges = {f"{e['source']}-{e['target']}-{e['type']}": e for e in edges}

        return {
            "nodes": list(nodes.values()),
            "edges": list(unique_edges.values())
        }
