import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PreRouteResult:
    matched: bool
    response: str | None = None
    escalated: bool = False
    escalation_reason: str | None = None
    match_type: str | None = None  # "greeting", "faq", "escalation_keyword"


class PreRouter:
    def __init__(self):
        self._init_greetings()
        self._init_faq_responses()
        self._init_escalation_keywords()

    def _init_greetings(self) -> None:
        self.greeting_patterns = [
            r"\b(hola|hello|hi|hey|buenas)\b",
            r"\b(buenos\s*d[ií]as)\b",
            r"\b(buenas\s*tardes)\b",
            r"\b(buenas\s*noches)\b",
            r"\b(qu[eé]\s*tal|que tal|quetale)\b",
            r"\b(c[oó]mo\s*est[aá]s|como estas)\b",
            r"\b(saludos)\b",
            r"\b(hey+)\b",
        ]
        self.greeting_response = (
            "¡Hola! 👋 Bienvenido a la Academia de Idiomas. "
            "¿En qué puedo ayudarte hoy?\n\n"
            "Puedo ayudarte con:\n"
            "• Precios de cursos\n"
            "• Horarios y modalidades\n"
            "• Información sobre inscripciones\n"
            "• Certificaciones\n"
            "• Disponibilidad de cupos\n\n"
            "Escribe tu pregunta y con gusto te ayudo."
        )

    def _init_faq_responses(self) -> None:
        self.faq_responses: dict[str, str] = {
            # --- QUIEN ES / IDENTIDAD ---
            r"(?i)(qui[eé]n\s*eres|c[oó]mo\s*te\s*llamas|eres\s*(un\s*)?bot|eres\s*ia|quien\s*soy\s*tu)":
                "¡Hola! Soy **Academia Bot**, el asistente virtual de la Academia de Idiomas. "
                "Estoy aquí para ayudarte con información sobre nuestros cursos, horarios, precios e inscripciones.",

            # --- PRECIOS INGLÉS ---
            r"(?i)(cu[aá]nto|precio|costo|valor).*(ingles|ingl[eé]s).*(a1|principiante|basico|b[aá]sico)":
                "El curso de inglés nivel A1 (Principiante) tiene un valor de **$350.000 COP**. "
                "Duración: 2 meses (32 horas). No se requiere experiencia previa.",

            r"(?i)(cu[aá]nto|precio|costo|valor).*(ingles|ingl[eé]s).*(a2|elemental)":
                "El curso de inglés nivel A2 (Elemental) tiene un valor de **$380.000 COP**. "
                "Duración: 2 meses (32 horas). Requisito: haber completado A1 o equivalente.",

            r"(?i)(cu[aá]nto|precio|costo|valor).*(ingles|ingl[eé]s).*(b1|intermedio\s*bajo)":
                "El curso de inglés nivel B1 (Intermedio Bajo) tiene un valor de **$450.000 COP**. "
                "Duración: 2.5 meses (40 horas). Requisito: haber completado A2 o equivalente.",

            r"(?i)(cu[aá]nto|precio|costo|valor).*(ingles|ingl[eé]s).*(b2|intermedio\s*alto)":
                "El curso de inglés nivel B2 (Intermedio Alto) tiene un valor de **$500.000 COP**. "
                "Duración: 3 meses (48 horas). Requisito: haber completado B1 o equivalente.",

            r"(?i)(cu[aá]nto|precio|costo|valor).*(ingles|ingl[eé]s).*(c1|avanzado)":
                "El curso de inglés nivel C1 (Avanzado) tiene un valor de **$550.000 COP**. "
                "Duración: 3 meses (48 horas). Requisito: haber completado B2 o equivalente.",

            # --- PRECIOS FRANCÉS ---
            r"(?i)(cu[aá]nto|precio|costo|valor).*(franc[eé]s|frances).*(a1|principiante)":
                "El curso de francés nivel A1 (Principiante) tiene un valor de **$400.000 COP**. "
                "Duración: 2 meses (32 horas). No se requiere experiencia previa.",

            r"(?i)(cu[aá]nto|precio|costo|valor).*(franc[eé]s|frances).*(a2|elemental)":
                "El curso de francés nivel A2 (Elemental) tiene un valor de **$430.000 COP**. "
                "Duración: 2 meses (32 horas). Requisito: haber completado A1 o equivalente.",

            r"(?i)(cu[aá]nto|precio|costo|valor).*(franc[eé]s|frances).*(b1|intermedio)":
                "El curso de francés nivel B1 (Intermedio) tiene un valor de **$500.000 COP**. "
                "Duración: 2.5 meses (40 horas). Requisito: haber completado A2 o equivalente.",

            # --- PRECIOS PORTUGUÉS ---
            r"(?i)(cu[aá]nto|precio|costo|valor).*(portugu[eé]s|portugues).*(a1|principiante)":
                "El curso de portugués nivel A1 (Principiante) tiene un valor de **$380.000 COP**. "
                "Duración: 2 meses (32 horas). No se requiere experiencia previa.",

            r"(?i)(cu[aá]nto|precio|costo|valor).*(portugu[eé]s|portugues).*(a2|elemental)":
                "El curso de portugués nivel A2 (Elemental) tiene un valor de **$420.000 COP**. "
                "Duración: 2 meses (32 horas). Requisito: haber completado A1 o equivalente.",

            # --- PRECIOS GENERALES ---
            r"(?i)(cu[aá]nto|precio|costo|valor).*(curso|clase)":
                "Nuestros precios varían según el idioma y nivel:\n\n"
                "**Inglés**: desde $350.000 COP (A1) hasta $550.000 COP (C1)\n"
                "**Francés**: desde $400.000 COP (A1) hasta $500.000 COP (B1)\n"
                "**Portugués**: desde $380.000 COP (A1) hasta $420.000 COP (A2)\n\n"
                "¿Te interesa algún idioma o nivel en particular?",

            # --- HORARIOS ---
            r"(?i)(horario|horarios|hora|cu[aá]ndo|dia|d[ií]a).*(clase|curso)":
                "Nuestros horarios son:\n\n"
                "**Inglés A1**: Lun-Mié 6-8pm | Mar-Jue 10am-12pm | Sáb 8-10am\n"
                "**Inglés A2**: Lun-Mié 8-10pm | Mar-Jue 6-8pm | Sáb 10am-12pm\n"
                "**Inglés B1**: Lun-Mié 6-8pm | Mar-Jue 8-10pm | Sáb 8-10am\n"
                "**Francés A1**: Mar-Jue 6-8pm | Sáb 10am-12pm\n"
                "**Portugués A1**: Mié-Vie 6-8pm | Sáb 8-10am\n\n"
                "¿Te interesa algún horario en específico?",

            r"(?i)(horario|horarios|a\s*qu[eé]\s*hora|cu[aá]ndo\s*(dan|es|hay))":
                "Nuestros horarios son:\n\n"
                "**Inglés A1**: Lun-Mié 6-8pm | Mar-Jue 10am-12pm | Sáb 8-10am\n"
                "**Inglés A2**: Lun-Mié 8-10pm | Mar-Jue 6-8pm | Sáb 10am-12pm\n"
                "**Inglés B1**: Lun-Mié 6-8pm | Mar-Jue 8-10pm | Sáb 8-10am\n"
                "**Inglés B2**: Lun-Mié 8-10pm | Mar-Jue 6-8pm | Sáb 10am-12pm\n"
                "**Francés A1**: Mar-Jue 6-8pm | Sáb 10am-12pm\n"
                "**Portugués A1**: Mié-Vie 6-8pm | Sáb 8-10am\n\n"
                "¿Te interesa algún idioma o nivel en particular?",

            r"(?i)(que\s*horario|horario\s*de|horarios\s*de|a\s*que\s*horas)":
                "Nuestros horarios son:\n\n"
                "**Inglés A1**: Lun-Mié 6-8pm | Mar-Jue 10am-12pm | Sáb 8-10am\n"
                "**Inglés A2**: Lun-Mié 8-10pm | Mar-Jue 6-8pm | Sáb 10am-12pm\n"
                "**Inglés B1**: Lun-Mié 6-8pm | Mar-Jue 8-10pm | Sáb 8-10am\n"
                "**Inglés B2**: Lun-Mié 8-10pm | Mar-Jue 6-8pm | Sáb 10am-12pm\n"
                "**Francés A1**: Mar-Jue 6-8pm | Sáb 10am-12pm\n"
                "**Portugués A1**: Mié-Vie 6-8pm | Sáb 8-10am\n\n"
                "¿Te interesa algún idioma o nivel en particular?",

            r"(?i)(horario|horarios).*(atenci[oó]n|general|academia)":
                "Nuestro horario de atención es:\n"
                "• Lunes a viernes: 7:00 a.m. a 9:00 p.m.\n"
                "• Sábados: 8:00 a.m. a 2:00 p.m.\n\n"
                "¿En qué puedo ayudarte?",

            # --- MODALIDADES ---
            r"(?i)(modalidad|modalidades|tipo|tipos).*(clase|clases|curso)":
                "Ofrecemos tres modalidades:\n\n"
                "**1. Presencial**: Calle 45 #7-32, Oficina 501, Bogotá. Máximo 12 estudiantes por grupo.\n\n"
                "**2. Virtual**: Por Zoom o Google Meet. Horarios flexibles mañana, tarde y noche. Material digital incluido.\n\n"
                "**3. Híbrida**: Combina presencial y virtual. Tú eliges qué clases asistir de cada forma.\n\n"
                "¿Cuál modalidad te interesa?",

            r"(?i)(virtual|en\s*l[ií]nea|online|presencial|h[ií]brido|h[ií]brida)":
                "Tenemos tres modalidades disponibles:\n\n"
                "• **Presencial**: Calle 45 #7-32, Oficina 501, Bogotá\n"
                "• **Virtual**: Zoom o Google Meet, horarios flexibles\n"
                "• **Híbrida**: Combina ambas a tu conveniencia\n\n"
                "¿Te gustaría más información sobre alguna?",

            # --- UBICACIÓN ---
            r"(?i)(ubicaci[oó]n|direcci[oó]n|d[oó]nde|local|sede|est[aá]n)":
                "Estamos ubicados en:\n"
                "📍 **Calle 45 #7-32, Oficina 501, Bogotá, Colombia**\n\n"
                "Horario de atención:\n"
                "• Lunes a viernes: 7:00 a.m. a 9:00 p.m.\n"
                "• Sábados: 8:00 a.m. a 2:00 p.m.",

            # --- CONTACTO ---
            r"(?i)(tel[eé]fono|contacto|contactar|whatsapp|correo|email|n[uú]mero)":
                "Puedes contactarnos por:\n"
                "📞 Teléfono: +57 300 123 4567\n"
                "💬 WhatsApp: +57 300 123 4567\n"
                "📧 Correo: info@academiaidiomas.com\n\n"
                "Horario de atención telefónica: Lunes a viernes de 8:00 a.m. a 6:00 p.m.",

            # --- INSCRIPCIÓN ---
            r"(?i)(inscrib|inscripci[oó]n|matricul|registro|c[oó]mo\s*me\s*inscribo|formulario)":
                "Para inscribirte necesitas:\n"
                "1. Documento de identidad vigente\n"
                "2. Comprobante de pago o primera cuota\n"
                "3. Foto tamaño carnet\n\n"
                "📄 **Completa tu inscripción aquí:**\n"
                "🔗 http://localhost:8000/inscripcion\n\n"
                "El proceso es:\n"
                "1. Diligencia el formulario\n"
                "2. Un asesor te contactará para confirmar\n"
                "3. Realiza el pago\n"
                "4. ¡Inicio de clases!\n\n"
                "¿Quieres que te ayude a elegir un curso?",

            # --- CERTIFICACIONES ---
            r"(?i)(certificaci[oó]n|certificado|diploma|t[ií]tulo)":
                "Ofrecemos tres tipos de certificación:\n\n"
                "**1. Certificado de Finalización de Nivel**\n"
                "• Incluido en el valor del curso\n"
                "• Vigencia indefinida\n\n"
                "**2. Certificado de Nivel MCER (Marco Europeo)**\n"
                "• A1, A2, B1, B2, C1, C2\n"
                "• Requiere examen final (mínimo 4.0/5.0)\n"
                "• Costo: $50.000 COP adicionales\n"
                "• Entrega: 15 días hábiles\n\n"
                "**3. Diploma de Competencia Lingüística**\n"
                "• Para niveles B2 y C1\n"
                "• Competencia académica y profesional\n\n"
                "¿Sobre cuál quieres más información?",

            # --- DESCUENTOS ---
            r"(?i)(descuento|promoci[oó]n|oferta|rebaja)":
                "Tenemos estas promociones disponibles:\n\n"
                "💰 **Pago anticipado**: 10% de descuento pagando el curso completo antes del inicio\n"
                "👨‍👩‍👧 **Hermanos**: 15% de descuento para el segundo miembro de la familia\n"
                "🏢 **Vinculación laboral**: 20% para empleados de empresas aliadas\n\n"
                "No ofrecemos descuentos personalizados fuera de estas promociones.\n\n"
                "¿Aplicas para alguna de estas?",

            # --- FORMAS DE PAGO ---
            r"(?i)(pago|pagar|forma\s*de\s*pago|m[eé]todo|transferencia|efectivo|tarjeta)":
                "Aceptamos las siguientes formas de pago:\n"
                "• Efectivo\n"
                "• Transferencia bancaria (Bancolombia, Davivienda, Nequi, Daviplata)\n"
                "• Tarjeta de crédito o débito\n\n"
                "También ofrecemos pago en cuotas (máximo 3 cuotas sin interés).",

            # --- CUPOS ---
            r"(?i)(cupo|cupos|disponibilidad|hay\s*lugar|quedan\s*lugares)":
                "Disponibilidad actual de cupos:\n\n"
                "✅ **Inglés**: Todos los niveles con cupos disponibles\n"
                "✅ **Francés**: A1 y A2 con cupos. B1 con cupos limitados\n"
                "✅ **Portugués**: A1 y A2 con cupos disponibles\n\n"
                "📝 Inscripción abierta todo el año\n"
                "📅 Los cursos inician el primer lunes de cada mes\n\n"
                "¿Te gustaría inscribirte en algún curso?",

            # --- PRUEBA DE NIVEL ---
            r"(?i)(prueba\s*de\s*nivel|test\s*de\s*nivel|nivel|qu[eé]\s*nivel|qu[eé]\s*curso)":
                "Si ya tienes conocimientos previos del idioma, ofrecemos una **prueba de nivel gratuita** "
                "para determinar en qué nivel debes inscribirte.\n\n"
                "Si eres principiante, puedes empezar directamente en el nivel A1.\n\n"
                "¿Quieres agendar una prueba de nivel?",

            # --- DEVOLUCIONES ---
            r"(?i)(devoluci[oó]n|devolver|reembolso|dinero|cancelar)":
                "Nuestra política de devolución es:\n\n"
                "• **Antes del inicio de clases**: 100% de devolución\n"
                "• **Durante la primera semana**: 80% de devolución\n"
                "• **Después de la primera semana**: No se realizan devoluciones\n\n"
                "Las devoluciones se procesan en máximo 15 días hábiles.",

            # --- ASISTENCIA ---
            r"(?i)(asistencia|inasistencia|falta|faltar|ausencia)":
                "Nuestra política de asistencia:\n\n"
                "• Máximo 3 inasistencias por curso\n"
                "• A partir de la 4ta falta, se puede perder el cupo\n"
                "• Faltas justificadas (certificado médico) no se contabilizan\n"
                "• Puedes solicitar suspensión por máximo 1 mes en caso de ausencia prolongada",

            # --- CLASES PARTICULARES ---
            r"(?i)(particular|privada|privado|individual|uno\s*a\s*uno)":
                "Sí, ofrecemos clases particulares:\n\n"
                "💰 Costo: **$45.000 COP por hora**\n\n"
                "Las clases se agendan según disponibilidad del profesor y del estudiante.\n\n"
                "¿Te gustaría agendar una clase particular?",

            # --- MATERIAL ---
            r"(?i)(material|libro|texto|apuntes|fotocopias)":
                "El material de estudio está incluido en formato digital.\n\n"
                "Si deseas material impreso, tiene un costo adicional de **$25.000 COP**.\n\n"
                "¿Necesitas más información sobre el material?",

            # --- NIVELES ESPECÍFICOS ---
            r"(?i)(para|quiero|necesito|informaci[oó]n).*(a1|a2|b1|b2|c1|principiante|elemental|intermedio|avanzado)":
                "¡Claro! Aquí tienes información de ese nivel:\n\n"
                "**Inglés A1** (Principiante): $350.000 COP | 2 meses | 32 horas\n"
                "**Inglés A2** (Elemental): $380.000 COP | 2 meses | 32 horas\n"
                "**Inglés B1** (Intermedio Bajo): $450.000 COP | 2.5 meses | 40 horas\n"
                "**Inglés B2** (Intermedio Alto): $500.000 COP | 3 meses | 48 horas\n"
                "**Inglés C1** (Avanzado): $550.000 COP | 3 meses | 48 horas\n\n"
                "**Francés A1**: $400.000 COP | 2 meses | 32 horas\n"
                "**Francés A2**: $430.000 COP | 2 meses | 32 horas\n"
                "**Francés B1**: $500.000 COP | 2.5 meses | 40 horas\n\n"
                "**Portugués A1**: $380.000 COP | 2 meses | 32 horas\n"
                "**Portugués A2**: $420.000 COP | 2 meses | 32 horas\n\n"
                "¿Qué nivel o idioma te interesa?",

            # --- QUÉ QUIERES / QUÉ BUSCAS ---
            r"(?i)(qu[eé]\s*quiero|qu[eé]\s*busco|qu[eé]\s*necesito|ayudame|ayuda)":
                "Soy AcademiaBot, tu asistente virtual. Puedo ayudarte con:\n\n"
                "• 💰 **Precios** de cursos de inglés, francés y portugués\n"
                "• 🕐 **Horarios** de las clases\n"
                "• 📝 **Inscripciones** y requisitos\n"
                "• 🎓 **Certificaciones** que ofrecemos\n"
                "• 💳 **Formas de pago** y descuentos\n"
                "• 📍 **Ubicación** y contacto\n"
                "• 📚 **Idiomas** disponibles\n\n"
                "Escribe tu pregunta y con gusto te ayudo.",

            # --- IDIOMAS DISPONIBLES ---
            r"(?i)(qu[eé]\s*idioma|idiomas|ense[nñ]an|imparten|ofrecen)":
                "En nuestra academia ofrecemos:\n\n"
                "🇬🇧 **Inglés** - Niveles A1 a C1\n"
                "🇫🇷 **Francés** - Niveles A1 a B1\n"
                "🇧🇷 **Portugués** - Niveles A1 a A2\n\n"
                "¿Cuál idioma te interesa?",

            # --- DURACIÓN ---
            r"(?i)(duraci[oó]n|cu[aá]nto\s*dura|tiempo|meses)":
                "La duración de los cursos varía:\n\n"
                "**Inglés**: A1-A2 (2 meses) | B1 (2.5 meses) | B2-C1 (3 meses)\n"
                "**Francés**: A1-A2 (2 meses) | B1 (2.5 meses)\n"
                "**Portugués**: A1-A2 (2 meses)\n\n"
                "Todos los cursos incluyen entre 32 y 48 horas de formación.",

            # --- FORMULARIO DIRECTO ---
            r"(?i)(formulario|form|formato|hoja\s*de\s*inscripci[oó]n)":
                "📄 **Formulario de inscripción**\n\n"
                "Completa tu inscripción aquí:\n"
                "🔗 http://localhost:8000/inscripcion\n\n"
                "O si prefieres, dime tu nombre, edad e idioma de interés y te registro directamente.\n\n"
                "¿Necesitas ayuda con algo más?",
        }

    def _init_escalation_keywords(self) -> None:
        self.escalation_rules: list[tuple[str, str]] = [
            # Problemas técnicos / quejas
            (r"(?i)\b(problema|problemas|inconveniente|inconvenientes|error|errores)\b",
             "El usuario reporta un problema"),
            (r"(?i)\b(queja|quejas|reclamo|reclamos|insatisfecho|insatisfecha|molesto|molesta)\b",
             "Queja o reclamo del usuario"),
            (r"(?i)\b(no\s*funciona|no\s*sirve|no\s*me\s*deja|falla|fallando)\b",
             "Reporte de fallo"),

            # Solicitud explícita de humano/soporte
            (r"(?i)\b(hablar\s*con\s*(un\s*)?(asesor|agente|persona|humano|representante|alguien))\b",
             "Solicitud de atención humana"),
            (r"(?i)\b(asesor|agente|representante|soporte|atenci[oó]n\s*al\s*cliente)\b",
             "Solicitud de asesor o soporte"),
            (r"(?i)\b(necesito\s*ayuda\s*humana|quiero\s*hablar|puedo\s*hablar)\b",
             "Solicitud de atención humana"),
            (r"(?i)\b(ll[aá]menme|llamar|llamada|tel[eé]fono\s*de\s*soporte)\b",
             "Solicitud de llamada"),

            # Casos especiales
            (r"(?i)\b(descuento\s*especial|descuento\s*personalizado|me\s*pueden\s*descuentar)\b",
             "Solicitud de descuento personalizado"),
            (r"(?i)\b(urgente|urgencia|emergencia|emergencias)\b",
             "Situación urgente"),
            (r"(?i)\b(queja\s*formal|denuncia|demanda)\b",
             "Queja formal"),

            # Problemas específicos de horario/grupo
            (r"(?i)\b(problema\s*con\s*(mi\s*)?horario|cambiar\s*de\s*grupo|cambio\s*de\s*horario)\b",
             "Problema o cambio de horario/grupo"),
            (r"(?i)\b(devoluci[oó]n|reembolso|devolver\s*dinero)\b",
             "Solicitud de devolución"),
        ]

    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\sáéíóúñü]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def check_greeting(self, message: str) -> bool:
        normalized = self._normalize(message)
        for pattern in self.greeting_patterns:
            if re.search(pattern, normalized):
                return True
        return False

    def check_escalation_keywords(self, message: str) -> tuple[bool, str | None]:
        for pattern, reason in self.escalation_rules:
            if re.search(pattern, message):
                return True, reason
        return False, None

    def check_faq(self, message: str) -> str | None:
        for pattern, response in self.faq_responses.items():
            if re.search(pattern, message):
                return response
        return None

    def evaluate(self, message: str) -> PreRouteResult:
        if not message or not message.strip():
            return PreRouteResult(matched=False)

        # 1. Check escalation keywords first (highest priority)
        is_escalation, reason = self.check_escalation_keywords(message)
        if is_escalation:
            logger.info(f"Pre-routing: escalation keyword detected - {reason}")
            return PreRouteResult(
                matched=True,
                response=None,
                escalated=True,
                escalation_reason=reason,
                match_type="escalation_keyword",
            )

        # 2. Check greetings
        if self.check_greeting(message):
            logger.info("Pre-routing: greeting detected")
            return PreRouteResult(
                matched=True,
                response=self.greeting_response,
                escalated=False,
                match_type="greeting",
            )

        # 3. Check FAQ responses
        faq_response = self.check_faq(message)
        if faq_response:
            logger.info("Pre-routing: FAQ match found")
            return PreRouteResult(
                matched=True,
                response=faq_response,
                escalated=False,
                match_type="faq",
            )

        # 4. No match - proceed to RAG
        return PreRouteResult(matched=False)


pre_router = PreRouter()
