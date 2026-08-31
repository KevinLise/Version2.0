import logging
from database.sqlite import db

logger = logging.getLogger(__name__)


class EscalationService:
    def _parse_escalation_reason(self, response: str) -> str:
        markers = {
            "[ESCALAR_HUMANO: Información insuficiente en la base de conocimiento]":
                "Información insuficiente en la base de conocimiento.",
            "[ESCALAR_HUMANO: El usuario solicita atención humana]":
                "El usuario solicita atención humana.",
            "[ESCALAR_HUMANO: Solicitud de descuento personalizado]":
                "Solicitud de descuento personalizado.",
            "[ESCALAR_HUMANO: Caso especial no contemplado en la documentación]":
                "Caso especial no contemplado en la documentación.",
            "[ESCALAR_HUMANO: Consulta fuera del alcance del asistente]":
                "Consulta fuera del alcance del asistente.",
        }

        for marker, reason in markers.items():
            if marker in response:
                return reason

        return "Motivo no especificado."

    def is_escalation(self, response: str) -> bool:
        return "[ESCALAR_HUMANO:" in response

    async def log_escalation(
        self,
        user_id: str,
        user_name: str,
        original_message: str,
        reason: str,
        context_retrieved: str = "",
    ) -> None:
        try:
            conn = await db.connect()
            try:
                await conn.execute(
                    """INSERT INTO escalations (user_id, user_name, original_message, reason, context_retrieved)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, user_name, original_message, reason, context_retrieved),
                )
                await conn.commit()
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Failed to log escalation: {e}")

    async def handle_escalation(
        self,
        user_id: str,
        user_name: str,
        original_message: str,
        llm_response: str,
        context_retrieved: str = "",
    ) -> dict:
        reason = self._parse_escalation_reason(llm_response)

        await self.log_escalation(
            user_id=user_id,
            user_name=user_name,
            original_message=original_message,
            reason=reason,
            context_retrieved=context_retrieved,
        )

        logger.info(f"Escalation logged: user={user_id}, reason={reason}")

        return {
            "escalated": True,
            "reason": reason,
        }


escalation_service = EscalationService()
