"""
AI-Powered Schema Enhancement Module

Uses OpenAI API first, then falls back to Gemini API to enhance schema detection with AI insights.
"""
from typing import Dict, List, Optional, Any, Union
import httpx
import json
import logging
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from models.schemas import TableInfo, Relationship, RelationshipType
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AISchemaEnhancer:
    """Uses AI to enhance schema detection and suggest relationships"""
    
    def __init__(self):
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
        # Initialize OpenAI client if available and configured
        self.openai_client = None
        if OPENAI_AVAILABLE and self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
    
    async def enhance_schema_with_ai(self, table_info: TableInfo, data_sample: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use AI to enhance schema detection with additional insights."""
        if not self.openai_client and not self.gemini_api_key:
            logger.warning("No AI API keys configured, skipping AI enhancement")
            return {}
        
        try:
            # Prepare data for AI analysis
            schema_summary = self._prepare_schema_summary(table_info, data_sample)
            
            # Try OpenAI first, then fallback to Gemini
            ai_insights = await self._call_ai_api(schema_summary)
            
            return ai_insights
        
        except Exception as e:
            logger.error(f"Error in AI schema enhancement: {e}")
            return {}
    
    def _prepare_schema_summary(self, table_info: TableInfo, data_sample: List[Dict[str, Any]] = None) -> str:
        """Prepare a summary of the schema for AI analysis."""
        summary_parts = [
            f"Table: {table_info.name}",
            f"Rows: {table_info.row_count}",
            "Columns:"
        ]
        
        for column in table_info.columns[:20]:  # Limit to first 20 columns
            col_summary = f"  - {column.name}: {column.type}"
            if column.nullable:
                col_summary += " (nullable)"
            if column.constraints:
                if column.constraints.get('unique'):
                    col_summary += " (unique)"
                if column.constraints.get('enum_like'):
                    col_summary += " (limited values)"
            summary_parts.append(col_summary)
        
        if len(table_info.columns) > 20:
            summary_parts.append(f"  ... and {len(table_info.columns) - 20} more columns")
        
        # Add sample data if available
        if data_sample:
            summary_parts.extend([
                "",
                "Sample data (first 3 rows):"
            ])
            for i, row in enumerate(data_sample[:3]):
                if isinstance(row, dict):
                    # Show only first 10 fields to keep prompt manageable
                    limited_row = dict(list(row.items())[:10])
                    summary_parts.append(f"  Row {i+1}: {limited_row}")
        
        return "\n".join(summary_parts)
    
    async def _call_ai_api(self, schema_summary: str) -> Dict[str, Any]:
        """Call AI API with fallback: OpenAI first, then Gemini."""
        # Try OpenAI first
        if self.openai_client:
            try:
                logger.info("Trying OpenAI API for schema enhancement")
                return await self._call_openai_api(schema_summary)
            except Exception as e:
                logger.warning(f"OpenAI API failed, falling back to Gemini: {e}")
        
        # Fallback to Gemini
        if self.gemini_api_key:
            try:
                logger.info("Using Gemini API for schema enhancement")
                return await self._call_gemini_api(schema_summary)
            except Exception as e:
                logger.error(f"Gemini API also failed: {e}")
                raise
        
        raise Exception("No working AI API available")
    
    async def _call_openai_api(self, schema_summary: str) -> Dict[str, Any]:
        """Call OpenAI API to get AI insights about the schema."""
        prompt = f"""
As a senior database architect, analyze this data schema and provide comprehensive insights:

{schema_summary}

Provide detailed analysis in JSON format with these fields:
1. "business_context": Detailed analysis of the business domain and use case this data represents
2. "table_purpose": Comprehensive explanation of this table's role in the system architecture
3. "key_relationships": Detailed potential relationships with other tables, including cardinality and foreign key suggestions
4. "data_quality_issues": Comprehensive data quality concerns including validation rules, constraints, and potential edge cases
5. "optimization_suggestions": Advanced suggestions for schema optimization including indexing strategies, partitioning, and performance considerations
6. "missing_columns": Detailed analysis of columns that might be missing for production use (audit fields, soft deletes, versioning, etc.)
7. "semantic_meaning": In-depth semantic analysis of key columns with business context
8. "security_considerations": Security best practices for this schema (encryption, access control, data masking)
9. "scalability_recommendations": Recommendations for handling growth and performance at scale
10. "advanced_features": Suggestions for advanced database features (triggers, stored procedures, views, etc.)

Provide production-ready, enterprise-level insights. Respond with valid JSON only.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior database architect and backend engineer. Always respond with valid JSON containing detailed, production-ready insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2048
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean the response (remove markdown formatting if present)
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
            
        except json.JSONDecodeError:
            logger.warning("OpenAI response was not valid JSON, returning raw text")
            return {"raw_response": content}
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _call_gemini_api(self, schema_summary: str) -> Dict[str, Any]:
        """Call Gemini API to get AI insights about the schema."""
        prompt = f"""
Analyze this data schema and provide insights:

{schema_summary}

Please provide analysis in JSON format with these fields:
1. "business_context": What type of business domain this data likely represents
2. "table_purpose": What this table is likely used for
3. "key_relationships": Potential relationships with other tables
4. "data_quality_issues": Potential data quality concerns
5. "optimization_suggestions": Suggestions for schema optimization
6. "missing_columns": Columns that might be missing for this type of data
7. "semantic_meaning": Semantic meaning of key columns

Respond with valid JSON only.
"""
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        url = f"{self.gemini_base_url}?key={self.gemini_api_key}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the generated text
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Try to parse as JSON
                try:
                    # Clean the response (remove markdown formatting if present)
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("AI response was not valid JSON, returning raw text")
                    return {"raw_response": content}
            
            return {}
    
    async def suggest_relationships(self, tables: List[TableInfo]) -> List[Relationship]:
        """Suggest relationships between tables using AI."""
        if not self.openai_client and not self.gemini_api_key:
            return []
        
        if len(tables) < 2:
            return []
        
        try:
            # Prepare table summaries
            table_summaries = []
            for table in tables:
                summary = f"Table {table.name}:\n"
                for col in table.columns[:10]:  # Limit columns
                    summary += f"  - {col.name}: {col.type}\n"
                table_summaries.append(summary)
            
            combined_summary = "\n".join(table_summaries)
            
            # Try OpenAI first, then fallback to Gemini
            return await self._suggest_relationships_with_ai(combined_summary)
        
        except Exception as e:
            logger.error(f"Error suggesting relationships with AI: {e}")
            return []
    
    async def _suggest_relationships_with_ai(self, combined_summary: str) -> List[Relationship]:
        """Call AI API for relationship suggestions with fallback."""
        # Try OpenAI first
        if self.openai_client:
            try:
                logger.info("Trying OpenAI API for relationship suggestions")
                return await self._suggest_relationships_openai(combined_summary)
            except Exception as e:
                logger.warning(f"OpenAI API failed for relationships, falling back to Gemini: {e}")
        
        # Fallback to Gemini
        if self.gemini_api_key:
            try:
                logger.info("Using Gemini API for relationship suggestions")
                return await self._suggest_relationships_gemini(combined_summary)
            except Exception as e:
                logger.error(f"Gemini API also failed for relationships: {e}")
                return []
        
        return []
    
    async def _suggest_relationships_openai(self, combined_summary: str) -> List[Relationship]:
        """Use OpenAI to suggest relationships."""
        prompt = f"""
Analyze these database tables and suggest relationships between them:

{combined_summary}

Identify potential foreign key relationships. For each relationship, provide:
1. Source table and column
2. Target table and column  
3. Relationship type (one-to-one, one-to-many, many-to-many)
4. Confidence level (high, medium, low)

Respond with JSON array format:
[
  {{
    "source_table": "table_name",
    "source_column": "column_name", 
    "target_table": "table_name",
    "target_column": "column_name",
    "relationship_type": "one-to-many",
    "confidence": "high",
    "reasoning": "explanation"
  }}
]
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a database design expert. Always respond with valid JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1024
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean and parse JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            relationships_data = json.loads(content)
            relationships = []
            
            for rel_data in relationships_data:
                rel_type = RelationshipType.ONE_TO_MANY  # Default
                if rel_data.get("relationship_type") == "one-to-one":
                    rel_type = RelationshipType.ONE_TO_ONE
                elif rel_data.get("relationship_type") == "many-to-many":
                    rel_type = RelationshipType.MANY_TO_MANY
                
                relationship = Relationship(
                    source_table=rel_data.get("source_table", ""),
                    source_column=rel_data.get("source_column", ""),
                    target_table=rel_data.get("target_table", ""),
                    target_column=rel_data.get("target_column", ""),
                    type=rel_type,
                    confidence=0.8 if rel_data.get("confidence") == "high" else 0.6
                )
                relationships.append(relationship)
            
            return relationships
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI relationship suggestions")
            return []
        except Exception as e:
            logger.error(f"OpenAI relationship API error: {e}")
            raise
    
    async def _suggest_relationships_gemini(self, combined_summary: str) -> List[Relationship]:
        """Use Gemini to suggest relationships."""
        prompt = f"""
Analyze these database tables and suggest relationships between them:

{combined_summary}

Identify potential foreign key relationships. For each relationship, provide:
1. Source table and column
2. Target table and column  
3. Relationship type (one-to-one, one-to-many, many-to-many)
4. Confidence level (high, medium, low)

Respond with JSON array format:
[
  {{
    "source_table": "table_name",
    "source_column": "column_name", 
    "target_table": "table_name",
    "target_column": "column_name",
    "relationship_type": "one-to-many",
    "confidence": "high",
    "reasoning": "explanation"
  }}
]
"""
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024
            }
        }
        
        url = f"{self.gemini_base_url}?key={self.gemini_api_key}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Clean and parse JSON
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                try:
                    relationships_data = json.loads(content)
                    relationships = []
                    
                    for rel_data in relationships_data:
                        rel_type = RelationshipType.ONE_TO_MANY  # Default
                        if rel_data.get("relationship_type") == "one-to-one":
                            rel_type = RelationshipType.ONE_TO_ONE
                        elif rel_data.get("relationship_type") == "many-to-many":
                            rel_type = RelationshipType.MANY_TO_MANY
                        
                        relationship = Relationship(
                            source_table=rel_data.get("source_table", ""),
                            source_column=rel_data.get("source_column", ""),
                            target_table=rel_data.get("target_table", ""),
                            target_column=rel_data.get("target_column", ""),
                            type=rel_type,
                            confidence=0.8 if rel_data.get("confidence") == "high" else 0.6
                        )
                        relationships.append(relationship)
                    
                    return relationships
                
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Gemini relationship suggestions")
                    return []
        
        return []
    
    async def enhance_column_semantics(self, table_info: TableInfo) -> Dict[str, Dict[str, Any]]:
        """Use AI to understand the semantic meaning of columns."""
        if not self.openai_client and not self.gemini_api_key:
            return {}
        
        try:
            # Prepare column information
            columns_info = []
            for col in table_info.columns[:20]:  # Limit to avoid token limits
                col_info = f"{col.name}: {col.type}"
                if hasattr(col, 'statistics') and col.statistics and col.statistics.sample_values:
                    col_info += f" (examples: {', '.join(col.statistics.sample_values[:3])})"
                columns_info.append(col_info)
            
            # Try OpenAI first, then fallback to Gemini
            return await self._enhance_column_semantics_with_ai(table_info, columns_info)
        
        except Exception as e:
            logger.error(f"Error enhancing column semantics with AI: {e}")
            return {}
    
    async def _enhance_column_semantics_with_ai(self, table_info: TableInfo, columns_info: List[str]) -> Dict[str, Dict[str, Any]]:
        """Call AI API for column semantics with fallback."""
        # Try OpenAI first
        if self.openai_client:
            try:
                logger.info("Trying OpenAI API for column semantics")
                return await self._enhance_column_semantics_openai(table_info, columns_info)
            except Exception as e:
                logger.warning(f"OpenAI API failed for column semantics, falling back to Gemini: {e}")
        
        # Fallback to Gemini
        if self.gemini_api_key:
            try:
                logger.info("Using Gemini API for column semantics")
                return await self._enhance_column_semantics_gemini(table_info, columns_info)
            except Exception as e:
                logger.error(f"Gemini API also failed for column semantics: {e}")
                return {}
        
        return {}
    
    async def _enhance_column_semantics_openai(self, table_info: TableInfo, columns_info: List[str]) -> Dict[str, Dict[str, Any]]:
        """Use OpenAI to understand column semantics."""
        prompt = f"""
Analyze these database columns and identify their semantic meaning:

Table: {table_info.name}
Columns:
{chr(10).join(columns_info)}

For each column, identify:
1. Business meaning/purpose
2. Data category (e.g., identifier, measurement, category, timestamp, etc.)
3. Potential data privacy concerns (PII, sensitive data)
4. Suggested constraints or validations
5. Common name alternatives in different domains

Respond with JSON format:
{{
  "column_name": {{
    "business_meaning": "description",
    "data_category": "category",
    "privacy_level": "none/low/high", 
    "constraints": ["suggestion1", "suggestion2"],
    "alternatives": ["alt_name1", "alt_name2"]
  }}
}}
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a database semantics expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2048
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean and parse JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI column semantics")
            return {}
        except Exception as e:
            logger.error(f"OpenAI column semantics API error: {e}")
            raise
    
    async def _enhance_column_semantics_gemini(self, table_info: TableInfo, columns_info: List[str]) -> Dict[str, Dict[str, Any]]:
        """Use Gemini to understand column semantics."""
        prompt = f"""
Analyze these database columns and identify their semantic meaning:

Table: {table_info.name}
Columns:
{chr(10).join(columns_info)}

For each column, identify:
1. Business meaning/purpose
2. Data category (e.g., identifier, measurement, category, timestamp, etc.)
3. Potential data privacy concerns (PII, sensitive data)
4. Suggested constraints or validations
5. Common name alternatives in different domains

Respond with JSON format:
{{
  "column_name": {{
    "business_meaning": "description",
    "data_category": "category",
    "privacy_level": "none/low/high", 
    "constraints": ["suggestion1", "suggestion2"],
    "alternatives": ["alt_name1", "alt_name2"]
  }}
}}
"""
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048
            }
        }
        
        url = f"{self.gemini_base_url}?key={self.gemini_api_key}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Clean and parse JSON
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Gemini column semantics")
                    return {}
        
        return {}
