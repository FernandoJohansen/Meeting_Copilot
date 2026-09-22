from __future__ import annotations

from openai import OpenAI

SYSTEM_PROMPT = (
    "Você é um copiloto de reunião em tempo real. Com base na transcrição recente "
    "(que pode ter pequenos erros de transcrição automática), sugira de 2 a 4 pontos de fala "
    "curtos, objetivos e acionáveis que a pessoa identificada como 'Você' poderia dizer a seguir. "
    "Priorize: perguntas de esclarecimento, riscos ou pontos não abordados, próximos passos e follow-ups. "
    "Responda SOMENTE com uma lista, um ponto por linha, sem numeração e sem markdown, em português do Brasil. "
    "Se não houver contexto suficiente ainda, responda com uma única linha: 'Aguardando mais contexto...'."
)


class SuggestionEngine:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str | None = None) -> None:
        # Ollama exposes an OpenAI-compatible endpoint (http://localhost:11434/v1) that accepts
        # any non-empty api_key value, so the same client works for both backends.
        self.client = OpenAI(api_key=api_key or "local", base_url=base_url)
        self.model = model

    def generate(self, transcript_window: str, meeting_context: str) -> list[str]:
        user_prompt = (
            f"Contexto/agenda da reunião (informado pelo usuário): {meeting_context or 'não informado'}\n\n"
            f"Transcrição recente:\n{transcript_window}\n\n"
            "Sugestões de fala:"
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=300,
        )
        content = response.choices[0].message.content or ""
        return [line.strip(" \t-•") for line in content.splitlines() if line.strip()]
