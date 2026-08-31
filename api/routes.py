from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.chat_service import chat_service
from services.metrics_service import metrics_service

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
