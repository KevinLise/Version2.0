from google import genai
from google.genai import types
from config.settings import settings


class LLMClient:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model
        self.embedding_model = settings.gemini_embedding_model

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        context: str = "",
        history: list[dict] | None = None,
    ) -> dict:
        try:
            if context:
                full_user = f"Contexto de la base de conocimiento:\n{context}\n\nPregunta del usuario:\n{user_message}"
            else:
                full_user = user_message

            response = self.client.models.generate_content(
                model=self.model,
                contents=full_user,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=settings.gemini_temperature,
                    max_output_tokens=settings.gemini_max_output_tokens,
                ),
            )

            return {
                "content": response.text or "",
                "finish_reason": "stop",
                "input_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                "model": self.model,
            }

        except Exception as e:
            return {
                "content": "",
                "finish_reason": "error",
                "input_tokens": 0,
                "output_tokens": 0,
                "model": self.model,
                "error": str(e),
            }

    def generate_embedding(self, text: str) -> list[float]:
        result = self.client.models.embed_content(
            model=self.embedding_model,
            contents=text,
        )
        return result.embeddings[0].values


llm_client = LLMClient()
