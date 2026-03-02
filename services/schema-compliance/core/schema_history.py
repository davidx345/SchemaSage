"""
Schema Versioning and Change History Core Logic
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from models.schemas import SchemaResponse
import uuid

class SchemaSnapshot:
    def __init__(self, schema: SchemaResponse, version: Optional[str] = None, timestamp: Optional[datetime] = None):
        self.id = version or str(uuid.uuid4())
        self.schema = schema
        self.timestamp = timestamp or datetime.utcnow()

class SchemaHistory:
    def __init__(self):
        self.snapshots: List[SchemaSnapshot] = []

    def add_snapshot(self, schema: SchemaResponse):
        snapshot = SchemaSnapshot(schema)
        self.snapshots.append(snapshot)
        return snapshot

    def get_history(self) -> List[Dict[str, Any]]:
        return [
            {"id": s.id, "timestamp": s.timestamp.isoformat(), "schema": s.schema.dict()} for s in self.snapshots
        ]

    def get_snapshot(self, version: str) -> Optional[SchemaSnapshot]:
        for s in self.snapshots:
            if s.id == version:
                return s
        return None

    def diff(self, version_a: str, version_b: str) -> Dict[str, Any]:
        # Simple diff: compare tables/columns/relationships
        snap_a = self.get_snapshot(version_a)
        snap_b = self.get_snapshot(version_b)
        if not snap_a or not snap_b:
            return {"error": "One or both versions not found"}
        # For simplicity, just show table/column/relationship names added/removed
        def extract(schema):
            return {
                "tables": set(t["name"] for t in schema["tables"]),
                "columns": set((t["name"], c["name"]) for t in schema["tables"] for c in t["columns"]),
                "relationships": set((r["source_table"], r["source_column"], r["target_table"], r["target_column"]) for r in schema["relationships"])
            }
        a = extract(snap_a.schema.dict())
        b = extract(snap_b.schema.dict())
        return {
            "tables_added": list(b["tables"] - a["tables"]),
            "tables_removed": list(a["tables"] - b["tables"]),
            "columns_added": list(b["columns"] - a["columns"]),
            "columns_removed": list(a["columns"] - b["columns"]),
            "relationships_added": list(b["relationships"] - a["relationships"]),
            "relationships_removed": list(a["relationships"] - b["relationships"])
        }
