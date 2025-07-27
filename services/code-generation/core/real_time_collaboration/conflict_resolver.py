"""
Conflict resolution utilities for real-time collaboration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
from dataclasses import dataclass

from .models import (
    ConflictInfo,
    ConflictResolutionStrategy,
    CollaborationEvent,
    CollaborationEventType,
    ElementLock,
    LockType
)

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts that can occur"""
    CONCURRENT_EDIT = "concurrent_edit"
    LOCK_CONFLICT = "lock_conflict"
    SCHEMA_STRUCTURE = "schema_structure"
    DATA_TYPE = "data_type"
    CONSTRAINT = "constraint"
    RELATIONSHIP = "relationship"
    NAMING = "naming"


@dataclass
class ConflictRule:
    """Rule for conflict resolution"""
    conflict_type: ConflictType
    priority: int
    auto_resolve: bool
    resolution_strategy: ConflictResolutionStrategy
    merge_possible: bool = False


class ConflictResolver:
    """
    Handles conflict detection and resolution in real-time collaboration
    """
    
    def __init__(self):
        self.conflict_rules = self._init_conflict_rules()
        self.pending_resolutions = {}
        self.resolution_timeouts = {}
    
    def _init_conflict_rules(self) -> Dict[ConflictType, ConflictRule]:
        """Initialize conflict resolution rules"""
        return {
            ConflictType.CONCURRENT_EDIT: ConflictRule(
                conflict_type=ConflictType.CONCURRENT_EDIT,
                priority=1,
                auto_resolve=False,
                resolution_strategy=ConflictResolutionStrategy.MANUAL,
                merge_possible=True
            ),
            ConflictType.LOCK_CONFLICT: ConflictRule(
                conflict_type=ConflictType.LOCK_CONFLICT,
                priority=2,
                auto_resolve=True,
                resolution_strategy=ConflictResolutionStrategy.FIRST_COME_FIRST_SERVED
            ),
            ConflictType.SCHEMA_STRUCTURE: ConflictRule(
                conflict_type=ConflictType.SCHEMA_STRUCTURE,
                priority=3,
                auto_resolve=False,
                resolution_strategy=ConflictResolutionStrategy.MANUAL,
                merge_possible=False
            ),
            ConflictType.DATA_TYPE: ConflictRule(
                conflict_type=ConflictType.DATA_TYPE,
                priority=4,
                auto_resolve=True,
                resolution_strategy=ConflictResolutionStrategy.LATEST_WINS
            ),
            ConflictType.CONSTRAINT: ConflictRule(
                conflict_type=ConflictType.CONSTRAINT,
                priority=5,
                auto_resolve=False,
                resolution_strategy=ConflictResolutionStrategy.MANUAL,
                merge_possible=True
            ),
            ConflictType.RELATIONSHIP: ConflictRule(
                conflict_type=ConflictType.RELATIONSHIP,
                priority=6,
                auto_resolve=False,
                resolution_strategy=ConflictResolutionStrategy.MANUAL
            ),
            ConflictType.NAMING: ConflictRule(
                conflict_type=ConflictType.NAMING,
                priority=7,
                auto_resolve=True,
                resolution_strategy=ConflictResolutionStrategy.APPEND_SUFFIX
            )
        }
    
    async def detect_conflicts(
        self,
        new_event: CollaborationEvent,
        recent_events: List[CollaborationEvent],
        active_locks: Dict[str, ElementLock],
        element_id: str
    ) -> List[ConflictInfo]:
        """
        Detect conflicts for a new collaboration event
        
        Args:
            new_event: The new event to check for conflicts
            recent_events: Recent events that might conflict
            active_locks: Currently active locks
            element_id: ID of the element being modified
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Check for lock conflicts
        lock_conflicts = await self._detect_lock_conflicts(
            new_event, active_locks, element_id
        )
        conflicts.extend(lock_conflicts)
        
        # Check for concurrent edit conflicts
        concurrent_conflicts = await self._detect_concurrent_edits(
            new_event, recent_events, element_id
        )
        conflicts.extend(concurrent_conflicts)
        
        # Check for schema structure conflicts
        structure_conflicts = await self._detect_structure_conflicts(
            new_event, recent_events, element_id
        )
        conflicts.extend(structure_conflicts)
        
        # Check for data type conflicts
        type_conflicts = await self._detect_type_conflicts(
            new_event, recent_events, element_id
        )
        conflicts.extend(type_conflicts)
        
        # Check for constraint conflicts
        constraint_conflicts = await self._detect_constraint_conflicts(
            new_event, recent_events, element_id
        )
        conflicts.extend(constraint_conflicts)
        
        # Check for relationship conflicts
        relationship_conflicts = await self._detect_relationship_conflicts(
            new_event, recent_events, element_id
        )
        conflicts.extend(relationship_conflicts)
        
        # Check for naming conflicts
        naming_conflicts = await self._detect_naming_conflicts(
            new_event, recent_events, element_id
        )
        conflicts.extend(naming_conflicts)
        
        return conflicts
    
    async def _detect_lock_conflicts(
        self,
        new_event: CollaborationEvent,
        active_locks: Dict[str, ElementLock],
        element_id: str
    ) -> List[ConflictInfo]:
        """Detect conflicts with existing locks"""
        conflicts = []
        
        for lock_id, lock in active_locks.items():
            if lock.element_id == element_id and lock.user_id != new_event.user_id:
                if lock.is_exclusive:
                    conflict = ConflictInfo(
                        conflict_id=f"lock_{lock_id}_{new_event.event_id}",
                        conflict_type=ConflictType.LOCK_CONFLICT.value,
                        element_id=element_id,
                        user_ids=[new_event.user_id, lock.user_id],
                        events=[new_event],
                        description=f"Exclusive lock held by {lock.user_id}",
                        severity="high",
                        auto_resolvable=True,
                        resolution_strategy=ConflictResolutionStrategy.FIRST_COME_FIRST_SERVED
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_concurrent_edits(
        self,
        new_event: CollaborationEvent,
        recent_events: List[CollaborationEvent],
        element_id: str
    ) -> List[ConflictInfo]:
        """Detect concurrent edit conflicts"""
        conflicts = []
        
        if new_event.event_type != CollaborationEventType.SCHEMA_UPDATE:
            return conflicts
        
        # Look for other schema updates in the last 5 seconds
        cutoff_time = new_event.timestamp - timedelta(seconds=5)
        
        concurrent_events = [
            event for event in recent_events
            if (event.event_type == CollaborationEventType.SCHEMA_UPDATE and
                event.element_id == element_id and
                event.user_id != new_event.user_id and
                event.timestamp > cutoff_time)
        ]
        
        if concurrent_events:
            conflict = ConflictInfo(
                conflict_id=f"concurrent_{element_id}_{new_event.event_id}",
                conflict_type=ConflictType.CONCURRENT_EDIT.value,
                element_id=element_id,
                user_ids=[new_event.user_id] + [e.user_id for e in concurrent_events],
                events=[new_event] + concurrent_events,
                description="Multiple users editing the same element simultaneously",
                severity="medium",
                auto_resolvable=False,
                resolution_strategy=ConflictResolutionStrategy.MANUAL,
                suggested_actions=["Review changes and merge manually", "Rollback to previous version"]
            )
            conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_structure_conflicts(
        self,
        new_event: CollaborationEvent,
        recent_events: List[CollaborationEvent],
        element_id: str
    ) -> List[ConflictInfo]:
        """Detect schema structure conflicts"""
        conflicts = []
        
        if new_event.event_type != CollaborationEventType.SCHEMA_UPDATE:
            return conflicts
        
        # Check for conflicting structural changes
        structure_events = [
            event for event in recent_events
            if (event.event_type == CollaborationEventType.SCHEMA_UPDATE and
                event.user_id != new_event.user_id and
                self._is_structural_change(event))
        ]
        
        for event in structure_events:
            if self._conflicts_with_structure(new_event, event):
                conflict = ConflictInfo(
                    conflict_id=f"structure_{element_id}_{new_event.event_id}_{event.event_id}",
                    conflict_type=ConflictType.SCHEMA_STRUCTURE.value,
                    element_id=element_id,
                    user_ids=[new_event.user_id, event.user_id],
                    events=[new_event, event],
                    description="Conflicting structural changes to schema",
                    severity="high",
                    auto_resolvable=False,
                    resolution_strategy=ConflictResolutionStrategy.MANUAL
                )
                conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_type_conflicts(
        self,
        new_event: CollaborationEvent,
        recent_events: List[CollaborationEvent],
        element_id: str
    ) -> List[ConflictInfo]:
        """Detect data type conflicts"""
        conflicts = []
        
        if new_event.event_type != CollaborationEventType.SCHEMA_UPDATE:
            return conflicts
        
        new_data_type = self._extract_data_type(new_event)
        if not new_data_type:
            return conflicts
        
        type_events = [
            event for event in recent_events
            if (event.event_type == CollaborationEventType.SCHEMA_UPDATE and
                event.element_id == element_id and
                event.user_id != new_event.user_id)
        ]
        
        for event in type_events:
            existing_type = self._extract_data_type(event)
            if existing_type and existing_type != new_data_type:
                conflict = ConflictInfo(
                    conflict_id=f"type_{element_id}_{new_event.event_id}_{event.event_id}",
                    conflict_type=ConflictType.DATA_TYPE.value,
                    element_id=element_id,
                    user_ids=[new_event.user_id, event.user_id],
                    events=[new_event, event],
                    description=f"Data type conflict: {existing_type} vs {new_data_type}",
                    severity="medium",
                    auto_resolvable=True,
                    resolution_strategy=ConflictResolutionStrategy.LATEST_WINS
                )
                conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_constraint_conflicts(
        self,
        new_event: CollaborationEvent,
        recent_events: List[CollaborationEvent],
        element_id: str
    ) -> List[ConflictInfo]:
        """Detect constraint conflicts"""
        conflicts = []
        
        if new_event.event_type != CollaborationEventType.SCHEMA_UPDATE:
            return conflicts
        
        new_constraints = self._extract_constraints(new_event)
        if not new_constraints:
            return conflicts
        
        constraint_events = [
            event for event in recent_events
            if (event.event_type == CollaborationEventType.SCHEMA_UPDATE and
                event.element_id == element_id and
                event.user_id != new_event.user_id)
        ]
        
        for event in constraint_events:
            existing_constraints = self._extract_constraints(event)
            if existing_constraints and self._constraints_conflict(new_constraints, existing_constraints):
                conflict = ConflictInfo(
                    conflict_id=f"constraint_{element_id}_{new_event.event_id}_{event.event_id}",
                    conflict_type=ConflictType.CONSTRAINT.value,
                    element_id=element_id,
                    user_ids=[new_event.user_id, event.user_id],
                    events=[new_event, event],
                    description="Conflicting constraints defined",
                    severity="medium",
                    auto_resolvable=False,
                    resolution_strategy=ConflictResolutionStrategy.MANUAL,
                    suggested_actions=["Merge compatible constraints", "Choose most restrictive constraint"]
                )
                conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_relationship_conflicts(
        self,
        new_event: CollaborationEvent,
        recent_events: List[CollaborationEvent],
        element_id: str
    ) -> List[ConflictInfo]:
        """Detect relationship conflicts"""
        conflicts = []
        
        if new_event.event_type != CollaborationEventType.SCHEMA_UPDATE:
            return conflicts
        
        new_relationships = self._extract_relationships(new_event)
        if not new_relationships:
            return conflicts
        
        relationship_events = [
            event for event in recent_events
            if (event.event_type == CollaborationEventType.SCHEMA_UPDATE and
                event.user_id != new_event.user_id)
        ]
        
        for event in relationship_events:
            existing_relationships = self._extract_relationships(event)
            if existing_relationships and self._relationships_conflict(new_relationships, existing_relationships):
                conflict = ConflictInfo(
                    conflict_id=f"relationship_{element_id}_{new_event.event_id}_{event.event_id}",
                    conflict_type=ConflictType.RELATIONSHIP.value,
                    element_id=element_id,
                    user_ids=[new_event.user_id, event.user_id],
                    events=[new_event, event],
                    description="Conflicting relationships defined",
                    severity="high",
                    auto_resolvable=False,
                    resolution_strategy=ConflictResolutionStrategy.MANUAL
                )
                conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_naming_conflicts(
        self,
        new_event: CollaborationEvent,
        recent_events: List[CollaborationEvent],
        element_id: str
    ) -> List[ConflictInfo]:
        """Detect naming conflicts"""
        conflicts = []
        
        if new_event.event_type != CollaborationEventType.SCHEMA_UPDATE:
            return conflicts
        
        new_name = self._extract_name(new_event)
        if not new_name:
            return conflicts
        
        naming_events = [
            event for event in recent_events
            if (event.event_type == CollaborationEventType.SCHEMA_UPDATE and
                event.user_id != new_event.user_id)
        ]
        
        for event in naming_events:
            existing_name = self._extract_name(event)
            if existing_name and existing_name != new_name and event.element_id != element_id:
                # Check if names conflict (same name for different elements)
                conflict = ConflictInfo(
                    conflict_id=f"naming_{element_id}_{new_event.event_id}_{event.event_id}",
                    conflict_type=ConflictType.NAMING.value,
                    element_id=element_id,
                    user_ids=[new_event.user_id, event.user_id],
                    events=[new_event, event],
                    description=f"Naming conflict: '{new_name}' already used",
                    severity="low",
                    auto_resolvable=True,
                    resolution_strategy=ConflictResolutionStrategy.APPEND_SUFFIX
                )
                conflicts.append(conflict)
        
        return conflicts
    
    async def resolve_conflict(
        self,
        conflict: ConflictInfo,
        resolution_strategy: Optional[ConflictResolutionStrategy] = None,
        user_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve a specific conflict
        
        Args:
            conflict: The conflict to resolve
            resolution_strategy: Strategy to use for resolution
            user_choice: User's choice for manual resolution
            
        Returns:
            Resolution result
        """
        if resolution_strategy is None:
            resolution_strategy = conflict.resolution_strategy
        
        try:
            if resolution_strategy == ConflictResolutionStrategy.LATEST_WINS:
                return await self._resolve_latest_wins(conflict)
            elif resolution_strategy == ConflictResolutionStrategy.FIRST_COME_FIRST_SERVED:
                return await self._resolve_first_come_first_served(conflict)
            elif resolution_strategy == ConflictResolutionStrategy.APPEND_SUFFIX:
                return await self._resolve_append_suffix(conflict)
            elif resolution_strategy == ConflictResolutionStrategy.MANUAL:
                return await self._resolve_manual(conflict, user_choice)
            else:
                return {
                    "success": False,
                    "error": f"Unknown resolution strategy: {resolution_strategy}"
                }
        
        except Exception as e:
            logger.error(f"Error resolving conflict {conflict.conflict_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Resolution failed: {str(e)}"
            }
    
    async def _resolve_latest_wins(self, conflict: ConflictInfo) -> Dict[str, Any]:
        """Resolve conflict using latest wins strategy"""
        latest_event = max(conflict.events, key=lambda e: e.timestamp)
        
        return {
            "success": True,
            "strategy": "latest_wins",
            "winning_event": latest_event.event_id,
            "winning_user": latest_event.user_id,
            "resolution_data": latest_event.data
        }
    
    async def _resolve_first_come_first_served(self, conflict: ConflictInfo) -> Dict[str, Any]:
        """Resolve conflict using first come first served strategy"""
        first_event = min(conflict.events, key=lambda e: e.timestamp)
        
        return {
            "success": True,
            "strategy": "first_come_first_served",
            "winning_event": first_event.event_id,
            "winning_user": first_event.user_id,
            "resolution_data": first_event.data
        }
    
    async def _resolve_append_suffix(self, conflict: ConflictInfo) -> Dict[str, Any]:
        """Resolve naming conflict by appending suffix"""
        latest_event = max(conflict.events, key=lambda e: e.timestamp)
        
        # Extract name and append suffix
        original_name = self._extract_name(latest_event)
        if original_name:
            new_name = f"{original_name}_v2"
            
            # Update event data with new name
            resolution_data = latest_event.data.copy()
            if "name" in resolution_data:
                resolution_data["name"] = new_name
            
            return {
                "success": True,
                "strategy": "append_suffix",
                "winning_event": latest_event.event_id,
                "winning_user": latest_event.user_id,
                "resolution_data": resolution_data,
                "original_name": original_name,
                "new_name": new_name
            }
        
        return {
            "success": False,
            "error": "Could not extract name for suffix resolution"
        }
    
    async def _resolve_manual(self, conflict: ConflictInfo, user_choice: Optional[str]) -> Dict[str, Any]:
        """Handle manual conflict resolution"""
        if not user_choice:
            return {
                "success": False,
                "error": "Manual resolution requires user choice",
                "requires_user_input": True,
                "conflict_details": {
                    "description": conflict.description,
                    "events": [e.event_id for e in conflict.events],
                    "users": conflict.user_ids,
                    "suggested_actions": conflict.suggested_actions
                }
            }
        
        # Process user choice
        try:
            choice_data = eval(user_choice) if isinstance(user_choice, str) else user_choice
            
            return {
                "success": True,
                "strategy": "manual",
                "user_choice": choice_data,
                "resolution_data": choice_data
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Invalid user choice: {str(e)}"
            }
    
    def _is_structural_change(self, event: CollaborationEvent) -> bool:
        """Check if event represents a structural change"""
        if "type" not in event.data:
            return False
        
        structural_types = {
            "table_create", "table_delete", "table_rename",
            "column_add", "column_remove", "column_rename",
            "index_create", "index_drop"
        }
        
        return event.data.get("type") in structural_types
    
    def _conflicts_with_structure(self, event1: CollaborationEvent, event2: CollaborationEvent) -> bool:
        """Check if two events have conflicting structural changes"""
        type1 = event1.data.get("type")
        type2 = event2.data.get("type")
        
        conflicting_pairs = {
            ("table_delete", "column_add"),
            ("table_delete", "index_create"),
            ("column_remove", "index_create"),
            ("table_rename", "table_delete")
        }
        
        return (type1, type2) in conflicting_pairs or (type2, type1) in conflicting_pairs
    
    def _extract_data_type(self, event: CollaborationEvent) -> Optional[str]:
        """Extract data type from event"""
        return event.data.get("data_type") or event.data.get("type")
    
    def _extract_constraints(self, event: CollaborationEvent) -> Optional[List[str]]:
        """Extract constraints from event"""
        return event.data.get("constraints", [])
    
    def _extract_relationships(self, event: CollaborationEvent) -> Optional[List[Dict[str, Any]]]:
        """Extract relationships from event"""
        return event.data.get("relationships", [])
    
    def _extract_name(self, event: CollaborationEvent) -> Optional[str]:
        """Extract name from event"""
        return event.data.get("name")
    
    def _constraints_conflict(self, constraints1: List[str], constraints2: List[str]) -> bool:
        """Check if two sets of constraints conflict"""
        # Simple check for mutually exclusive constraints
        exclusive_pairs = {
            ("nullable", "not_null"),
            ("unique", "non_unique"),
            ("primary_key", "foreign_key")
        }
        
        for c1 in constraints1:
            for c2 in constraints2:
                if (c1, c2) in exclusive_pairs or (c2, c1) in exclusive_pairs:
                    return True
        
        return False
    
    def _relationships_conflict(self, relationships1: List[Dict[str, Any]], relationships2: List[Dict[str, Any]]) -> bool:
        """Check if two sets of relationships conflict"""
        # Check for conflicting foreign key relationships
        for r1 in relationships1:
            for r2 in relationships2:
                if (r1.get("type") == "foreign_key" and r2.get("type") == "foreign_key" and
                    r1.get("column") == r2.get("column") and
                    r1.get("references") != r2.get("references")):
                    return True
        
        return False
