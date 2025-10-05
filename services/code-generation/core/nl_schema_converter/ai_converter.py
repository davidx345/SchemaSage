"""
AI-powered schema conversion using external AI services
"""

import json
import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

from config import settings
from models.schemas import TableInfo, ColumnInfo, Relationship, SchemaResponse, SchemaMetadata

logger = logging.getLogger(__name__)


class AISchemaConverter:
    """
    AI-powered schema generation using OpenAI (GPT-4) first, then fallback to Gemini
    """
    
    def __init__(self):
        self.api_timeout = 30
        self.max_retries = 3
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
    
    async def generate_schema_with_ai(
        self,
        description: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[SchemaResponse]:
        """
        Generate schema using AI service (OpenAI first, then Gemini fallback)
        
        Args:
            description: Natural language description
            options: Additional options for schema generation
            
        Returns:
            Generated schema or None if failed
        """
        if not self.openai_client and not settings.GEMINI_API_KEY:
            logger.warning("No AI API keys configured for schema generation")
            return None

        try:
            logger.info(f"Generating schema with AI for: {description[:100]}...")
            
            # Build enhanced prompt for production-ready schema
            prompt = self._build_enhanced_schema_generation_prompt(description, options)
            
            # Try OpenAI first, then fallback to Gemini
            ai_response = await self._make_ai_request(prompt)
            
            if ai_response:
                # Parse response to schema
                schema = self._parse_ai_response_to_schema(ai_response, description)
                logger.info("Successfully generated schema with AI")
                return schema
            
        except Exception as e:
            logger.error(f"AI schema generation failed: {str(e)}")
        
        return None
    
    async def enhance_schema_with_ai(
        self,
        tables: List[TableInfo],
        description: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[TableInfo]:
        """
        Enhance existing schema using AI (OpenAI first, then Gemini fallback)
        
        Args:
            tables: Existing table definitions
            description: Original description
            options: Enhancement options
            
        Returns:
            Enhanced table definitions
        """
        if not self.openai_client and not settings.GEMINI_API_KEY:
            logger.debug("No AI API keys available, returning tables as-is")
            return tables
        
        try:
            # Build enhancement prompt
            prompt = self._build_enhancement_prompt(tables, description, options)
            
            # Make AI request with fallback
            ai_response = await self._make_ai_request(prompt)
            
            if ai_response:
                # Parse enhanced schema
                enhanced_schema = self._parse_enhancement_response(ai_response, tables)
                if enhanced_schema:
                    logger.info("Successfully enhanced schema with AI")
                    return enhanced_schema
            
        except Exception as e:
            logger.error(f"AI schema enhancement failed: {str(e)}")
        
        # Return original tables if enhancement fails
        return tables
    
    async def suggest_relationships_with_ai(
        self,
        tables: List[TableInfo],
        description: str
    ) -> List[Relationship]:
        """
        Suggest relationships using AI (OpenAI first, then Gemini fallback)
        
        Args:
            tables: Table definitions
            description: Original description
            
        Returns:
            Suggested relationships
        """
        if not self.openai_client and not settings.GEMINI_API_KEY:
            logger.debug("No AI API keys available for relationship suggestions")
            return []
        
        try:
            # Build relationship prompt
            prompt = self._build_relationship_prompt(tables, description)
            
            # Make AI request with fallback
            ai_response = await self._make_ai_request(prompt)
            
            if ai_response:
                # Parse relationships
                relationships = self._parse_relationship_response(ai_response, tables)
                logger.info(f"AI suggested {len(relationships)} relationships")
                return relationships
            
        except Exception as e:
            logger.error(f"AI relationship suggestion failed: {str(e)}")
        
        return []
    
    async def _make_ai_request(self, prompt: str) -> Optional[str]:
        """
        Make AI request with fallback: OpenAI (GPT-4) first, then Gemini
        
        Args:
            prompt: Prompt text
            
        Returns:
            AI response text or None if failed
        """
        # Try OpenAI first
        if self.openai_client:
            try:
                logger.info("Trying OpenAI API (GPT-4) for schema generation")
                return await self._make_openai_request(prompt)
            except Exception as e:
                logger.warning(f"OpenAI API failed, falling back to Gemini: {e}")
        
        # Fallback to Gemini
        if settings.GEMINI_API_KEY:
            try:
                logger.info("Using Gemini API for schema generation")
                return await self._make_gemini_request(prompt)
            except Exception as e:
                logger.error(f"Gemini API also failed: {e}")
                raise
        
        raise Exception("No working AI API available")
    
    async def _make_openai_request(self, prompt: str) -> Optional[str]:
        """
        Make request to OpenAI API using GPT-4
        
        Args:
            prompt: Prompt text
            
        Returns:
            AI response text or None if failed
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior database architect and schema expert. Always respond with valid, production-ready JSON schemas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4096
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean the response (remove markdown formatting if present)
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            return content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _make_gemini_request(self, prompt: str) -> Optional[str]:
        """
        Make request to Gemini API
        
        Args:
            prompt: Prompt text
            
        Returns:
            AI response text or None if failed
        """
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": settings.GEMINI_API_KEY}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,  # Lower temperature for more consistent output
                "maxOutputTokens": 4096
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        url, 
                        headers=headers, 
                        params=params, 
                        json=data, 
                        timeout=self.api_timeout
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    
                    if "candidates" in result and result["candidates"]:
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        logger.warning("No candidates in AI response")
                        return None
                        
            except httpx.TimeoutException:
                logger.warning(f"AI request timeout (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    raise
            except httpx.HTTPError as e:
                logger.error(f"AI request HTTP error: {e}")
                if attempt == self.max_retries - 1:
                    raise
            except Exception as e:
                logger.error(f"AI request error: {e}")
                if attempt == self.max_retries - 1:
                    raise
        
        return None
    
    def _build_enhanced_schema_generation_prompt(
        self,
        description: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build enhanced prompt for production-ready schema generation"""
        options = options or {}
        
        database_type = options.get('database_type', 'PostgreSQL')
        include_indexes = options.get('include_indexes', True)
        include_constraints = options.get('include_constraints', True)
        include_security = options.get('include_security', True)
        
        return f"""
You are a senior database architect with 15+ years of experience designing production-grade database schemas. 
Convert this natural language description into a comprehensive, enterprise-ready database schema for {database_type}.

REQUIREMENTS DESCRIPTION:
{description}

Generate a detailed JSON response with the following structure. Include ALL the following elements for a production-ready system:

{{
  "tables": [
    {{
      "name": "table_name",
      "description": "detailed table description with business context",
      "columns": [
        {{
          "name": "column_name",
          "type": "String|Integer|Float|Boolean|DateTime|Text|JSON|UUID|JSONB",
          "nullable": true/false,
          "is_primary_key": true/false,
          "unique": true/false,
          "default": "default_value or null",
          "description": "detailed column description with business meaning",
          "validation": "email|url|phone|regex pattern (if applicable)",
          "max_length": 255,
          "constraints": ["check constraints", "foreign key constraints"],
          "index_type": "btree|gin|gist|hash (if indexed)",
          "security_level": "public|restricted|encrypted"
        }}
      ],
      "indexes": [
        {{
          "name": "idx_table_column",
          "columns": ["column1", "column2"],
          "type": "btree|gin|gist|hash",
          "unique": true/false,
          "purpose": "performance optimization reason"
        }}
      ],
      "constraints": [
        {{
          "name": "constraint_name",
          "type": "check|unique|foreign_key",
          "definition": "constraint definition",
          "purpose": "business rule being enforced"
        }}
      ],
      "triggers": [
        {{
          "name": "trigger_name",
          "event": "before_insert|after_update|etc",
          "purpose": "audit|validation|business logic"
        }}
      ],
      "estimated_rows": 10000,
      "growth_pattern": "linear|exponential|seasonal",
      "audit_fields": true
    }}
  ],
  "relationships": [
    {{
      "source_table": "table1",
      "source_column": "table2_id",
      "target_table": "table2", 
      "target_column": "id",
      "type": "one_to_one|one_to_many|many_to_many",
      "on_delete": "cascade|restrict|set_null",
      "on_update": "cascade|restrict",
      "description": "business relationship explanation"
    }}
  ],
  "security_policies": [
    {{
      "table": "table_name",
      "policy_name": "row_level_security_policy",
      "rule": "security rule definition",
      "applies_to": "select|insert|update|delete"
    }}
  ],
  "performance_recommendations": [
    {{
      "table": "table_name",
      "recommendation": "specific performance optimization",
      "reasoning": "why this optimization is needed"
    }}
  ],
  "business_rules": [
    {{
      "rule": "business rule description",
      "implementation": "how it's enforced in the schema",
      "tables_affected": ["table1", "table2"]
    }}
  ]
}}

ADDITIONAL REQUIREMENTS:
1. Include proper audit fields (created_at, updated_at, created_by, updated_by) for all main entities
2. Add soft delete support where appropriate (deleted_at, is_deleted)
3. Include proper indexing strategy for performance
4. Add data validation constraints
5. Consider security and privacy requirements
6. Include version/optimistic locking fields where needed
7. Add proper foreign key relationships with cascading rules
8. Include check constraints for data integrity
9. Consider partitioning strategies for large tables
10. Add proper data types optimized for the use case

Respond with ONLY the JSON - no explanations, no markdown formatting.
"""
    
    def _build_schema_generation_prompt(
        self,
        description: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for complete schema generation"""
        options = options or {}
        
        database_type = options.get('database_type', 'PostgreSQL')
        include_indexes = options.get('include_indexes', True)
        include_constraints = options.get('include_constraints', True)
        
        return f"""
You are a database architect. Convert this natural language description into a detailed database schema for {database_type}.

Description: {description}

Return a JSON response with the following structure:
{{
  "tables": [
    {{
      "name": "table_name",
      "description": "table description",
      "columns": [
        {{
          "name": "column_name",
          "type": "String|Integer|Float|Boolean|DateTime|Text|JSON|UUID",
          "nullable": true/false,
          "is_primary_key": true/false,
          "unique": true/false,
          "default": "default_value",
          "description": "column description",
          "validation": "email|url|phone (if applicable)",
          "max_length": 255
        }}
      ]
    }}
  ],
  "relationships": [
    {{
      "source_table": "table1",
      "source_column": "table2_id",
      "target_table": "table2", 
      "target_column": "id",
      "type": "one-to-one|one-to-many|many-to-one|many-to-many"
    }}
  ]
}}

Guidelines:
1. Always include id (primary key), created_at, updated_at for each table
2. Infer appropriate data types from field names and context
3. Add validation where applicable (email, url, phone)
4. Create logical relationships between entities
5. Use snake_case for names
6. Include foreign key columns for relationships
7. Consider common database patterns and best practices
8. Add appropriate constraints and indexes if specified
9. Use descriptive column and table names
10. Include reasonable default values where appropriate

{"Include indexes and constraints in the schema." if include_indexes or include_constraints else ""}

Return only valid JSON, no explanation text.
"""
    
    def _build_enhancement_prompt(
        self,
        tables: List[TableInfo],
        description: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for schema enhancement"""
        # Convert tables to JSON for the prompt
        tables_json = []
        for table in tables:
            table_dict = {
                "name": table.name,
                "description": table.description,
                "columns": [
                    {
                        "name": col.name,
                        "type": col.type,
                        "nullable": col.nullable,
                        "is_primary_key": col.is_primary_key,
                        "unique": getattr(col, 'unique', False),
                        "default": getattr(col, 'default', None),
                        "description": col.description
                    }
                    for col in table.columns
                ]
            }
            tables_json.append(table_dict)
        
        return f"""
You are a database architect. Enhance this existing database schema based on the original description and best practices.

Original Description: {description}

Current Schema:
{json.dumps(tables_json, indent=2)}

Please enhance the schema by:
1. Adding missing columns that would be useful for the described system
2. Improving data types and constraints
3. Adding validation rules where appropriate
4. Suggesting better column names if needed
5. Adding indexes and performance considerations
6. Ensuring all necessary fields are present for the business logic

Return the enhanced schema in the same JSON format:
{{
  "tables": [
    {{
      "name": "table_name",
      "description": "enhanced description",
      "columns": [
        {{
          "name": "column_name",
          "type": "String|Integer|Float|Boolean|DateTime|Text|JSON|UUID",
          "nullable": true/false,
          "is_primary_key": true/false,
          "unique": true/false,
          "default": "default_value",
          "description": "column description",
          "validation": "email|url|phone (if applicable)",
          "max_length": 255
        }}
      ]
    }}
  ]
}}

Return only valid JSON, no explanation text.
"""
    
    def _build_relationship_prompt(
        self,
        tables: List[TableInfo],
        description: str
    ) -> str:
        """Build prompt for relationship suggestions"""
        table_names = [table.name for table in tables]
        table_info = []
        
        for table in tables:
            columns = [col.name for col in table.columns]
            table_info.append(f"- {table.name}: {', '.join(columns)}")
        
        return f"""
You are a database architect. Analyze these tables and suggest appropriate relationships based on the description.

Description: {description}

Tables:
{chr(10).join(table_info)}

Suggest relationships that make sense for this system. Consider:
1. Which entities should reference each other
2. What type of relationship makes sense (one-to-many, many-to-many, etc.)
3. Foreign key placements
4. Business logic implied by the description

Return a JSON array of relationships:
[
  {{
    "source_table": "table1",
    "source_column": "table2_id",
    "target_table": "table2",
    "target_column": "id",
    "type": "one-to-one|one-to-many|many-to-one|many-to-many",
    "description": "explanation of the relationship"
  }}
]

Return only valid JSON, no explanation text.
"""
    
    def _parse_ai_response_to_schema(
        self,
        ai_response: str,
        original_description: str
    ) -> SchemaResponse:
        """Parse AI JSON response into SchemaResponse object"""
        try:
            # Extract JSON from response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_str = ai_response[json_start:json_end]
            data = json.loads(json_str)
            
            # Convert to TableInfo objects
            tables = []
            for table_data in data.get('tables', []):
                columns = []
                for col_data in table_data.get('columns', []):
                    column = ColumnInfo(
                        name=col_data.get('name', ''),
                        type=col_data.get('type', 'String'),
                        nullable=col_data.get('nullable', True),
                        is_primary_key=col_data.get('is_primary_key', False),
                        unique=col_data.get('unique', False),
                        default=col_data.get('default'),
                        description=col_data.get('description', ''),
                        validation=col_data.get('validation'),
                        max_length=col_data.get('max_length')
                    )
                    columns.append(column)
                
                # Extract primary keys
                primary_keys = [col.name for col in columns if col.is_primary_key]
                if not primary_keys:
                    primary_keys = ['id']  # Default primary key
                
                table = TableInfo(
                    name=table_data.get('name', ''),
                    columns=columns,
                    description=table_data.get('description', ''),
                    primary_keys=primary_keys
                )
                tables.append(table)
            
            # Convert to Relationship objects
            relationships = []
            for rel_data in data.get('relationships', []):
                relationship = Relationship(
                    source_table=rel_data.get('source_table', ''),
                    source_column=rel_data.get('source_column', ''),
                    target_table=rel_data.get('target_table', ''),
                    target_column=rel_data.get('target_column', ''),
                    type=rel_data.get('type', 'one-to-many')
                )
                relationships.append(relationship)
            
            metadata = SchemaMetadata(
                version="1.0",
                created_at=datetime.utcnow().isoformat(),
                description=f"AI-generated from: {original_description[:200]}...",
                source="ai_generation"
            )
            
            return SchemaResponse(
                tables=tables,
                relationships=relationships,
                metadata=metadata
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {e}")
            raise Exception(f"AI response parsing failed: Invalid JSON - {str(e)}")
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise Exception(f"AI response parsing failed: {str(e)}")
    
    def _parse_enhancement_response(
        self,
        ai_response: str,
        original_tables: List[TableInfo]
    ) -> Optional[List[TableInfo]]:
        """Parse AI enhancement response"""
        try:
            # Extract JSON from response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return None
            
            json_str = ai_response[json_start:json_end]
            data = json.loads(json_str)
            
            # Convert to TableInfo objects
            enhanced_tables = []
            for table_data in data.get('tables', []):
                columns = []
                for col_data in table_data.get('columns', []):
                    column = ColumnInfo(
                        name=col_data.get('name', ''),
                        type=col_data.get('type', 'String'),
                        nullable=col_data.get('nullable', True),
                        is_primary_key=col_data.get('is_primary_key', False),
                        unique=col_data.get('unique', False),
                        default=col_data.get('default'),
                        description=col_data.get('description', ''),
                        validation=col_data.get('validation'),
                        max_length=col_data.get('max_length')
                    )
                    columns.append(column)
                
                # Extract primary keys
                primary_keys = [col.name for col in columns if col.is_primary_key]
                if not primary_keys:
                    primary_keys = ['id']
                
                table = TableInfo(
                    name=table_data.get('name', ''),
                    columns=columns,
                    description=table_data.get('description', ''),
                    primary_keys=primary_keys
                )
                enhanced_tables.append(table)
            
            return enhanced_tables
            
        except Exception as e:
            logger.error(f"Failed to parse enhancement response: {e}")
            return None
    
    def _parse_relationship_response(
        self,
        ai_response: str,
        tables: List[TableInfo]
    ) -> List[Relationship]:
        """Parse AI relationship response"""
        try:
            # Extract JSON from response
            json_start = ai_response.find('[')
            json_end = ai_response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                return []
            
            json_str = ai_response[json_start:json_end]
            data = json.loads(json_str)
            
            # Convert to Relationship objects
            relationships = []
            table_names = {table.name for table in tables}
            
            for rel_data in data:
                source_table = rel_data.get('source_table', '')
                target_table = rel_data.get('target_table', '')
                
                # Only include relationships for existing tables
                if source_table in table_names and target_table in table_names:
                    relationship = Relationship(
                        source_table=source_table,
                        source_column=rel_data.get('source_column', ''),
                        target_table=target_table,
                        target_column=rel_data.get('target_column', ''),
                        type=rel_data.get('type', 'one-to-many')
                    )
                    relationships.append(relationship)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Failed to parse relationship response: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return bool(settings.GEMINI_API_KEY)
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the AI service"""
        return {
            "service": "Google Gemini",
            "available": self.is_available(),
            "timeout": self.api_timeout,
            "max_retries": self.max_retries
        }
