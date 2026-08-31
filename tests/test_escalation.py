import pytest
from services.escalation_service import EscalationService


class TestEscalationDetection:
    def setup_method(self):
        self.service = EscalationService()

    def test_detects_insufficient_info(self):
        response = "[ESCALAR_HUMANO: Información insuficiente en la base de conocimiento] Lo siento..."
        assert self.service.is_escalation(response) is True

    def test_detects_human_request(self):
        response = "[ESCALAR_HUMANO: El usuario solicita atención humana]"
        assert self.service.is_escalation(response) is True

    def test_detects_discount_request(self):
        response = "[ESCALAR_HUMANO: Solicitud de descuento personalizado]"
        assert self.service.is_escalation(response) is True

    def test_detects_out_of_scope(self):
        response = "[ESCALAR_HUMANO: Consulta fuera del alcance del asistente]"
        assert self.service.is_escalation(response) is True

    def test_detects_special_case(self):
        response = "[ESCALAR_HUMANO: Caso especial no contemplado en la documentación]"
        assert self.service.is_escalation(response) is True

    def test_normal_response_not_escalation(self):
        response = "El curso de inglés B1 tiene un valor de 450.000 COP."
        assert self.service.is_escalation(response) is False

    def test_empty_response_not_escalation(self):
        assert self.service.is_escalation("") is False


class TestEscalationReasonParsing:
    def setup_method(self):
        self.service = EscalationService()

    def test_parse_insufficient_info(self):
        response = "[ESCALAR_HUMANO: Información insuficiente en la base de conocimiento]"
        reason = self.service._parse_escalation_reason(response)
        assert "insuficiente" in reason.lower()

    def test_parse_human_request(self):
        response = "[ESCALAR_HUMANO: El usuario solicita atención humana]"
        reason = self.service._parse_escalation_reason(response)
        assert "humana" in reason.lower() or "humano" in reason.lower()

    def test_parse_discount(self):
        response = "[ESCALAR_HUMANO: Solicitud de descuento personalizado]"
        reason = self.service._parse_escalation_reason(response)
        assert "descuento" in reason.lower()

    def test_parse_out_of_scope(self):
        response = "[ESCALAR_HUMANO: Consulta fuera del alcance del asistente]"
        reason = self.service._parse_escalation_reason(response)
        assert "alcance" in reason.lower()

    def test_parse_unknown_marker(self):
        response = "[ESCALAR_HUMANO: Some unknown reason]"
        reason = self.service._parse_escalation_reason(response)
        assert reason == "Motivo no especificado."
