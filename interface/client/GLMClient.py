"""
GLM API Client for BlackBox5

This module provides a GLM-compatible API client that can be used
as a drop-in replacement for Anthropic's Claude API in BlackBox5.

GLM (General Language Model) is developed by Zhipu AI and provides
similar capabilities to Claude for agent orchestration.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class GLMMessage:
    """A message in the conversation"""
    role: str  # "user", "assistant", or "system"
    content: str


@dataclass
class GLMResponse:
    """Response from GLM API"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class GLMClientError(Exception):
    """Base exception for GLM client errors"""
    pass


class GLMAPIError(GLMClientError):
    """Exception raised when GLM API returns an error"""
    pass


class GLMClient:
    """
    GLM API Client compatible with BlackBox5 agent system.

    This client provides a simple interface to GLM's chat completion API
    and can be used as a replacement for Anthropic's Claude SDK.

    Example:
        ```python
        client = GLMClient(api_key="your-api-key")

        response = client.create(
            messages=[
                {"role": "user", "content": "Hello, GLM!"}
            ],
            model="glm-4.7"
        )

        print(response.content)
        ```
    """

    # Available GLM models
    MODELS = {
        "glm-4.7": "glm-4.7",
        "glm-4-plus": "glm-4-plus",
        "glm-4-air": "glm-4-air",
        "glm-4-flash": "glm-4-flash",
        "glm-4-long": "glm-4-long",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        timeout: int = 120,
        max_retries: int = 3,
        enable_prompt_compression: bool = True,
        compression_config: Optional[Dict[str, Any]] = None,
        enable_token_optimization: bool = True,
    ):
        """
        Initialize GLM client.

        Args:
            api_key: GLM API key (defaults to GLM_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            enable_prompt_compression: Enable LLMLingua prompt compression
            compression_config: Optional configuration for LLMLingua
        """
        self.api_key = api_key or os.getenv("GLM_API_KEY")
        if not self.api_key:
            raise GLMClientError(
                "GLM API key not found. Set GLM_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_prompt_compression = enable_prompt_compression
        self.compression_config = compression_config or {}
        self.enable_token_optimization = enable_token_optimization

        # Initialize token optimizer
        self.token_optimizer = None
        if enable_token_optimization:
            try:
                from TokenOptimizer import TokenOptimizer
                self.token_optimizer = TokenOptimizer()
                logger.info("GLM Client: Token optimization enabled")
            except ImportError:
                logger.warning("TokenOptimizer not available, optimization disabled")
                self.enable_token_optimization = False

        # Try to import requests, provide helpful error if not available
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise GLMClientError(
                "The 'requests' library is required for GLMClient. "
                "Install it with: pip install requests"
            )

        # Initialize LLMLingua compressor if enabled
        self.compressor = None
        if self.enable_prompt_compression:
            try:
                import sys
                from pathlib import Path

                # Add parent directory to path to import LLMLinguaCompressor
                # Assuming GLMClient is in 2-engine/01-core/client/
                # and LLMLinguaCompressor is in engine/core/
                client_dir = Path(__file__).parent
                engine_core = client_dir.parent.parent.parent / "engine" / "core"
                if str(engine_core) not in sys.path:
                    sys.path.insert(0, str(engine_core))

                from LLMLinguaCompressor import get_compressor

                self.compressor = get_compressor(self.compression_config)
                logger.info("GLM Client: LLMLingua compression enabled")
            except ImportError as e:
                logger.warning(f"LLMLingua not available: {e}. Compression disabled.")
                self.enable_prompt_compression = False
            except Exception as e:
                logger.warning(f"Failed to initialize LLMLingua: {e}. Compression disabled.")
                self.enable_prompt_compression = False

        logger.info(f"GLM Client initialized with model: {self.base_url}")

    def _validate_model(self, model: str) -> str:
        """Validate and return model name"""
        model = model.lower()
        if model not in self.MODELS:
            valid_models = ", ".join(self.MODELS.keys())
            logger.warning(
                f"Unknown model '{model}'. Valid models: {valid_models}. "
                f"Using default 'glm-4.7'"
            )
            return "glm-4.7"
        return model

    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for GLM API"""
        formatted = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            elif isinstance(msg, GLMMessage):
                formatted.append({
                    "role": msg.role,
                    "content": msg.content
                })
        return formatted

    def create(
        self,
        messages: List[Dict[str, str]],
        model: str = "glm-4.7",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stream: bool = False,
        instruction: Optional[str] = None,
        question: Optional[str] = None,
        **kwargs
    ) -> GLMResponse:
        """
        Create a chat completion.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name (default: glm-4.7)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling threshold
            stream: Whether to stream responses
            instruction: Optional instruction for prompt compression
            question: Optional question for prompt compression
            **kwargs: Additional parameters

        Returns:
            GLMResponse with the generated content

        Raises:
            GLMAPIError: If the API request fails
        """
        model = self._validate_model(model)
        formatted_messages = self._format_messages(messages)

        # Apply LLMLingua compression if enabled
        compression_stats = {}
        if self.enable_prompt_compression and self.compressor:
            try:
                formatted_messages, compression_stats = self.compressor.compress_messages(
                    formatted_messages,
                    instruction=instruction,
                    question=question,
                )
                logger.debug(
                    f"Prompt compression: {compression_stats.get('original_length', 0)} -> "
                    f"{compression_stats.get('compressed_length', 0)} tokens "
                    f"({compression_stats.get('compression_ratio', 1.0):.1%} of original)"
                )
            except Exception as e:
                logger.warning(f"Prompt compression failed, using original: {e}")

        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Add any additional parameters
        payload.update(kwargs)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Sending request to GLM API (attempt {attempt + 1}): "
                    f"{len(messages)} messages"
                )

                response = self.requests.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                response.raise_for_status()
                data = response.json()

                # Extract response content
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                finish_reason = data["choices"][0].get("finish_reason", "stop")

                logger.debug(
                    f"GLM response received: {len(content)} chars, "
                    f"tokens: {usage.get('total_tokens', 'N/A')}"
                )

                return GLMResponse(
                    content=content,
                    model=model,
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    finish_reason=finish_reason
                )

            except self.requests.exceptions.HTTPError as e:
                error_detail = e.response.text if e.response else str(e)
                logger.error(f"GLM API HTTP error: {error_detail}")

                if attempt == self.max_retries - 1:
                    raise GLMAPIError(
                        f"GLM API request failed after {self.max_retries} attempts: {error_detail}"
                    )

                # Exponential backoff
                import time
                time.sleep(2 ** attempt)

            except self.requests.exceptions.RequestException as e:
                logger.error(f"GLM API request error: {e}")

                if attempt == self.max_retries - 1:
                    raise GLMAPIError(f"GLM API request failed: {e}")

                import time
                time.sleep(2 ** attempt)

            except (KeyError, IndexError, json.JSONDecodeError) as e:
                raise GLMAPIError(f"Failed to parse GLM API response: {e}")

    def create_optimized(
        self,
        system_prompt: str,
        agent_persona: str,
        conversation_history: List[Dict[str, str]],
        code_context: str,
        user_query: str,
        task_type: Optional[str] = None,
        model: str = "glm-4.7",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> GLMResponse:
        """
        Create an optimized chat completion with automatic token management.

        This method uses the TokenOptimizer to:
        1. Cache static prompts (system, persona)
        2. Trim conversation to budget
        3. Allocate tokens by task type
        4. Consolidate old messages

        Args:
            system_prompt: Base system prompt
            agent_persona: Agent-specific persona (from agent.md)
            conversation_history: Previous conversation messages
            code_context: Code/files context
            user_query: Current user query
            task_type: Optional task type (auto-detected if None)
            model: Model name
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            **kwargs: Additional parameters

        Returns:
            GLMResponse with the generated content
        """
        if not self.token_optimizer:
            # Fallback to regular create
            logger.warning("TokenOptimizer not available, using regular create()")
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'system', 'content': agent_persona},
                *conversation_history,
                {'role': 'user', 'content': user_query}
            ]
            return self.create(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                **kwargs
            )

        # Optimize prompts
        optimization_result = self.token_optimizer.optimize(
            system_prompt=system_prompt,
            agent_persona=agent_persona,
            conversation_history=conversation_history,
            code_context=code_context,
            user_query=user_query,
            task_type=task_type
        )

        # Log optimization stats
        stats = optimization_result.stats
        logger.info(
            f"Token optimization ({stats.get('task_type', 'unknown')}): "
            f"{stats['original_tokens']['total']} -> {stats['optimized_tokens']['total']} input tokens "
            f"({100 * stats['optimized_tokens']['total'] / stats['original_tokens']['total']:.1f}%)"
        )

        # Determine max_tokens from budget if not provided
        if max_tokens is None and 'budget' in stats:
            max_tokens = stats['budget']['total_output']

        # Call create with optimized messages
        return self.create(
            messages=optimization_result.messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs
        )

    async def acreate(
        self,
        messages: List[Dict[str, str]],
        model: str = "glm-4.7",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stream: bool = False,
        **kwargs
    ) -> GLMResponse:
        """
        Async version of create().

        Uses asyncio to run the synchronous request in a thread pool.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.create(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=stream,
                **kwargs
            )
        )

    async def acreate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "glm-4.7",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Create a streaming chat completion.

        Yields chunks of the response as they're generated.

        Args:
            messages: List of message dictionaries
            model: Model name
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            **kwargs: Additional parameters

        Yields:
            str: Response content chunks
        """
        model = self._validate_model(model)
        formatted_messages = self._format_messages(messages)

        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": True,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        payload.update(kwargs)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            import httpx
        except ImportError:
            raise GLMClientError(
                "The 'httpx' library is required for streaming. "
                "Install it with: pip install httpx"
            )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", self.base_url, json=payload, headers=headers) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")

                            if content:
                                yield content

                        except (json.JSONDecodeError, KeyError, IndexError):
                            logger.warning(f"Failed to parse streaming chunk: {data_str}")
                            continue


class GLMClientMock:
    """
    Mock GLM client for testing without API calls.

    This is useful for integration tests and development.
    """

    def __init__(self, **kwargs):
        self.calls = []

    def _validate_model(self, model: str) -> str:
        """Mock model validation - mimic real client behavior"""
        valid_models = ["glm-4.7", "glm-4-plus", "glm-4-air", "glm-4-flash", "glm-4-long"]
        model_lower = model.lower()
        if model_lower not in valid_models:
            return "glm-4.7"
        return model_lower

    def _format_messages(self, messages: list) -> list:
        """Mock message formatting - handle both dict and GLMMessage objects"""
        formatted = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            elif hasattr(msg, "role") and hasattr(msg, "content"):
                formatted.append({
                    "role": msg.role,
                    "content": msg.content
                })
            else:
                formatted.append(msg)
        return formatted

    def create(self, messages, **kwargs) -> GLMResponse:
        """Return mock response"""
        self.calls.append({"messages": messages, "kwargs": kwargs})

        # Generate a simple response based on the last user message
        user_content = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                user_content = msg.get("content", "")
                break
            elif hasattr(msg, "role") and msg.role == "user":
                user_content = msg.content
                break

        mock_response = f"[MOCK GLM RESPONSE] I received: {user_content[:100]}..."

        return GLMResponse(
            content=mock_response,
            model="glm-4.7-mock",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop"
        )

    async def acreate(self, messages, **kwargs) -> GLMResponse:
        """Async mock response"""
        return self.create(messages, **kwargs)


def create_glm_client(
    api_key: Optional[str] = None,
    mock: bool = False,
    **kwargs
) -> Union[GLMClient, GLMClientMock]:
    """
    Factory function to create a GLM client.

    Args:
        api_key: GLM API key (defaults to GLM_API_KEY env var)
        mock: If True, return a mock client for testing
        **kwargs: Additional arguments passed to GLMClient

    Returns:
        GLMClient or GLMClientMock instance
    """
    if mock:
        logger.info("Creating mock GLM client")
        return GLMClientMock(**kwargs)

    return GLMClient(api_key=api_key, **kwargs)


# Convenience function for simple chat completions
def chat(
    prompt: str,
    model: str = "glm-4.7",
    api_key: Optional[str] = None,
    mock: bool = False,
    **kwargs
) -> str:
    """
    Simple chat completion interface.

    Args:
        prompt: User prompt
        model: Model name
        api_key: GLM API key
        mock: If True, use mock client
        **kwargs: Additional parameters

    Returns:
        str: Response content
    """
    client = create_glm_client(api_key=api_key, mock=mock)
    response = client.create(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        **kwargs
    )
    return response.content


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(level=logging.INFO)

    # Test with mock client
    print("Testing GLM Client (mock mode)...")
    mock_client = create_glm_client(mock=True)
    response = mock_client.create([
        {"role": "user", "content": "Hello, GLM!"}
    ])
    print(f"Mock response: {response.content}")

    # Test with real API if API key is available
    if os.getenv("GLM_API_KEY"):
        print("\nTesting GLM Client (real API)...")
        try:
            real_client = create_glm_client()
            response = real_client.create([
                {"role": "user", "content": "Say 'Hello from GLM!' in one sentence."}
            ])
            print(f"Real response: {response.content}")
            print(f"Tokens used: {response.usage['total_tokens']}")
        except GLMAPIError as e:
            print(f"API Error: {e}", file=sys.stderr)
    else:
        print("\nSkipping real API test (no GLM_API_KEY set)")
