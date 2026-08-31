from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.chat_service import chat_service
from services.metrics_service import metrics_service
from database.sqlite import db

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    message: str = Field(..., min_length=1, description="User message")
    user_name: str = Field(default="Usuario", description="User display name")
    history: list[dict] | None = Field(default=None, description="Conversation history")


class ChatResponse(BaseModel):
    response: str
    escalated: bool
    cached: bool
    relevance_score: float
    request_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


class HealthResponse(BaseModel):
    status: str


class InscripcionRequest(BaseModel):
    nombre: str = Field(..., min_length=2, description="Nombre completo")
    edad: int = Field(..., ge=5, le=100, description="Edad del estudiante")
    telefono: str = Field(default="", description="Teléfono de contacto")
    email: str = Field(default="", description="Correo electrónico")
    idioma: str = Field(..., description="Idioma de interés (ingles, frances, portugues)")
    nivel: str = Field(default="", description="Nivel deseado (A1, A2, B1, B2, C1)")
    modalidad: str = Field(default="", description="Modalidad (presencial, virtual, hibrida)")
    horario_preferido: str = Field(default="", description="Horario preferido")
    mensaje: str = Field(default="", description="Mensaje adicional")


class InscripcionResponse(BaseModel):
    success: bool
    message: str
    inscripcion_id: int | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = await chat_service.process_message(
        user_id=request.user_id,
        message=request.message,
        user_name=request.user_name,
        history=request.history,
    )

    return ChatResponse(**result)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/metrics")
async def metrics() -> dict:
    return await metrics_service.get_metrics()


@router.post("/inscripcion", response_model=InscripcionResponse)
async def inscripcion(request: InscripcionRequest) -> InscripcionResponse:
    try:
        conn = await db.connect()
        try:
            cursor = await conn.execute(
                """INSERT INTO inscripciones (nombre, edad, telefono, email, idioma, nivel, modalidad, horario_preferido, mensaje)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (request.nombre, request.edad, request.telefono, request.email,
                 request.idioma.lower(), request.nivel.upper(), request.modalidad.lower(),
                 request.horario_preferido, request.mensaje),
            )
            await conn.commit()
            inscripcion_id = cursor.lastrowid
        finally:
            await conn.close()

        return InscripcionResponse(
            success=True,
            message=f"¡Gracias {request.nombre}! Tu inscripción ha sido registrada. Un asesor se comunicará contigo pronto.",
            inscripcion_id=inscripcion_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al registrar inscripción")


@router.get("/inscripciones")
async def listar_inscripciones(estado: str = "pendiente") -> list[dict]:
    try:
        conn = await db.connect()
        try:
            cursor = await conn.execute(
                "SELECT * FROM inscripciones WHERE estado = ? ORDER BY created_at DESC",
                (estado,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener inscripciones")
