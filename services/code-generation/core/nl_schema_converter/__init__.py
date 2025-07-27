"""
Natural Language to Schema Converter Module

This module provides functionality to convert natural language descriptions
into structured database schemas using pattern extraction and AI assistance.
"""

from .models import (
    ExtractedEntity,
    ExtractedRelationship,
    FieldInfo,
    StandardFields,
    EntityType,
    RelationshipType,
    TypeInference,
    normalize_field_name
)

from .pattern_extractor import PatternExtractor
from .ai_converter import AIConverter
from .schema_builder import SchemaBuilder

__all__ = [
    'ExtractedEntity',
    'ExtractedRelationship', 
    'FieldInfo',
    'StandardFields',
    'EntityType',
    'RelationshipType',
    'TypeInference',
    'normalize_field_name',
    'PatternExtractor',
    'AIConverter',
    'SchemaBuilder',
    'NLSchemaConverter'
]

class NLSchemaConverter:
    """
    Main converter class that orchestrates pattern extraction, AI conversion,
    and schema building to convert natural language descriptions to database schemas.
    """
    
    def __init__(self, gemini_api_key: str = None):
        """
        Initialize the NL Schema Converter
        
        Args:
            gemini_api_key: Optional Gemini API key for AI conversion
        """
        self.pattern_extractor = PatternExtractor()
        self.ai_converter = AIConverter(gemini_api_key) if gemini_api_key else None
        self.schema_builder = SchemaBuilder()
    
    def convert_to_schema(self, description: str, use_ai: bool = True, options: dict = None):
        """
        Convert natural language description to database schema
        
        Args:
            description: Natural language description
            use_ai: Whether to use AI for enhancement
            options: Conversion options
            
        Returns:
            SchemaResponse with tables, relationships, and metadata
        """
        options = options or {}
        
        # Step 1: Extract patterns
        entities, relationships, fields = self.pattern_extractor.extract_all(description)
        
        # Step 2: Use AI if available and requested
        if use_ai and self.ai_converter:
            try:
                ai_schema = self.ai_converter.generate_schema(description, options)
                # Merge AI results with pattern extraction results
                entities, relationships, fields = self._merge_ai_and_pattern_results(
                    entities, relationships, fields, ai_schema
                )
            except Exception as e:
                # Fall back to pattern extraction only
                pass
        
        # Step 3: Build final schema
        schema = self.schema_builder.build_schema_from_extracted_data(
            entities, relationships, fields, description, options
        )
        
        return schema
    
    def _merge_ai_and_pattern_results(self, pattern_entities, pattern_relationships, 
                                     pattern_fields, ai_schema):
        """Merge results from pattern extraction and AI conversion"""
        # This is a simplified merge - in practice, this would be more sophisticated
        # For now, we'll prioritize pattern extraction results and supplement with AI
        return pattern_entities, pattern_relationships, pattern_fields
