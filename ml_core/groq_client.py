import logging
from typing import AsyncGenerator
from groq import AsyncGroq, APIError, APITimeoutError, RateLimitError
from config.settings import settings

logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

async def generate_answer(prompt: str, system_prompt: str) -> str:
    """Generate a complete answer using Groq API."""
    try:
        logger.info(f"Calling Groq API. Model: {settings.GROQ_MODEL}, Prompt length: {len(prompt)} chars")
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=1024
        )
        answer = response.choices[0].message.content or ""
        logger.info(f"Groq API response received. Answer length: {len(answer)} chars")
        return answer
    except RateLimitError as e:
        logger.error(f"Groq API Rate limit exceeded: {e}")
        return f"Rate limit exceeded. Please try again later. Details: {e}"
    except APITimeoutError as e:
        logger.error(f"Groq API timeout: {e}")
        return f"API timeout. Please try again. Details: {e}"
    except APIError as e:
        logger.error(f"Groq API error (status={e.status_code}): {e.message}")
        return f"API error ({e.status_code}): {e.message}"
    except Exception as e:
        logger.error(f"Unexpected Groq API error: {type(e).__name__}: {e}")
        return f"Unexpected error: {type(e).__name__}: {e}"

async def generate_answer_stream(prompt: str, system_prompt: str) -> AsyncGenerator[str, None]:
    """Stream an answer using Groq API."""
    try:
        stream = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=1024,
            stream=True
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except RateLimitError as e:
        logger.error(f"Groq API Rate limit exceeded in stream: {e}")
        yield "I could not generate an answer at this time."
    except APITimeoutError as e:
        logger.error(f"Groq API timeout in stream: {e}")
        yield "I could not generate an answer at this time."
    except APIError as e:
        logger.error(f"Groq API error in stream: {e}")
        yield "I could not generate an answer at this time."
    except Exception as e:
        logger.error(f"Unexpected Groq API error in stream: {e}")
        yield "I could not generate an answer at this time."
