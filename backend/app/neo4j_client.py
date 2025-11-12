"""Neo4j graph database client for relationship queries."""
from __future__ import annotations

from typing import Dict, List, Optional

from neo4j import GraphDatabase, Driver

from .config import settings


class Neo4jClient:
    """Client for interacting with Neo4j graph database."""

    def __init__(self) -> None:
        """Initialize Neo4j driver."""
        self.driver: Optional[Driver] = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            # Test connection
            self.driver.verify_connectivity()
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    def close(self) -> None:
        """Close Neo4j driver."""
        if self.driver:
            self.driver.close()

    def create_entity_node(
        self,
        entity_id: int,
        name: str,
        role: Optional[str] = None,
        company: Optional[str] = None,
        properties: Optional[Dict] = None,
    ) -> None:
        """Create or update an entity node in the graph."""
        if not self.driver:
            return

        props = properties or {}
        props.update({
            "entity_id": entity_id,
            "name": name,
            "role": role or "unknown",
            "company": company or "",
        })

        with self.driver.session(database=settings.neo4j_database) as session:
            session.run(
                """
                MERGE (e:Entity {entity_id: $entity_id})
                SET e.name = $name,
                    e.role = $role,
                    e.company = $company,
                    e.updated_at = datetime()
                """,
                props,
            )

    def create_connection(
        self,
        source_id: int,
        target_id: int,
        relationship_type: str = "CONNECTED_TO",
        strength: float = 1.0,
    ) -> None:
        """Create a relationship between two entities."""
        if not self.driver:
            return

        with self.driver.session(database=settings.neo4j_database) as session:
            session.run(
                f"""
                MATCH (a:Entity {{entity_id: $source_id}})
                MATCH (b:Entity {{entity_id: $target_id}})
                MERGE (a)-[r:{relationship_type}]->(b)
                SET r.strength = $strength,
                    r.updated_at = datetime()
                """,
                {
                    "source_id": source_id,
                    "target_id": target_id,
                    "strength": strength,
                },
            )

    def find_intro_path(
        self,
        source_id: int,
        target_id: int,
        max_depth: int = 3,
    ) -> List[Dict]:
        """Find shortest introduction path between two entities."""
        if not self.driver:
            return []

        with self.driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH path = shortestPath(
                    (a:Entity {entity_id: $source_id})-[*1..%d]-(b:Entity {entity_id: $target_id})
                )
                RETURN [node in nodes(path) | {
                    entity_id: node.entity_id,
                    name: node.name,
                    role: node.role,
                    company: node.company
                }] as path_nodes
                LIMIT 1
                """ % max_depth,
                {
                    "source_id": source_id,
                    "target_id": target_id,
                },
            )
            
            record = result.single()
            if record:
                return record["path_nodes"]
            return []

    def get_mutual_connections(
        self,
        entity_id: int,
        target_id: int,
    ) -> List[Dict]:
        """Find mutual connections between two entities."""
        if not self.driver:
            return []

        with self.driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (a:Entity {entity_id: $entity_id})-[:CONNECTED_TO]-(mutual)-[:CONNECTED_TO]-(b:Entity {entity_id: $target_id})
                WHERE mutual.entity_id <> $entity_id AND mutual.entity_id <> $target_id
                RETURN DISTINCT mutual.entity_id as entity_id,
                       mutual.name as name,
                       mutual.role as role,
                       mutual.company as company
                LIMIT 10
                """,
                {
                    "entity_id": entity_id,
                    "target_id": target_id,
                },
            )
            
            return [dict(record) for record in result]

    def get_connected_investors(
        self,
        entity_id: int,
        limit: int = 20,
    ) -> List[int]:
        """Get all investors connected to an entity."""
        if not self.driver:
            return []

        with self.driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (e:Entity {entity_id: $entity_id})-[:CONNECTED_TO]-(investor:Entity)
                WHERE investor.role = 'investor'
                RETURN investor.entity_id as entity_id
                LIMIT $limit
                """,
                {
                    "entity_id": entity_id,
                    "limit": limit,
                },
            )
            
            return [record["entity_id"] for record in result]

    def clear_graph(self) -> None:
        """Clear all nodes and relationships (use with caution)."""
        if not self.driver:
            return

        with self.driver.session(database=settings.neo4j_database) as session:
            session.run("MATCH (n) DETACH DELETE n")


# Global client instance
neo4j_client = Neo4jClient()

