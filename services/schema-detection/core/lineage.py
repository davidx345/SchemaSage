"""
Data Lineage and Impact Analysis Core Logic
"""
from typing import List, Dict, Any, Optional
from models.schemas import TableInfo, Relationship

class LineageNode:
    def __init__(self, table: str, column: Optional[str] = None):
        self.table = table
        self.column = column
        self.id = f"{table}.{column}" if column else table

class LineageEdge:
    def __init__(self, source: str, target: str, relationship: Optional[Relationship] = None):
        self.source = source
        self.target = target
        self.relationship = relationship

class DataLineageGraph:
    def __init__(self, tables: List[TableInfo], relationships: List[Relationship], glossary: Optional[List[dict]] = None, context: Optional[dict] = None):
        self.nodes: Dict[str, LineageNode] = {}
        self.edges: List[LineageEdge] = []
        self.glossary = glossary or []
        self.context = context or {}
        self._build_graph(tables, relationships)

    def _build_graph(self, tables: List[TableInfo], relationships: List[Relationship]):
        for table in tables:
            self.nodes[table.name] = LineageNode(table=table.name)
            for col in getattr(table, 'columns', []):
                self.nodes[f"{table.name}.{col.name}"] = LineageNode(table=table.name, column=col.name)
        for rel in relationships:
            src = f"{rel.source_table}.{rel.source_column}"
            tgt = f"{rel.target_table}.{rel.target_column}"
            self.edges.append(LineageEdge(source=src, target=tgt, relationship=rel))

    def _find_business_term(self, name: str) -> Optional[dict]:
        for term in self.glossary:
            if term.get("term", "").lower() == name.lower() or name.lower() in [s.lower() for s in term.get("synonyms", [])]:
                return term
        return None

    def get_table_lineage(self, table: str) -> Dict[str, Any]:
        upstream = [e.source for e in self.edges if e.target.startswith(table)]
        downstream = [e.target for e in self.edges if e.source.startswith(table)]
        business_term = self._find_business_term(table)
        return {
            "table": table,
            "upstream": upstream,
            "downstream": downstream,
            "business_term": business_term,
            "context": self.context.get(table)
        }

    def get_column_lineage(self, table: str, column: str) -> Dict[str, Any]:
        node_id = f"{table}.{column}"
        upstream = [e.source for e in self.edges if e.target == node_id]
        downstream = [e.target for e in self.edges if e.source == node_id]
        business_term = self._find_business_term(column)
        return {
            "column": node_id,
            "upstream": upstream,
            "downstream": downstream,
            "business_term": business_term,
            "context": self.context.get(column)
        }

    def impact_analysis(self, node_id: str) -> Dict[str, Any]:
        impacted = set()
        to_visit = [node_id]
        while to_visit:
            current = to_visit.pop()
            for e in self.edges:
                if e.source == current and e.target not in impacted:
                    impacted.add(e.target)
                    to_visit.append(e.target)
        business_term = self._find_business_term(node_id.split(".")[-1])
        return {
            "changed": node_id,
            "impacted": list(impacted),
            "business_term": business_term,
            "context": self.context.get(node_id)
        }
