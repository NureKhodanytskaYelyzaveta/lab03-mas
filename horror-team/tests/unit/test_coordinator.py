"""Координатор: делегування, яке обирає модель (тут — сценарій)."""
import asyncio
from collections.abc import AsyncGenerator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from app.coordinator import build_coordinator
from run_cli import run_once


class CallingLlm(BaseLlm):
    turn: int = 0

    async def generate_content_async(self, req, stream=False) -> AsyncGenerator[LlmResponse, None]:
        instruction = str(req.config.system_instruction or "")
        if "horror sound designer" in instruction:
            part = types.Part(text="- тиша перед піком")
        elif self.turn == 0:
            self.turn += 1
            part = types.Part(function_call=types.FunctionCall(
                name="sound_expert", args={"request": "Який звук для коридору?"}))
        else:
            part = types.Part(text="Підсумок: використати тишу перед піком.")
        yield LlmResponse(content=types.Content(role="model", parts=[part]))


def test_coordinator_delegates_to_one_expert():
    result = asyncio.run(run_once(build_coordinator(CallingLlm(model="scripted")),
                                  "Який звук потрібен для темного коридору?"))
    authors = [s["author"] for s in result["trace"]]
    assert "sound_expert" in authors
    assert "level_expert" not in authors and "vfx_expert" not in authors
    assert result["trace"][-1]["text"].startswith("Підсумок")
