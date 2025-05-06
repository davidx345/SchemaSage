import os
import re
import aiohttp
import asyncio
from fastapi import HTTPException
from ..config import get_settings
import logging
from typing import Dict, Any
import json
from ..config import settings

settings = get_settings()
logger = logging.getLogger(__name__)

class ModelUnavailableError(Exception):
    """Raised when a model is temporarily unavailable"""
    pass

async def wait_for_model(session: aiohttp.ClientSession, model_name: str, timeout: int = 30) -> bool:
    """Wait for model to load, returns True if model becomes available"""
    start_time = asyncio.get_event_loop().time()
    url = f"https://api-inference.huggingface.co/models/{model_name}"
    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }

    while asyncio.get_event_loop().time() - start_time < timeout:
        try:
            async with session.post(url, headers=headers, json={"inputs": "test"}, timeout=5) as response:
                if response.status != 503:
                    return True
                await asyncio.sleep(2)  # Wait before retrying
        except Exception:
            await asyncio.sleep(2)  # Wait before retrying
    return False

async def ai_schema_detect(data: str, retry_count: int = 0, max_retries: int = 3) -> dict:
    """Detect schema using OpenAI API."""
    if not settings.is_openai_key_valid:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured or invalid.")
    
    try:
        headers = settings.get_openai_headers()
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": "You are a database schema expert. Analyze this data and return a JSON schema."},
                {"role": "user", "content": f"""Given the following data, infer a database schema. Return only valid JSON in this format:
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
  ]
}}

Data to analyze:
{data}

Return only the JSON schema, no other text."""}
            ],
            "max_tokens": 1024,
            "temperature": 0.1,
            "top_p": 1.0
        }

        timeout = aiohttp.ClientTimeout(total=15)  # 15 second total timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(
                    f"{settings.OPENAI_API_BASE}/chat/completions",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"OpenAI API request failed: {error_text}")
                        if retry_count < max_retries:
                            logger.info(f"Retrying request (attempt {retry_count + 1}/{max_retries})")
                            return await ai_schema_detect(data, retry_count + 1, max_retries)
                        raise HTTPException(status_code=500, detail=f"OpenAI API request failed after {max_retries} retries: {error_text}")
                    
                    result = await resp.json()
                    text = result["choices"][0]["message"]["content"]
                    match = re.search(r'\{[\s\S]*\}', text)
                    
                    if match:
                        try:
                            parsed = json.loads(match.group(0))
                            if "tables" in parsed and isinstance(parsed["tables"], list):
                                logger.info("Successfully generated schema using OpenAI")
                                return parsed
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse JSON from OpenAI response")
                    
                    if retry_count < max_retries:
                        logger.info(f"Invalid response format, retrying (attempt {retry_count + 1}/{max_retries})")
                        return await ai_schema_detect(data, retry_count + 1, max_retries)
                    raise HTTPException(status_code=500, detail="Failed to generate valid schema from OpenAI response")
            except asyncio.TimeoutError:
                logger.error("Request timed out")
                if retry_count < max_retries:
                    logger.info(f"Retrying after timeout (attempt {retry_count + 1}/{max_retries})")
                    return await ai_schema_detect(data, retry_count + 1, max_retries)
                raise HTTPException(status_code=504, detail="Request timed out after multiple retries")
    except Exception as e:
        logger.error(f"Schema detection error: {str(e)}")
        if retry_count < max_retries:
            logger.info(f"Retrying after error (attempt {retry_count + 1}/{max_retries})")
            return await ai_schema_detect(data, retry_count + 1, max_retries)
        raise HTTPException(status_code=500, detail=f"Schema detection failed after {max_retries} retries: {str(e)}")

async def detect_schema(data: str) -> Dict[str, Any]:
    """Detect schema using OpenAI's chat completion."""
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a database expert. Analyze the provided data and return a JSON schema."
            },
            {
                "role": "user",
                "content": f"""Analyze this data and return a JSON schema with tables and relationships.
                The schema should be in this format:
                {{
                    "tables": [
                        {{
                            "name": "table_name",
                            "columns": [
                                {{
                                    "name": "column_name",
                                    "data_type": "type",
                                    "is_nullable": boolean,
                                    "is_primary_key": boolean,
                                    "is_foreign_key": boolean
                                }}
                            ]
                        }}
                    ],
                    "relationships": [
                        {{
                            "source_table": "table1",
                            "source_column": "col1",
                            "target_table": "table2",
                            "target_column": "col2",
                            "relationship_type": "one_to_many"
                        }}
                    ]
                }}

                Data to analyze:
                {data}
                
                Return only valid JSON, no other text."""
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.OPENAI_API_BASE}/chat/completions",
                headers=settings.get_openai_headers(),
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 2000
                }
            ) as response:
                if response.status != 200:
                    raise Exception(f"OpenAI API error: {await response.text()}")
                
                data = await response.json()
                schema_text = data["choices"][0]["message"]["content"]
                
                # Parse the JSON response
                try:
                    schema = json.loads(schema_text)
                    return schema
                except json.JSONDecodeError:
                    raise Exception("Failed to parse schema JSON from OpenAI response")
                
    except Exception as e:
        raise Exception(f"Failed to detect schema: {str(e)}")
