import pytest
from services.pre_routing import PreRouter, PreRouteResult


@pytest.fixture
def pre_router():
    return PreRouter()


class TestGreetings:
    def test_hola(self, pre_router):
        result = pre_router.evaluate("hola")
        assert result.matched is True
        assert result.match_type == "greeting"
        assert result.escalated is False
        assert "Bienvenido" in result.response

    def test_buenos_dias(self, pre_router):
        result = pre_router.evaluate("buenos días")
        assert result.matched is True
        assert result.match_type == "greeting"

    def test_buenas_tardes(self, pre_router):
        result = pre_router.evaluate("buenas tardes")
        assert result.matched is True
        assert result.match_type == "greeting"

    def test_hello(self, pre_router):
        result = pre_router.evaluate("hello")
        assert result.matched is True
        assert result.match_type == "greeting"

    def test_que_tal(self, pre_router):
        result = pre_router.evaluate("¿qué tal?")
        assert result.matched is True
        assert result.match_type == "greeting"

    def test_saludos(self, pre_router):
        result = pre_router.evaluate("saludos")
        assert result.matched is True
        assert result.match_type == "greeting"


class TestEscalationKeywords:
    def test_problema(self, pre_router):
        result = pre_router.evaluate("tengo un problema con mi horario")
        assert result.matched is True
        assert result.escalated is True
        assert result.match_type == "escalation_keyword"

    def test_hablar_con_asesor(self, pre_router):
        result = pre_router.evaluate("quiero hablar con un asesor")
        assert result.matched is True
        assert result.escalated is True

    def test_soporte(self, pre_router):
        result = pre_router.evaluate("necesito soporte técnico")
        assert result.matched is True
        assert result.escalated is True

    def test_queja(self, pre_router):
        result = pre_router.evaluate("tengo una queja sobre el servicio")
        assert result.matched is True
        assert result.escalated is True

    def test_no_funciona(self, pre_router):
        result = pre_router.evaluate("la plataforma no funciona")
        assert result.matched is True
        assert result.escalated is True

    def test_descuento_especial(self, pre_router):
        result = pre_router.evaluate("¿me pueden dar un descuento especial?")
        assert result.matched is True
        assert result.escalated is True

    def test_urgente(self, pre_router):
        result = pre_router.evaluate("es urgente, necesito ayuda")
        assert result.matched is True
        assert result.escalated is True


class TestFAQPrecios:
    def test_precio_ingles_a1(self, pre_router):
        result = pre_router.evaluate("¿cuánto cuesta el curso de inglés A1?")
        assert result.matched is True
        assert result.match_type == "faq"
        assert "350.000" in result.response

    def test_precio_ingles_b1(self, pre_router):
        result = pre_router.evaluate("precio del curso de inglés B1")
        assert result.matched is True
        assert "450.000" in result.response

    def test_precio_frances_a1(self, pre_router):
        result = pre_router.evaluate("cuánto cuesta el francés A1")
        assert result.matched is True
        assert "400.000" in result.response

    def test_precio_portugues_a1(self, pre_router):
        result = pre_router.evaluate("valor del curso de portugués A1")
        assert result.matched is True
        assert "380.000" in result.response

    def test_precios_generales(self, pre_router):
        result = pre_router.evaluate("¿cuánto cuestan los cursos?")
        assert result.matched is True
        assert "Inglés" in result.response
        assert "Francés" in result.response


class TestFAQHorarios:
    def test_horario_clases(self, pre_router):
        result = pre_router.evaluate("¿cuáles son los horarios de clases?")
        assert result.matched is True
        assert result.match_type == "faq"
        assert "Lun-Mié" in result.response

    def test_horario_atencion(self, pre_router):
        result = pre_router.evaluate("horario de atención general")
        assert result.matched is True
        assert "7:00 a.m." in result.response


class TestFAQModalidades:
    def test_modalidades(self, pre_router):
        result = pre_router.evaluate("¿qué modalidades de clases tienen?")
        assert result.matched is True
        assert "Presencial" in result.response
        assert "Virtual" in result.response
        assert "Híbrida" in result.response

    def test_clase_virtual(self, pre_router):
        result = pre_router.evaluate("¿tienen clases virtuales?")
        assert result.matched is True
        assert "Virtual" in result.response


class TestFAQUbicacion:
    def test_donde_estan(self, pre_router):
        result = pre_router.evaluate("¿dónde están ubicados?")
        assert result.matched is True
        assert "Calle 45" in result.response

    def test_direccion(self, pre_router):
        result = pre_router.evaluate("cuál es la dirección")
        assert result.matched is True
        assert "Bogotá" in result.response


class TestFAQContacto:
    def test_telefono(self, pre_router):
        result = pre_router.evaluate("¿cuál es el teléfono de contacto?")
        assert result.matched is True
        assert "300 123 4567" in result.response

    def test_whatsapp(self, pre_router):
        result = pre_router.evaluate("tienen WhatsApp?")
        assert result.matched is True
        assert "300 123 4567" in result.response


class TestFAQInscripcion:
    def test_como_inscribirse(self, pre_router):
        result = pre_router.evaluate("¿cómo me inscribo?")
        assert result.matched is True
        assert "Documento de identidad" in result.response

    def test_inscripcion(self, pre_router):
        result = pre_router.evaluate("quiero inscribirme")
        assert result.matched is True


class TestFAQCertificaciones:
    def test_certificados(self, pre_router):
        result = pre_router.evaluate("¿qué certificados ofrecen?")
        assert result.matched is True
        assert "Finalización de Nivel" in result.response
        assert "MCER" in result.response


class TestFAQDescuentos:
    def test_descuentos(self, pre_router):
        result = pre_router.evaluate("¿tienen descuentos?")
        assert result.matched is True
        assert "10%" in result.response
        assert "15%" in result.response
        assert "20%" in result.response


class TestFAQPagos:
    def test_formas_de_pago(self, pre_router):
        result = pre_router.evaluate("¿cómo puedo pagar?")
        assert result.matched is True
        assert "Efectivo" in result.response
        assert "Transferencia" in result.response


class TestFAQCupos:
    def test_cupos(self, pre_router):
        result = pre_router.evaluate("hay cupos disponibles?")
        assert result.matched is True
        assert "Inglés" in result.response
        assert "Francés" in result.response


class TestFAQOtros:
    def test_idiomas(self, pre_router):
        result = pre_router.evaluate("¿qué idiomas enseñan?")
        assert result.matched is True
        assert "Inglés" in result.response
        assert "Francés" in result.response
        assert "Portugués" in result.response

    def test_duracion(self, pre_router):
        result = pre_router.evaluate("¿cuál es la duración de los cursos?")
        assert result.matched is True
        assert "meses" in result.response

    def test_prueba_nivel(self, pre_router):
        result = pre_router.evaluate("necesito una prueba de nivel")
        assert result.matched is True
        assert "gratuita" in result.response

    def test_devolucion(self, pre_router):
        result = pre_router.evaluate("¿puedo pedir devolución?")
        assert result.matched is True
        assert result.escalated is True
        assert result.match_type == "escalation_keyword"

    def test_clases_particulares(self, pre_router):
        result = pre_router.evaluate("¿ofrecen clases particulares?")
        assert result.matched is True
        assert "45.000" in result.response

    def test_material(self, pre_router):
        result = pre_router.evaluate("¿el material está incluido?")
        assert result.matched is True
        assert "digital" in result.response


class TestNoMatch:
    def test_complex_question_no_match(self, pre_router):
        result = pre_router.evaluate("¿puedo cambiarme de horario después de inscrito?")
        assert result.matched is False

    def test_random_text(self, pre_router):
        result = pre_router.evaluate("asdfghjkl")
        assert result.matched is False

    def test_empty_string(self, pre_router):
        result = pre_router.evaluate("")
        assert result.matched is False

    def test_whitespace_only(self, pre_router):
        result = pre_router.evaluate("   ")
        assert result.matched is False


class TestEscalationPriority:
    def test_escalation_over_faq(self, pre_router):
        result = pre_router.evaluate("tengo un problema con el precio del curso")
        assert result.matched is True
        assert result.escalated is True
        assert result.match_type == "escalation_keyword"
