"""
Gemini Integration for SchemaSage
Provides services for schema detection, code generation, and chat using Google's Gemini API.
"""
import re
import json
import logging
import google.generativeai as genai
from typing import Dict, List, Any, Optional, Union
from ..config import get_settings
from ..models.schemas import ChatResponse

settings = get_settings()
logger = logging.getLogger(__name__)

class GeminiServiceError(Exception):
    """Base exception for Gemini service errors"""
    pass

def setup_gemini(api_key: Optional[str] = None):
    """Set up Gemini API with API key from settings or provided key"""
    key = api_key or settings.GEMINI_API_KEY
    if not key:
        logger.error("Gemini API key is not configured")
        raise GeminiServiceError("Gemini API key is not configured")
    try:
        genai.configure(api_key=key)
        logger.info(f"Gemini API initialized with model: {settings.GEMINI_MODEL}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {str(e)}")
        raise GeminiServiceError(f"Failed to initialize Gemini API: {str(e)}")

async def chat_with_gemini(messages: List[Dict[str, str]], schema: Any = None, api_key: Optional[str] = None) -> ChatResponse:
    """Generate chat responses using Gemini API"""
    try:
        setup_gemini(api_key)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Convert messages to Gemini format and include schema context
        prompt = "You are a helpful database schema expert assistant.\n\n"
        
        # Add schema context if provided
        if schema:
            prompt += f"Database schema information: {json.dumps(schema.model_dump())}\n\n"
        
        # Add conversation history
        for msg in messages:
            role = "user" if msg["role"] == "user" else "assistant"
            prompt += f"{role.capitalize()}: {msg['content']}\n"
            
        # Generate response
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            logger.warning("Empty response from Gemini API")
            raise GeminiServiceError("Empty response from Gemini API")
            
        return ChatResponse(
            response=response.text,
            suggestions=[
                "Tell me more about this schema",
                "How can I optimize this schema?",
                "What indexes should I add?"
            ]
        )
        
    except Exception as e:
        logger.error(f"Error generating chat response with Gemini: {str(e)}")
        raise GeminiServiceError(f"Failed to generate chat response: {str(e)}")

async def detect_schema_with_gemini(data: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Detect schema using Gemini API"""
    try:
        setup_gemini(api_key)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        prompt = f"""Analyze this data and infer a database schema. Return only valid JSON in this format:
{{
  "tables": [
    {{
      "name": "table_name",
      "columns": [
        {{
          "name": "column_name",
          "data_type": "type",
          "is_primary_key": false,
          "is_foreign_key": false,
          "nullable": true
        }}
      ]
    }}
  ],
  "relationships": []
}}

Data to analyze:
{data}

Return ONLY the JSON schema, no other text or explanation."""
        
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            logger.warning("Empty response from Gemini API")
            raise GeminiServiceError("Empty response from Gemini API")
            
        # Extract JSON from response
        text = response.text
        match = re.search(r'\{[\s\S]*\}', text)
        
        if match:
            try:
                parsed = json.loads(match.group(0))
                if "tables" in parsed and isinstance(parsed["tables"], list):
                    logger.info("Successfully generated schema using Gemini")
                    return parsed
                else:
                    logger.warning("Invalid schema structure returned by Gemini")
                    raise GeminiServiceError("Invalid schema structure returned by Gemini")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
                raise GeminiServiceError(f"Failed to parse Gemini response as JSON: {str(e)}")
        else:
            logger.error("No JSON found in Gemini response")
            raise GeminiServiceError("No JSON found in Gemini response")
            
    except Exception as e:
        logger.error(f"Error detecting schema with Gemini: {str(e)}")
        raise GeminiServiceError(f"Failed to detect schema: {str(e)}")

async def generate_code_with_gemini(schema: Any, format: str, options: Optional[Dict[str, Any]] = None, api_key: Optional[str] = None) -> str:
    """Generate code from schema using Gemini API"""
    try:
        setup_gemini(api_key)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Format options for the prompt
        options_text = ""
        if options:
            options_text = "Options:\n" + "\n".join([f"- {k}: {v}" for k, v in options.items()])

        schema_json = json.dumps(schema.model_dump(), indent=2) if hasattr(schema, 'model_dump') else json.dumps(schema, indent=2)
        
        prompt = f"""Generate {format} code for the following database schema:

Schema:
{schema_json}

{options_text}

Requirements:
1. Generate clean, production-ready code
2. Include proper typing and validation
3. Follow best practices for {format}
4. Include helpful comments
5. Return ONLY the code, no explanations or markdown formatting

The code should be complete and ready to use."""
        
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            logger.warning("Empty code generation response from Gemini API")
            raise GeminiServiceError("Empty code generation response from Gemini API")
            
        # Clean the response to extract only code
        code = response.text
        # Remove markdown code blocks if present
        code = re.sub(r'^```[\w]*\n', '', code)
        code = re.sub(r'\n```$', '', code)
        
        return code
            
    except Exception as e:
        logger.error(f"Error generating code with Gemini: {str(e)}")
        raise GeminiServiceError(f"Failed to generate code: {str(e)}")

async def verify_gemini_connection(api_key: Optional[str] = None) -> tuple[bool, str]:
    """Verify connection to Gemini API"""
    try:
        setup_gemini(api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello, world!")
        if response and response.text:
            return True, "API key is valid and working"
        return False, "API returned empty response"
    except Exception as e:
        return False, str(e)