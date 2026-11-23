"""Підмінна модель для тестів: відповідає за сценарієм, без мережі і ключа."""
import json
from collections.abc import AsyncGenerator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types


class ScriptedLlm(BaseLlm):
    """script: {фрагмент системної інструкції: [відповідь1, відповідь2, ...]}.

    Агента впізнаємо за його інструкцією, тому порядок паралельних
    викликів не впливає на результат. Остання відповідь повторюється.
    """
    script: dict[str, list] = {}
    calls: list[str] = []

    async def generate_content_async(self, llm_request: LlmRequest,
                                     stream: bool = False) -> AsyncGenerator[LlmResponse, None]:
        instruction = str(llm_request.config.system_instruction or "")
        for marker, replies in self.script.items():
            if marker in instruction:
                self.calls.append(marker)
                reply = replies.pop(0) if len(replies) > 1 else replies[0]
                text = reply if isinstance(reply, str) else json.dumps(reply, ensure_ascii=False)
                yield LlmResponse(content=types.Content(role="model",
                                                        parts=[types.Part(text=text)]))
                return
        raise AssertionError(f"no scripted reply for instruction: {instruction[:80]}")


class ToolCallingLlm(ScriptedLlm):
    """Як ScriptedLlm, але агент-дослідник спершу викликає search_knowledge,
    а після відповіді інструмента пише підсумок зі сценарію."""
    tool_query: str = "how does silence affect fear"

    async def generate_content_async(self, llm_request: LlmRequest,
                                     stream: bool = False) -> AsyncGenerator[LlmResponse, None]:
        instruction = str(llm_request.config.system_instruction or "")
        marker = "game-design researcher"
        if marker not in instruction:
            async for r in super().generate_content_async(llm_request, stream):
                yield r
            return
        self.calls.append(marker)
        got_tool_result = any(p.function_response for c in llm_request.contents or []
                              for p in c.parts or [])
        if not got_tool_result:
            part = types.Part(function_call=types.FunctionCall(
                name="search_knowledge", args={"query": self.tool_query}))
        else:
            part = types.Part(text=self.script[marker][0])
        yield LlmResponse(content=types.Content(role="model", parts=[part]))
