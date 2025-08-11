"""
Natural Language Processing Service
Converts natural language queries to SQL
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import re
import openai
from anthropic import Anthropic

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.ai_features import (
    NaturalLanguageQuery, AIModel, QueryComplexity
)
from ...core.database import DatabaseManager
from ...utils.logging import get_logger
from ...utils.exceptions import AIProcessingError

logger = get_logger(__name__)

class NaturalLanguageProcessor:
    """Natural language to SQL conversion service."""
    
    def __init__(self, db_manager: DatabaseManager, ai_models: Dict[str, AIModel]):
        self.db_manager = db_manager
        self.ai_models = ai_models
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize AI clients
        for model in ai_models.values():
            if model.provider == "openai" and not self.openai_client:
                self.openai_client = openai.AsyncOpenAI()
            elif model.provider == "anthropic" and not self.anthropic_client:
                self.anthropic_client = Anthropic()
    
    async def process_natural_language_query(
        self,
        query_text: str,
        workspace_id: str,
        connection_id: str,
        user_context: Dict[str, Any],
        session: AsyncSession
    ) -> NaturalLanguageQuery:
        """Convert natural language to SQL query."""
        
        nl_query = NaturalLanguageQuery(
            workspace_id=workspace_id,
            connection_id=connection_id,
            natural_language_query=query_text,
            user_context=user_context
        )
        
        try:
            # Get database schema context
            schema_context = await self._get_schema_context(connection_id)
            
            # Classify intent
            nl_query.intent_classification = await self._classify_intent(query_text)
            
            # Extract entities
            nl_query.entity_extraction = await self._extract_entities(query_text, schema_context)
            
            # Assess complexity
            nl_query.complexity_assessment = self._assess_complexity(query_text)
            
            # Generate SQL
            sql_result = await self._generate_sql(query_text, schema_context, nl_query)
            nl_query.generated_sql = sql_result['sql']
            nl_query.confidence_score = sql_result['confidence']
            nl_query.alternative_queries = sql_result.get('alternatives', [])
            
            # Validate generated SQL
            validation_result = await self._validate_sql(nl_query.generated_sql, connection_id)
            nl_query.syntax_valid = validation_result['syntax_valid']
            nl_query.semantic_valid = validation_result['semantic_valid']
            nl_query.execution_safe = validation_result['execution_safe']
            
            nl_query.processed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Natural language processing failed: {e}")
            raise AIProcessingError(f"Natural language processing failed: {e}")
        
        return nl_query
    
    async def _get_schema_context(self, connection_id: str) -> Dict[str, Any]:
        """Get database schema context for AI processing."""
        
        connection = await self.db_manager.get_connection(connection_id)
        
        context = {
            'tables': [],
            'relationships': [],
            'common_patterns': []
        }
        
        try:
            # Get table information
            tables_query = """
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """
            
            async with connection.execute(text(tables_query)) as result:
                rows = await result.fetchall()
                
                current_table = None
                table_info = None
                
                for row in rows:
                    table_name, column_name, data_type, is_nullable = row
                    
                    if table_name != current_table:
                        if table_info:
                            context['tables'].append(table_info)
                        
                        current_table = table_name
                        table_info = {
                            'name': table_name,
                            'columns': []
                        }
                    
                    table_info['columns'].append({
                        'name': column_name,
                        'type': data_type,
                        'nullable': is_nullable == 'YES'
                    })
                
                if table_info:
                    context['tables'].append(table_info)
        
        except Exception as e:
            logger.warning(f"Could not get schema context: {e}")
        
        return context
    
    async def _classify_intent(self, query_text: str) -> str:
        """Classify the intent of the natural language query."""
        
        # Simple rule-based classification
        query_lower = query_text.lower()
        
        if any(word in query_lower for word in ['show', 'list', 'get', 'find', 'select', 'what']):
            return "retrieval"
        elif any(word in query_lower for word in ['add', 'insert', 'create', 'new']):
            return "insertion"
        elif any(word in query_lower for word in ['update', 'change', 'modify', 'set']):
            return "update"
        elif any(word in query_lower for word in ['delete', 'remove', 'drop']):
            return "deletion"
        elif any(word in query_lower for word in ['count', 'sum', 'average', 'total']):
            return "aggregation"
        else:
            return "unknown"
    
    async def _extract_entities(
        self, 
        query_text: str, 
        schema_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract entities (tables, columns) from natural language query."""
        
        entities = []
        query_lower = query_text.lower()
        
        # Extract table names
        for table in schema_context.get('tables', []):
            table_name = table['name'].lower()
            if table_name in query_lower:
                entities.append({
                    'type': 'table',
                    'value': table['name'],
                    'confidence': 0.8
                })
            
            # Check for column names
            for column in table['columns']:
                column_name = column['name'].lower()
                if column_name in query_lower:
                    entities.append({
                        'type': 'column',
                        'value': column['name'],
                        'table': table['name'],
                        'confidence': 0.7
                    })
        
        return entities
    
    def _assess_complexity(self, query_text: str) -> QueryComplexity:
        """Assess the complexity of the natural language query."""
        
        complexity_indicators = 0
        query_lower = query_text.lower()
        
        # Count complexity factors
        if any(word in query_lower for word in ['join', 'with', 'and', 'where']):
            complexity_indicators += 1
        
        if any(word in query_lower for word in ['group by', 'order by', 'having']):
            complexity_indicators += 1
        
        if any(word in query_lower for word in ['subquery', 'nested', 'inner', 'outer']):
            complexity_indicators += 2
        
        if len(query_text.split()) > 20:
            complexity_indicators += 1
        
        # Classify based on indicators
        if complexity_indicators == 0:
            return QueryComplexity.SIMPLE
        elif complexity_indicators <= 2:
            return QueryComplexity.MODERATE
        elif complexity_indicators <= 4:
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.VERY_COMPLEX
    
    async def _generate_sql(
        self, 
        query_text: str, 
        schema_context: Dict[str, Any], 
        nl_query: NaturalLanguageQuery
    ) -> Dict[str, Any]:
        """Generate SQL from natural language using AI."""
        
        # Prepare context for AI
        context = self._prepare_ai_context(schema_context, nl_query)
        
        # Generate prompt
        prompt = self._build_sql_generation_prompt(query_text, context)
        
        # Use AI model to generate SQL
        if self.openai_client:
            return await self._generate_sql_with_openai(prompt)
        elif self.anthropic_client:
            return await self._generate_sql_with_anthropic(prompt)
        else:
            # Fallback to rule-based generation
            return await self._generate_sql_rule_based(query_text, schema_context)
    
    def _prepare_ai_context(
        self, 
        schema_context: Dict[str, Any], 
        nl_query: NaturalLanguageQuery
    ) -> str:
        """Prepare database context for AI prompt."""
        
        context_parts = []
        
        # Add table information
        context_parts.append("Database Schema:")
        for table in schema_context.get('tables', []):
            table_desc = f"Table: {table['name']}"
            columns = [f"{col['name']} ({col['type']})" for col in table['columns']]
            table_desc += f" - Columns: {', '.join(columns)}"
            context_parts.append(table_desc)
        
        # Add entity information
        if nl_query.entity_extraction:
            context_parts.append("\nIdentified Entities:")
            for entity in nl_query.entity_extraction:
                context_parts.append(f"- {entity['type']}: {entity['value']}")
        
        return "\n".join(context_parts)
    
    def _build_sql_generation_prompt(self, query_text: str, context: str) -> str:
        """Build prompt for SQL generation."""
        
        return f"""
Convert the following natural language query to SQL.

Database Context:
{context}

Natural Language Query: {query_text}

Requirements:
- Generate valid SQL syntax
- Use only tables and columns that exist in the schema
- Ensure the query is safe to execute (no destructive operations unless explicitly requested)
- Provide confidence score (0.0 to 1.0)
- If multiple interpretations are possible, provide alternatives

Response format:
{{
    "sql": "SELECT ...",
    "confidence": 0.85,
    "explanation": "This query retrieves...",
    "alternatives": ["SELECT ...", "SELECT ..."]
}}
"""
    
    async def _generate_sql_with_openai(self, prompt: str) -> Dict[str, Any]:
        """Generate SQL using OpenAI."""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert SQL developer. Convert natural language to SQL queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # Fallback if not valid JSON
                return {
                    "sql": content,
                    "confidence": 0.5,
                    "explanation": "Generated by AI",
                    "alternatives": []
                }
        
        except Exception as e:
            logger.error(f"OpenAI SQL generation failed: {e}")
            raise AIProcessingError(f"SQL generation failed: {e}")
    
    async def _generate_sql_with_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Generate SQL using Anthropic Claude."""
        
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            
            # Parse JSON response
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                return {
                    "sql": content,
                    "confidence": 0.5,
                    "explanation": "Generated by AI",
                    "alternatives": []
                }
        
        except Exception as e:
            logger.error(f"Anthropic SQL generation failed: {e}")
            raise AIProcessingError(f"SQL generation failed: {e}")
    
    async def _generate_sql_rule_based(
        self, 
        query_text: str, 
        schema_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate SQL using rule-based approach (fallback)."""
        
        query_lower = query_text.lower()
        
        # Simple rule-based SQL generation
        if 'show' in query_lower or 'list' in query_lower:
            # Try to find table name
            for table in schema_context.get('tables', []):
                if table['name'].lower() in query_lower:
                    return {
                        "sql": f"SELECT * FROM {table['name']} LIMIT 10;",
                        "confidence": 0.6,
                        "explanation": "Basic SELECT query",
                        "alternatives": []
                    }
        
        return {
            "sql": "-- Could not generate SQL from natural language query",
            "confidence": 0.0,
            "explanation": "Query too complex for rule-based generation",
            "alternatives": []
        }
    
    async def _validate_sql(self, sql: str, connection_id: str) -> Dict[str, bool]:
        """Validate generated SQL."""
        
        validation = {
            'syntax_valid': False,
            'semantic_valid': False,
            'execution_safe': False
        }
        
        try:
            connection = await self.db_manager.get_connection(connection_id)
            
            # Check for dangerous operations
            sql_upper = sql.upper()
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
            
            if not any(keyword in sql_upper for keyword in dangerous_keywords):
                validation['execution_safe'] = True
            
            # Try to explain the query (syntax check)
            try:
                async with connection.execute(text(f"EXPLAIN {sql}")) as result:
                    await result.fetchone()
                validation['syntax_valid'] = True
                validation['semantic_valid'] = True
            except Exception:
                validation['syntax_valid'] = False
                validation['semantic_valid'] = False
        
        except Exception as e:
            logger.warning(f"SQL validation failed: {e}")
        
        return validation
