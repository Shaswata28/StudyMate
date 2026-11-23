from functools import lru_cache

import ollama
from pydantic import BaseModel, Field, ValidationError
from typing import Annotated

from app.core.config import settings
from app.services.prompt_service import prompt_service


@lru_cache(maxsize=1)
def ollama_client():
    return ollama.AsyncClient(host=settings.OLLAMA_BASE_URL, timeout=180)


class ChatFlowchart(BaseModel):
    steps: list[Annotated[str, Field(min_length=1, max_length=90)]] = Field(max_length=8)
    explanation: str = Field(max_length=350)


async def generate_chat(system_prompt: str, history: list[dict], question: str, images: list[bytes], *, flowchart=False) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    for index, message in enumerate(history):
        role = "assistant" if message["role"] == "model" else "user"
        limit = 700 if index >= len(history) - 2 else 300
        messages.append({"role": role, "content": message["content"][:limit]})

    user_message = {"role": "user", "content": question}
    if images:
        user_message["images"] = images
    messages.append(user_message)
    model = settings.vision_model if images else settings.tutor_model
    thinking_options = {"think": False} if model.startswith(("qwen3:", "qwen3.5:")) else {}
    if flowchart:
        messages[0]["content"] += (
            "\nReturn JSON with an ordered list of 3 to 8 short step labels, and a short explanation. "
            "Use an empty steps list and explain the gap if there is insufficient evidence. "
            "StudyMate draws arrows between consecutive steps. Do not write Mermaid syntax."
        )
        thinking_options["format"] = ChatFlowchart.model_json_schema()
    response = await ollama_client().chat(
        model=model,
        messages=messages,
        options={"num_ctx": settings.LLM_CONTEXT_SIZE, "num_predict": settings.LLM_MAX_RESPONSE_TOKENS},
        **thinking_options,
    )
    if flowchart:
        from app.services.diagram_service import label

        try:
            draft = ChatFlowchart.model_validate_json(response.message.content or "")
        except ValidationError as error:
            raise RuntimeError("The tutor could not generate a valid diagram. Try asking for a shorter process.") from error
        steps = [step.strip() for step in draft.steps if step.strip()]
        if len(steps) < 2:
            return draft.explanation or "There is not enough information to draw this process."
        nodes = [f'n{index}["{label(step)}"]' for index, step in enumerate(steps, 1)]
        return "\x60\x60\x60mermaid\nflowchart TD\n    " + " --> ".join(nodes) + "\n\x60\x60\x60\n\n" + draft.explanation
    answer = prompt_service.clean_output(response.message.content or "")
    if not answer:
        raise RuntimeError("Ollama returned an empty answer")
    return answer
