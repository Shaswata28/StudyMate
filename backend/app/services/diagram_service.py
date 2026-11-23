from typing import Literal

from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.llm_service import ollama_client


class Node(BaseModel):
    id: int = Field(ge=1)
    label: str = Field(min_length=1, max_length=100)
    kind: Literal["step", "decision"]
    source: int = Field(ge=1)


class Edge(BaseModel):
    start: int
    end: int
    label: str = Field(max_length=50)


class DiagramDraft(BaseModel):
    title: str = Field(max_length=100)
    nodes: list[Node] = Field(max_length=18)
    edges: list[Edge] = Field(max_length=30)
    missing: str = Field(max_length=300)

    def mermaid(self, source_count: int) -> str:
        if self.missing.strip():
            raise ValueError(self.missing)
        nodes = {node.id: node for node in self.nodes}
        if len(nodes) < 2 or len(nodes) != len(self.nodes) or any(n.source > source_count for n in self.nodes):
            raise ValueError("Use unique nodes with known sources.")
        outgoing = {key: [] for key in nodes}
        incoming = set()
        for edge in self.edges:
            if edge.start not in nodes or edge.end not in nodes or edge.start == edge.end:
                raise ValueError("Each edge must connect two different existing nodes.")
            outgoing[edge.start].append(edge)
            incoming.add(edge.end)
        starts = set(nodes) - incoming
        if len(starts) != 1:
            raise ValueError("The flowchart needs one starting step.")
        visited = set(starts)
        pending = list(starts)
        while pending:
            for edge in outgoing[pending.pop()]:
                if edge.end not in visited:
                    visited.add(edge.end)
                    pending.append(edge.end)
        if len(visited) != len(nodes):
            raise ValueError("Every step must be reachable from the start.")
        for node in self.nodes:
            branches = outgoing[node.id]
            if node.kind == "decision" and (
                len(branches) < 2 or len({edge.end for edge in branches}) != len(branches)
                or len({edge.label.strip().casefold() for edge in branches if edge.label.strip()}) != len(branches)
            ):
                raise ValueError("Each decision needs two or more distinct labeled paths.")
            if node.kind == "step" and len(branches) > 1:
                raise ValueError("Mark branching steps as decisions.")

        lines = ["flowchart TD"]
        for node in self.nodes:
            text = f'"{label(node.label)}"'
            shape = "{" + text + "}" if node.kind == "decision" else "[" + text + "]"
            lines.append(f"    n{node.id}{shape}")
        for edge in self.edges:
            condition = f'|"{label(edge.label)}"|' if edge.label.strip() else ""
            lines.append(f"    n{edge.start} -->{condition} n{edge.end}")
        return "\n".join(lines)


def label(value: str) -> str:
    return "".join(char if char.isalnum() or char in " .,:?+-_/" else f"#{ord(char)};" for char in value)


class Participant(BaseModel):
    id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=80)


class SequenceMessage(BaseModel):
    start: int
    end: int
    label: str = Field(min_length=1, max_length=100)
    source: int = Field(ge=1)


class SequenceDraft(BaseModel):
    title: str = Field(max_length=100)
    participants: list[Participant] = Field(max_length=10)
    messages: list[SequenceMessage] = Field(max_length=24)
    missing: str = Field(max_length=300)

    @property
    def source_numbers(self):
        return {message.source for message in self.messages}

    def mermaid(self, source_count: int) -> str:
        if self.missing.strip():
            raise ValueError(self.missing)
        ids = {participant.id for participant in self.participants}
        if len(ids) < 2 or len(ids) != len(self.participants) or not self.messages:
            raise ValueError("Use at least two unique participants and include ordered messages.")
        if any(message.start not in ids or message.end not in ids or message.source > source_count for message in self.messages):
            raise ValueError("Every message must reference known participants and a known source.")
        if {actor for message in self.messages for actor in (message.start, message.end)} != ids:
            raise ValueError("Every participant must send or receive a message.")
        lines = ["sequenceDiagram"]
        lines.extend(f"    participant p{actor.id} as {label(actor.name)}" for actor in self.participants)
        lines.extend(f"    p{message.start}->>p{message.end}: {label(message.label)}" for message in self.messages)
        return "\n".join(lines)


async def draft_diagram(question: str, excerpts: list[str], *, model=None, correction="", diagram_type="flowchart"):
    sequence = diagram_type == "sequence"
    draft_type = SequenceDraft if sequence else DiagramDraft
    schema = draft_type.model_json_schema()
    schema["$defs"]["SequenceMessage" if sequence else "Node"]["properties"]["source"]["enum"] = list(range(1, len(excerpts) + 1))
    numbered = "\n\n".join(f"Source {index}: {text}" for index, text in enumerate(excerpts, 1))
    response = await ollama_client().chat(
        model=model or settings.tutor_model, stream=False, think=False, format=schema,
        options={"temperature": 0, "num_ctx": settings.LLM_CONTEXT_SIZE, "num_predict": settings.LLM_MAX_RESPONSE_TOKENS},
        messages=[
            {"role": "system", "content": (
                "Create a sequence diagram using only the evidence. List participants with unique integer IDs, "
                "then messages in chronological order using those IDs and the source number for each message. "
                "If the evidence cannot support the sequence, explain the gap in missing. Otherwise leave missing empty."
            ) if sequence else (
                "Build a flowchart of the requested process using only the numbered evidence. Use integer node IDs. "
                "Each node must cite its source number. Reuse a source number when it supports several nodes. "
                "Put a check and its question in a single decision node. Each decision needs distinct labeled edges to all outcomes. "
                "Connect each ordinary step to the next step with an edge whose label is empty. "
                "Example edges for a binary decision after a normal step: "
                "[{\"start\":1,\"end\":2,\"label\":\"\"},{\"start\":2,\"end\":3,\"label\":\"Yes\"},"
                "{\"start\":2,\"end\":4,\"label\":\"No\"}]. "
                "If any required branch or step is absent from the evidence, "
                "return a brief explanation in missing with empty nodes and edges. Otherwise set missing to empty."
            )},
            {"role": "user", "content": f"{question}\n\n{numbered}\n\n{correction}"},
        ],
    )
    return draft_type.model_validate_json(response.message.content or "")
