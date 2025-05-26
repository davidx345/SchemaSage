from typing import List, Dict, Any
import aiohttp
from app.config import settings
from app.models.schemas import ChatResponse

class ChatError(Exception):
    """Base exception for chat service errors"""
    pass

class ChatService:
    async def get_response(self, schema: Any, messages: List[Dict[str, str]], question: str) -> ChatResponse:
        """Generate a response using OpenAI's chat completion."""
        try:
            # Format messages for OpenAI
            openai_messages = [
                {"role": "system", "content": "You are a helpful assistant specializing in database schemas and SQL."},
                *[{"role": m["role"], "content": m["content"]} for m in messages],
                {"role": "user", "content": question}
            ]
            
            # Call OpenAI API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OPENAI_API_BASE}/chat/completions",
                    headers=settings.get_openai_headers(),
                    json={
                        "model": settings.OPENAI_MODEL,
                        "messages": openai_messages,
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                ) as response:
                    if response.status != 200:
                        raise Exception(f"OpenAI API error: {await response.text()}")
                    
                    data = await response.json()
                    answer = data["choices"][0]["message"]["content"]
                    
                    return ChatResponse(
                        response=answer,
                        suggestions=[
                            "Tell me more about the schema",
                            "How can I optimize this schema?",
                            "What indexes should I add?"
                        ]
                    )
                    
        except Exception as e:
            raise Exception(f"Failed to get chat response: {str(e)}")