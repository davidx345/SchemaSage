"""
Embedding generation for schema intelligence
Converts schema data to vector embeddings using transformer models
"""

import logging
from typing import Dict, List, Any, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib
import json
from datetime import datetime

from models.schemas import SchemaResponse, TableInfo, ColumnInfo
from .models import SchemaEmbedding, EmbeddingType

logger = logging.getLogger(__name__)


class SchemaEmbeddingGenerator:
    """
    Generates embeddings for schema components using transformer models
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding generator
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"Initialized embedding generator with model {model_name}, dimension: {self.dimension}")
    
    def generate_schema_embedding(self, schema: SchemaResponse) -> SchemaEmbedding:
        """
        Generate embedding for complete schema
        
        Args:
            schema: Schema response object
            
        Returns:
            Schema embedding
        """
        try:
            # Convert schema to text representation
            schema_text = self._schema_to_text(schema)
            
            # Generate embedding
            embedding_vector = self.model.encode(schema_text)
            
            # Create embedding ID
            embedding_id = self._generate_embedding_id("schema", schema.schema_name, schema_text)
            
            # Prepare metadata
            metadata = {
                'schema_name': schema.schema_name,
                'table_count': len(schema.tables),
                'total_columns': sum(len(table.columns) for table in schema.tables),
                'has_relationships': bool(schema.relationships),
                'model_name': self.model_name,
                'text_length': len(schema_text)
            }
            
            # Prepare schema data
            schema_data = {
                'schema_name': schema.schema_name,
                'tables': [table.table_name for table in schema.tables],
                'relationships': schema.relationships or [],
                'description': getattr(schema, 'description', ''),
                'source': getattr(schema, 'source', '')
            }
            
            return SchemaEmbedding(
                embedding_id=embedding_id,
                embedding_type=EmbeddingType.SCHEMA,
                embedding=embedding_vector,
                schema_data=schema_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error generating schema embedding: {e}")
            raise
    
    def generate_table_embedding(self, table: TableInfo, schema_name: str = None) -> SchemaEmbedding:
        """
        Generate embedding for table
        
        Args:
            table: Table info object
            schema_name: Optional schema name for context
            
        Returns:
            Table embedding
        """
        try:
            # Convert table to text representation
            table_text = self._table_to_text(table)
            
            # Generate embedding
            embedding_vector = self.model.encode(table_text)
            
            # Create embedding ID
            embedding_id = self._generate_embedding_id("table", table.table_name, table_text)
            
            # Prepare metadata
            metadata = {
                'table_name': table.table_name,
                'schema_name': schema_name,
                'column_count': len(table.columns),
                'has_primary_key': any(col.is_primary_key for col in table.columns),
                'has_foreign_keys': any(col.is_foreign_key for col in table.columns),
                'nullable_columns': sum(1 for col in table.columns if col.is_nullable),
                'model_name': self.model_name,
                'text_length': len(table_text)
            }
            
            # Prepare schema data
            schema_data = {
                'table_name': table.table_name,
                'schema_name': schema_name,
                'columns': [col.column_name for col in table.columns],
                'column_types': [col.data_type for col in table.columns],
                'primary_keys': [col.column_name for col in table.columns if col.is_primary_key],
                'foreign_keys': [col.column_name for col in table.columns if col.is_foreign_key],
                'description': getattr(table, 'description', '')
            }
            
            return SchemaEmbedding(
                embedding_id=embedding_id,
                embedding_type=EmbeddingType.TABLE,
                embedding=embedding_vector,
                schema_data=schema_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error generating table embedding for {table.table_name}: {e}")
            raise
    
    def generate_column_embedding(self, column: ColumnInfo, table_name: str = None, schema_name: str = None) -> SchemaEmbedding:
        """
        Generate embedding for column
        
        Args:
            column: Column info object
            table_name: Optional table name for context
            schema_name: Optional schema name for context
            
        Returns:
            Column embedding
        """
        try:
            # Convert column to text representation
            column_text = self._column_to_text(column, table_name)
            
            # Generate embedding
            embedding_vector = self.model.encode(column_text)
            
            # Create embedding ID
            embedding_id = self._generate_embedding_id("column", f"{table_name}.{column.column_name}", column_text)
            
            # Prepare metadata
            metadata = {
                'column_name': column.column_name,
                'table_name': table_name,
                'schema_name': schema_name,
                'data_type': column.data_type,
                'is_primary_key': column.is_primary_key,
                'is_foreign_key': column.is_foreign_key,
                'is_nullable': column.is_nullable,
                'has_default': bool(column.default_value),
                'model_name': self.model_name,
                'text_length': len(column_text)
            }
            
            # Prepare schema data
            schema_data = {
                'column_name': column.column_name,
                'table_name': table_name,
                'schema_name': schema_name,
                'data_type': column.data_type,
                'max_length': column.max_length,
                'is_primary_key': column.is_primary_key,
                'is_foreign_key': column.is_foreign_key,
                'is_nullable': column.is_nullable,
                'default_value': column.default_value,
                'description': getattr(column, 'description', '')
            }
            
            return SchemaEmbedding(
                embedding_id=embedding_id,
                embedding_type=EmbeddingType.COLUMN,
                embedding=embedding_vector,
                schema_data=schema_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error generating column embedding for {column.column_name}: {e}")
            raise
    
    def generate_query_embedding(self, query_text: str) -> np.ndarray:
        """
        Generate embedding for search query
        
        Args:
            query_text: Query text
            
        Returns:
            Query embedding vector
        """
        try:
            return self.model.encode(query_text)
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
    
    def generate_pattern_embedding(self, pattern_text: str) -> SchemaEmbedding:
        """
        Generate embedding for schema pattern
        
        Args:
            pattern_text: Pattern description text
            
        Returns:
            Pattern embedding
        """
        try:
            # Generate embedding
            embedding_vector = self.model.encode(pattern_text)
            
            # Create embedding ID
            embedding_id = self._generate_embedding_id("pattern", "pattern", pattern_text)
            
            # Prepare metadata
            metadata = {
                'pattern_text': pattern_text,
                'model_name': self.model_name,
                'text_length': len(pattern_text)
            }
            
            # Prepare schema data
            schema_data = {
                'pattern_text': pattern_text,
                'pattern_type': 'custom'
            }
            
            return SchemaEmbedding(
                embedding_id=embedding_id,
                embedding_type=EmbeddingType.PATTERN,
                embedding=embedding_vector,
                schema_data=schema_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error generating pattern embedding: {e}")
            raise
    
    def _schema_to_text(self, schema: SchemaResponse) -> str:
        """Convert schema to text representation"""
        text_parts = []
        
        # Schema name and description
        text_parts.append(f"Schema: {schema.schema_name}")
        if hasattr(schema, 'description') and schema.description:
            text_parts.append(f"Description: {schema.description}")
        
        # Tables summary
        table_names = [table.table_name for table in schema.tables]
        text_parts.append(f"Tables: {', '.join(table_names)}")
        
        # Column information
        for table in schema.tables:
            table_info = f"Table {table.table_name}:"
            
            column_descriptions = []
            for col in table.columns:
                col_desc = f"{col.column_name} ({col.data_type})"
                if col.is_primary_key:
                    col_desc += " PRIMARY KEY"
                if col.is_foreign_key:
                    col_desc += " FOREIGN KEY"
                if not col.is_nullable:
                    col_desc += " NOT NULL"
                column_descriptions.append(col_desc)
            
            table_info += " " + ", ".join(column_descriptions)
            text_parts.append(table_info)
        
        # Relationships
        if schema.relationships:
            relationships_text = "Relationships: " + ", ".join(
                f"{rel.get('from_table', '')}.{rel.get('from_column', '')} -> "
                f"{rel.get('to_table', '')}.{rel.get('to_column', '')}"
                for rel in schema.relationships
            )
            text_parts.append(relationships_text)
        
        return " ".join(text_parts)
    
    def _table_to_text(self, table: TableInfo) -> str:
        """Convert table to text representation"""
        text_parts = []
        
        # Table name
        text_parts.append(f"Table: {table.table_name}")
        
        # Table description
        if hasattr(table, 'description') and table.description:
            text_parts.append(f"Description: {table.description}")
        
        # Column details
        column_descriptions = []
        primary_keys = []
        foreign_keys = []
        
        for col in table.columns:
            col_desc = f"{col.column_name} {col.data_type}"
            
            if col.max_length:
                col_desc += f"({col.max_length})"
            
            attributes = []
            if col.is_primary_key:
                attributes.append("PRIMARY KEY")
                primary_keys.append(col.column_name)
            if col.is_foreign_key:
                attributes.append("FOREIGN KEY")
                foreign_keys.append(col.column_name)
            if not col.is_nullable:
                attributes.append("NOT NULL")
            if col.default_value:
                attributes.append(f"DEFAULT {col.default_value}")
            
            if attributes:
                col_desc += " " + " ".join(attributes)
            
            column_descriptions.append(col_desc)
        
        text_parts.append("Columns: " + ", ".join(column_descriptions))
        
        # Key information
        if primary_keys:
            text_parts.append(f"Primary Keys: {', '.join(primary_keys)}")
        if foreign_keys:
            text_parts.append(f"Foreign Keys: {', '.join(foreign_keys)}")
        
        return " ".join(text_parts)
    
    def _column_to_text(self, column: ColumnInfo, table_name: str = None) -> str:
        """Convert column to text representation"""
        text_parts = []
        
        # Column identification
        if table_name:
            text_parts.append(f"Column: {table_name}.{column.column_name}")
        else:
            text_parts.append(f"Column: {column.column_name}")
        
        # Data type
        type_desc = column.data_type
        if column.max_length:
            type_desc += f"({column.max_length})"
        text_parts.append(f"Type: {type_desc}")
        
        # Attributes
        attributes = []
        if column.is_primary_key:
            attributes.append("PRIMARY KEY")
        if column.is_foreign_key:
            attributes.append("FOREIGN KEY")
        if not column.is_nullable:
            attributes.append("NOT NULL")
        if column.default_value:
            attributes.append(f"DEFAULT {column.default_value}")
        
        if attributes:
            text_parts.append("Attributes: " + ", ".join(attributes))
        
        # Description
        if hasattr(column, 'description') and column.description:
            text_parts.append(f"Description: {column.description}")
        
        return " ".join(text_parts)
    
    def _generate_embedding_id(self, embedding_type: str, identifier: str, content: str) -> str:
        """Generate unique embedding ID"""
        # Create hash from type, identifier, and content
        hash_input = f"{embedding_type}:{identifier}:{content}:{self.model_name}"
        hash_object = hashlib.md5(hash_input.encode())
        return f"{embedding_type}_{hash_object.hexdigest()[:12]}"
    
    def batch_generate_embeddings(
        self,
        items: List[Union[SchemaResponse, TableInfo, ColumnInfo]],
        batch_size: int = 32
    ) -> List[SchemaEmbedding]:
        """
        Generate embeddings in batches for better performance
        
        Args:
            items: List of schema items to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embeddings
        """
        embeddings = []
        
        try:
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_embeddings = []
                
                for item in batch:
                    if isinstance(item, SchemaResponse):
                        embedding = self.generate_schema_embedding(item)
                    elif isinstance(item, TableInfo):
                        embedding = self.generate_table_embedding(item)
                    elif isinstance(item, ColumnInfo):
                        embedding = self.generate_column_embedding(item)
                    else:
                        logger.warning(f"Unknown item type: {type(item)}")
                        continue
                    
                    batch_embeddings.append(embedding)
                
                embeddings.extend(batch_embeddings)
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(items) + batch_size - 1)//batch_size}")
            
            logger.info(f"Generated {len(embeddings)} embeddings total")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {e}")
            raise
    
    def update_embedding(self, embedding: SchemaEmbedding, new_data: Dict[str, Any]) -> SchemaEmbedding:
        """
        Update existing embedding with new data
        
        Args:
            embedding: Existing embedding
            new_data: New schema data
            
        Returns:
            Updated embedding
        """
        try:
            # Update schema data
            embedding.schema_data.update(new_data)
            
            # Regenerate text representation based on embedding type
            if embedding.embedding_type == EmbeddingType.SCHEMA:
                # For schema embeddings, recreate text from updated data
                text_parts = [f"Schema: {embedding.schema_data.get('schema_name', '')}"]
                if embedding.schema_data.get('tables'):
                    text_parts.append(f"Tables: {', '.join(embedding.schema_data['tables'])}")
                new_text = " ".join(text_parts)
            elif embedding.embedding_type == EmbeddingType.TABLE:
                # For table embeddings
                text_parts = [f"Table: {embedding.schema_data.get('table_name', '')}"]
                if embedding.schema_data.get('columns'):
                    text_parts.append(f"Columns: {', '.join(embedding.schema_data['columns'])}")
                new_text = " ".join(text_parts)
            else:
                # For other types, use existing approach
                new_text = str(new_data)
            
            # Regenerate embedding
            new_embedding_vector = self.model.encode(new_text)
            
            # Update embedding properties
            embedding.embedding = new_embedding_vector
            embedding.updated_at = datetime.utcnow()
            embedding.version += 1
            
            # Update metadata
            embedding.metadata.update({
                'text_length': len(new_text),
                'last_updated': datetime.utcnow().isoformat()
            })
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error updating embedding {embedding.embedding_id}: {e}")
            raise
