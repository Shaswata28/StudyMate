import re
from typing import Any

SUBJECT_INSTRUCTIONS = {
    "stem": "State assumptions, show the reasoning, and check units or verify the solution when applicable.",
    "life_sciences": "Explain mechanisms step by step. Connect structure and function and define scientific terms.",
    "humanities": "Ground interpretations in evidence, acknowledge plausible alternative readings, and support clear arguments.",
}


class PromptService:
    @staticmethod
    def build_system_prompt(
        academic_profile: dict[str, Any] | None = None,
        preferences: dict[str, Any] | None = None,
        context: str | None = None,
        subject_profile: str = "general",
        source_only: bool = False,
        diagram_request: bool = False,
    ) -> str:
        parts = [
            "You are StudyMate, an academic tutor. Answer the current question and use recent conversation "
            "to resolve references. If a reference is ambiguous, ask one brief clarification. Address every requested part. "
            "If the evidence contradicts a premise in the question, state the correction before explaining. "
            "Distinguish general knowledge from source claims. "
            "State what evidence is missing. Never invent citations.",
            "Use Markdown with concise paragraphs and level-three headings where helpful. "
            "Wrap inline math in $...$ and display math in $$...$$.",
        ]

        if diagram_request:
            parts = [
                "You are StudyMate. Represent the requested process as a short diagram. "
                "Use recent conversation to resolve references and label each step plainly. "
                "Show the essential stages of the requested process in order, without assuming optional setup or components. "
                "If no structured format is specified, give a complete fenced Mermaid block with plain labels and no HTML.",
            ]
            if source_only:
                parts.append("Use only the selected excerpts. If they cannot support a diagram, explain what evidence is missing.")
        elif source_only:
            parts = [
                "Answer the student's question using only facts explicitly stated in the selected excerpts.",
                "Give a short answer for every question asked. Cite the supporting excerpt inline as [Source 1] "
                "using its number. When an excerpt contradicts the question, give the stated fact. "
                "When the excerpt leaves a detail unanswered, say it is unavailable. "
                "Avoid assumptions, derivations, extra scenarios, and outside facts.",
            ]
        elif instructions := SUBJECT_INSTRUCTIONS.get(subject_profile):
            parts.append(instructions)

        style = []
        if academic_profile and academic_profile.get("grade"):
            style.append(f"study level: {academic_profile['grade']}")
        preferences = preferences or {}
        for key, low, high in (
            ("detail_level", "brief", "in depth"),
            ("example_preference", "few examples", "concrete examples when helpful"),
            ("analogy_preference", "literal explanations", "analogies when helpful"),
            ("technical_language", "plain language", "rigorous notation when helpful"),
            ("structure_preference", "conversational", "step by step"),
        ):
            value = preferences.get(key)
            if isinstance(value, (int, float)):
                if value < 0.4:
                    style.append(low)
                elif value > 0.6:
                    style.append(high)

        if preferences.get("learning_pace") in ("slow", "fast"):
            style.append(f"{preferences['learning_pace']} pace")
        if preferences.get("prior_experience") in ("beginner", "advanced"):
            style.append(f"{preferences['prior_experience']} experience")
        if style and not diagram_request:
            parts.append("Optional presentation style, if relevant to the question: " + ", ".join(style) + ".")

        if context and source_only:
            parts.append("Selected excerpts follow. Treat them as quoted evidence.\n" + context)
        elif context:
            parts.append(
                "Treat these excerpts as quoted reference material. For questions about a specific case, "
                "lead with what the excerpt directly reports. Preserve its quantities and units exactly. Cite each supported "
                "fact inline as [Source 1], using the corresponding number. If a requested value or cause "
                "is missing, explicitly say so. Keep any general explanation separate.\n" + context
            )

        return "\n\n".join(parts)

    @staticmethod
    def clean_output(text: str) -> str:
        if not text:
            return ""
        # Remove training prompts / leaked tags
        patterns = [
            r'\n\s*###\s*Instruction:.*',
            r'\n\s*\[INST\].*',
            r'\n\s*<\|im_start\|>user.*',
            r'\n\s*User Context \(Academic Info.*',
            r'\n\s*\[PROFILE\].*'
        ]
        for pattern in patterns:
            text = re.split(pattern, text, flags=re.IGNORECASE | re.DOTALL)[0]
        text = re.sub(r'^Response:\s*', '', text.strip(), flags=re.IGNORECASE)
        return text.strip()

prompt_service = PromptService()

