"""
Pattern-based extraction for natural language schema conversion
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict

from .models import (
    NLPatterns, ExtractedEntity, ExtractedRelationship, FieldInfo, PatternMatch,
    EntityType, RelationshipType, EntityClassifier, TypeInference,
    normalize_entity_name, normalize_field_name, is_valid_entity_name
)

logger = logging.getLogger(__name__)


class PatternExtractor:
    """
    Extracts entities, relationships, and fields using regex patterns
    """
    
    def __init__(self):
        self.patterns = NLPatterns()
        self.entity_classifier = EntityClassifier()
        self.type_inference = TypeInference()
        
        # Cache for performance
        self._pattern_cache = {}
    
    def extract_all_patterns(self, description: str) -> Tuple[List[ExtractedEntity], List[ExtractedRelationship], Dict[str, List[FieldInfo]]]:
        """
        Extract entities, relationships, and fields from description
        
        Args:
            description: Natural language description
            
        Returns:
            Tuple of (entities, relationships, fields)
        """
        logger.debug(f"Extracting patterns from: {description[:100]}...")
        
        # Extract entities
        entities = self.extract_entities(description)
        logger.debug(f"Extracted {len(entities)} entities")
        
        # Extract relationships
        relationships = self.extract_relationships(description)
        logger.debug(f"Extracted {len(relationships)} relationships")
        
        # Extract fields
        fields = self.extract_fields(description, entities)
        logger.debug(f"Extracted fields for {len(fields)} entities")
        
        return entities, relationships, fields
    
    def extract_entities(self, description: str) -> List[ExtractedEntity]:
        """
        Extract entities from natural language description
        
        Args:
            description: Natural language description
            
        Returns:
            List of extracted entities
        """
        entities = {}  # Use dict to avoid duplicates
        
        # Extract direct entities
        direct_entities = self._extract_direct_entities(description)
        for entity in direct_entities:
            entities[entity.name] = entity
        
        # Extract plural entities
        plural_entities = self._extract_plural_entities(description)
        for entity in plural_entities:
            entities[entity.name] = entity
        
        # Extract contextual entities
        contextual_entities = self._extract_contextual_entities(description)
        for entity in contextual_entities:
            entities[entity.name] = entity
        
        # Extract fallback entities if not enough found
        if len(entities) < 1:
            fallback_entities = self._extract_fallback_entities(description)
            for entity in fallback_entities:
                entities[entity.name] = entity
        
        # Sort by confidence
        result = sorted(entities.values(), key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"Extracted {len(result)} entities: {[e.name for e in result]}")
        return result
    
    def extract_relationships(self, description: str) -> List[ExtractedRelationship]:
        """
        Extract relationships from natural language description
        
        Args:
            description: Natural language description
            
        Returns:
            List of extracted relationships
        """
        relationships = []
        
        # Extract each relationship type
        for rel_type, patterns in self.patterns.RELATIONSHIP_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, description, re.IGNORECASE)
                
                for match in matches:
                    if len(match) == 2:
                        source, target = match
                        source = normalize_entity_name(source)
                        target = normalize_entity_name(target)
                        
                        if source and target and source != target:
                            relationship = ExtractedRelationship(
                                source=source,
                                target=target,
                                relationship_type=RelationshipType(rel_type.replace('_', '-')),
                                confidence=0.8,
                                context=pattern
                            )
                            relationships.append(relationship)
        
        logger.info(f"Extracted {len(relationships)} relationships")
        return relationships
    
    def extract_fields(self, description: str, entities: List[ExtractedEntity]) -> Dict[str, List[FieldInfo]]:
        """
        Extract fields for entities from description
        
        Args:
            description: Natural language description
            entities: List of extracted entities
            
        Returns:
            Dictionary mapping entity names to their fields
        """
        entity_fields = {}
        entity_names = {e.name for e in entities}
        
        # Extract explicit fields
        explicit_fields = self._extract_explicit_fields(description)
        for entity_name, fields in explicit_fields.items():
            if entity_name in entity_names:
                entity_fields[entity_name] = fields
        
        # Extract compound fields
        compound_fields = self._extract_compound_fields(description)
        for entity_name, fields in compound_fields.items():
            if entity_name in entity_names:
                if entity_name in entity_fields:
                    entity_fields[entity_name].extend(fields)
                else:
                    entity_fields[entity_name] = fields
        
        # Extract descriptive fields
        descriptive_fields = self._extract_descriptive_fields(description)
        for entity_name, fields in descriptive_fields.items():
            if entity_name in entity_names:
                if entity_name in entity_fields:
                    entity_fields[entity_name].extend(fields)
                else:
                    entity_fields[entity_name] = fields
        
        # Remove duplicates and normalize
        for entity_name in entity_fields:
            unique_fields = {}
            for field in entity_fields[entity_name]:
                normalized_name = normalize_field_name(field.name)
                if normalized_name and normalized_name not in unique_fields:
                    field.name = normalized_name
                    unique_fields[normalized_name] = field
            entity_fields[entity_name] = list(unique_fields.values())
        
        logger.info(f"Extracted fields for entities: {list(entity_fields.keys())}")
        return entity_fields
    
    def _extract_direct_entities(self, description: str) -> List[ExtractedEntity]:
        """Extract entities using direct patterns"""
        entities = {}
        
        for pattern in self.patterns.ENTITY_PATTERNS['direct_entities']:
            matches = re.findall(pattern, description, re.IGNORECASE)
            
            for match in matches:
                entity_name = match if isinstance(match, str) else match[0]
                entity_name = normalize_entity_name(entity_name)
                
                if entity_name and is_valid_entity_name(entity_name):
                    entity_type = self.entity_classifier.classify_entity(entity_name)
                    confidence = self.entity_classifier.get_confidence_score(entity_name, entity_type)
                    
                    if entity_name not in entities:
                        entities[entity_name] = ExtractedEntity(
                            name=entity_name,
                            entity_type=entity_type,
                            confidence=confidence,
                            fields=[],
                            context=pattern
                        )
        
        return list(entities.values())
    
    def _extract_plural_entities(self, description: str) -> List[ExtractedEntity]:
        """Extract entities from plural forms"""
        entities = {}
        
        for pattern in self.patterns.ENTITY_PATTERNS['plural_entities']:
            matches = re.findall(pattern, description, re.IGNORECASE)
            
            for match in matches:
                entity_name = match if isinstance(match, str) else match[0]
                entity_name = normalize_entity_name(entity_name)
                
                if entity_name and is_valid_entity_name(entity_name):
                    entity_type = self.entity_classifier.classify_entity(entity_name)
                    confidence = self.entity_classifier.get_confidence_score(entity_name, entity_type)
                    
                    if entity_name not in entities:
                        entities[entity_name] = ExtractedEntity(
                            name=entity_name,
                            entity_type=entity_type,
                            confidence=confidence * 0.9,  # Slightly lower confidence for plural
                            fields=[],
                            context=pattern
                        )
        
        return list(entities.values())
    
    def _extract_contextual_entities(self, description: str) -> List[ExtractedEntity]:
        """Extract entities from contextual patterns"""
        entities = {}
        
        for pattern in self.patterns.ENTITY_PATTERNS['contextual_entities']:
            matches = re.findall(pattern, description, re.IGNORECASE)
            
            for match in matches:
                entity_name = match if isinstance(match, str) else match[0]
                entity_name = normalize_entity_name(entity_name)
                
                if entity_name and is_valid_entity_name(entity_name):
                    entity_type = self.entity_classifier.classify_entity(entity_name)
                    confidence = self.entity_classifier.get_confidence_score(entity_name, entity_type) * 0.7
                    
                    if entity_name not in entities:
                        entities[entity_name] = ExtractedEntity(
                            name=entity_name,
                            entity_type=entity_type,
                            confidence=confidence,
                            fields=[],
                            context=pattern
                        )
        
        return list(entities.values())
    
    def _extract_fallback_entities(self, description: str) -> List[ExtractedEntity]:
        """Extract entities using fallback patterns when others fail"""
        entities = {}
        
        # Common database entity indicators
        entity_indicators = [
            'students', 'student', 'teachers', 'teacher', 'subjects', 'subject',
            'users', 'user', 'customers', 'customer', 'products', 'product',
            'orders', 'order', 'items', 'item', 'posts', 'post', 'comments', 'comment',
            'categories', 'category', 'departments', 'department', 'courses', 'course',
            'companies', 'company', 'projects', 'project', 'employees', 'employee'
        ]
        
        description_lower = description.lower()
        
        for indicator in entity_indicators:
            if indicator in description_lower:
                entity_name = normalize_entity_name(indicator)
                
                if entity_name and is_valid_entity_name(entity_name):
                    entity_type = self.entity_classifier.classify_entity(entity_name)
                    confidence = 0.5  # Lower confidence for fallback
                    
                    if entity_name not in entities:
                        entities[entity_name] = ExtractedEntity(
                            name=entity_name,
                            entity_type=entity_type,
                            confidence=confidence,
                            fields=[],
                            context="fallback_extraction"
                        )
        
        return list(entities.values())
    
    def _extract_explicit_fields(self, description: str) -> Dict[str, List[FieldInfo]]:
        """Extract explicitly mentioned fields"""
        entity_fields = defaultdict(list)
        
        for pattern in self.patterns.FIELD_PATTERNS['explicit_fields']:
            matches = re.findall(pattern, description, re.IGNORECASE)
            
            for match in matches:
                if len(match) == 2:
                    entity, field_list = match
                    entity = normalize_entity_name(entity)
                    
                    if entity:
                        field_names = [f.strip() for f in field_list.split(',')]
                        
                        for field_name in field_names:
                            normalized_field = normalize_field_name(field_name)
                            if normalized_field:
                                field_type = self.type_inference.infer_type_from_field_name(normalized_field)
                                validation = self.type_inference.infer_validation(normalized_field, field_type)
                                
                                field_info = FieldInfo(
                                    name=normalized_field,
                                    inferred_type=field_type,
                                    nullable=True,
                                    validation=validation,
                                    description=f"{field_name.title()} field"
                                )
                                entity_fields[entity].append(field_info)
        
        return dict(entity_fields)
    
    def _extract_compound_fields(self, description: str) -> Dict[str, List[FieldInfo]]:
        """Extract fields from compound patterns (X has Y and Z)"""
        entity_fields = defaultdict(list)
        
        for pattern in self.patterns.FIELD_PATTERNS['compound_fields']:
            matches = re.findall(pattern, description, re.IGNORECASE)
            
            for match in matches:
                if len(match) >= 3:
                    entity = normalize_entity_name(match[0])
                    
                    if entity:
                        # Extract all field names from the match
                        field_names = [normalize_field_name(f) for f in match[1:] if f]
                        
                        for field_name in field_names:
                            if field_name:
                                field_type = self.type_inference.infer_type_from_field_name(field_name)
                                validation = self.type_inference.infer_validation(field_name, field_type)
                                
                                field_info = FieldInfo(
                                    name=field_name,
                                    inferred_type=field_type,
                                    nullable=True,
                                    validation=validation,
                                    description=f"{field_name.replace('_', ' ').title()} field"
                                )
                                entity_fields[entity].append(field_info)
        
        return dict(entity_fields)
    
    def _extract_descriptive_fields(self, description: str) -> Dict[str, List[FieldInfo]]:
        """Extract fields from descriptive patterns"""
        entity_fields = defaultdict(list)
        
        for pattern in self.patterns.FIELD_PATTERNS['descriptive_fields']:
            matches = re.findall(pattern, description, re.IGNORECASE)
            
            for match in matches:
                if len(match) == 2:
                    entity, field_name = match
                    entity = normalize_entity_name(entity)
                    field_name = normalize_field_name(field_name)
                    
                    if entity and field_name:
                        field_type = self.type_inference.infer_type_from_field_name(field_name)
                        validation = self.type_inference.infer_validation(field_name, field_type)
                        
                        field_info = FieldInfo(
                            name=field_name,
                            inferred_type=field_type,
                            nullable=True,
                            validation=validation,
                            description=f"{field_name.replace('_', ' ').title()} field"
                        )
                        entity_fields[entity].append(field_info)
        
        return dict(entity_fields)
    
    def get_pattern_matches(self, description: str, pattern_type: str) -> List[PatternMatch]:
        """
        Get all pattern matches for a specific type
        
        Args:
            description: Text to search
            pattern_type: Type of patterns to match
            
        Returns:
            List of pattern matches
        """
        matches = []
        
        if pattern_type == 'entities':
            for category, patterns in self.patterns.ENTITY_PATTERNS.items():
                for pattern in patterns:
                    regex_matches = re.findall(pattern, description, re.IGNORECASE)
                    
                    for match in regex_matches:
                        value = match if isinstance(match, str) else match[0]
                        
                        pattern_match = PatternMatch(
                            match_type=f"entity_{category}",
                            value=value,
                            confidence=0.8,
                            context=pattern
                        )
                        matches.append(pattern_match)
        
        elif pattern_type == 'relationships':
            for rel_type, patterns in self.patterns.RELATIONSHIP_PATTERNS.items():
                for pattern in patterns:
                    regex_matches = re.findall(pattern, description, re.IGNORECASE)
                    
                    for match in regex_matches:
                        if len(match) == 2:
                            value = f"{match[0]} -> {match[1]}"
                            
                            pattern_match = PatternMatch(
                                match_type=f"relationship_{rel_type}",
                                value=value,
                                confidence=0.8,
                                context=pattern
                            )
                            matches.append(pattern_match)
        
        elif pattern_type == 'fields':
            for category, patterns in self.patterns.FIELD_PATTERNS.items():
                for pattern in patterns:
                    regex_matches = re.findall(pattern, description, re.IGNORECASE)
                    
                    for match in regex_matches:
                        if len(match) >= 2:
                            value = f"{match[0]}: {', '.join(match[1:])}"
                            
                            pattern_match = PatternMatch(
                                match_type=f"field_{category}",
                                value=value,
                                confidence=0.7,
                                context=pattern
                            )
                            matches.append(pattern_match)
        
        return matches
    
    def validate_extracted_data(
        self,
        entities: List[ExtractedEntity],
        relationships: List[ExtractedRelationship],
        fields: Dict[str, List[FieldInfo]]
    ) -> Tuple[List[ExtractedEntity], List[ExtractedRelationship], Dict[str, List[FieldInfo]]]:
        """
        Validate and clean extracted data
        
        Args:
            entities: Extracted entities
            relationships: Extracted relationships
            fields: Extracted fields
            
        Returns:
            Cleaned and validated data
        """
        # Filter entities by confidence
        valid_entities = [e for e in entities if e.confidence > 0.3]
        entity_names = {e.name for e in valid_entities}
        
        # Filter relationships to only include valid entities
        valid_relationships = [
            r for r in relationships 
            if r.source in entity_names and r.target in entity_names
        ]
        
        # Filter fields to only include valid entities
        valid_fields = {
            entity_name: field_list 
            for entity_name, field_list in fields.items()
            if entity_name in entity_names
        }
        
        logger.info(f"Validated data: {len(valid_entities)} entities, {len(valid_relationships)} relationships")
        return valid_entities, valid_relationships, valid_fields
