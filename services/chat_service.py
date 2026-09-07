import time
import uuid
import logging
from config.settings import settings
from rag.retriever import retriever
from rag.reranker import reranker
from rag.scoring import normalize_relevance_score, is_above_threshold
from llm.client import llm_client
from llm.prompts import SYSTEM_PROMPT
from services.cache_service import cache_service
from services.escalation_service import escalation_service
from services.metrics_service import metrics_service
from services.pre_routing import pre_router
from services.user_memory import user_memory

logger = logging.getLogger(__name__)


class ChatService:
    async def process_message(
        self,
        user_id: str,
        message: str,
        user_name: str = "Usuario",
        history: list[dict] | None = None,
    ) -> dict:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        logger.info(
            f"[{request_id}] Processing message from user {user_id}: {message[:80]}..."
        )

        # USER MEMORY: extraer info del usuario y actualizar perfil
        extracted_info = user_memory.extract_user_info(message)
        if extracted_info:
            user_memory.update_user(user_id, **extracted_info)
            logger.info(f"[{request_id}] User info extracted: {extracted_info}")

        # actualizar nombre si se proporciona
        if user_name and user_name != "Usuario":
            user_memory.update_user(user_id, name=user_name)

        user_memory.increment_query_count(user_id)
        user_context = user_memory.get_context_for_user(user_id)
        if user_context:
            logger.info(f"[{request_id}] {user_context}")

        cached = await cache_service.get(message)
        if cached:
            response_time = (time.time() - start_time) * 1000
            await metrics_service.record_query(
                user_id=user_id,
                request_id=request_id,
                relevance_score=cached.get("relevance_score"),
                cache_hit=True,
                llm_called=False,
                escalated=False,
                response_time_ms=response_time,
            )
            logger.info(f"[{request_id}] Cache hit, returning cached response")
            return {
                "response": cached["response"],
                "escalated": False,
                "cached": True,
                "relevance_score": cached.get("relevance_score"),
                "request_id": request_id,
                "input_tokens": 0,
                "output_tokens": 0,
                "model": "cache",
            }

        await metrics_service.record_query(
            user_id=user_id,
            request_id=request_id,
            cache_hit=False,
        )

        # CAPA 1: Pre-routing - respuestas predeterminadas y escalamiento directo
        pre_route = pre_router.evaluate(message)

        if pre_route.matched:
            response_time = (time.time() - start_time) * 1000

            # Escalamiento directo por keyword
            if pre_route.escalated:
                escalation_result = await escalation_service.handle_escalation(
                    user_id=user_id,
                    user_name=user_name,
                    original_message=message,
                    llm_response=f"[ESCALAR_HUMANO: {pre_route.escalation_reason}]",
                    context_retrieved="",
                )
                await metrics_service.record_query(
                    user_id=user_id,
                    request_id=request_id,
                    relevance_score=1.0,
                    escalated=True,
                    response_time_ms=response_time,
                )
                logger.info(f"[{request_id}] Pre-routing: escalation - {pre_route.escalation_reason}")
                return {
                    "response": "Un representante de soporte te contactará pronto para ayudarte con tu consulta.",
                    "escalated": True,
                    "cached": False,
                    "relevance_score": 1.0,
                    "request_id": request_id,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "model": "pre_routing",
                }

            # Respuesta predeterminada (greeting o FAQ)
            await cache_service.set(
                query=message,
                response=pre_route.response,
                relevance_score=1.0,
            )
            await metrics_service.record_query(
                user_id=user_id,
                request_id=request_id,
                relevance_score=1.0,
                cache_hit=False,
                llm_called=False,
                escalated=False,
                response_time_ms=response_time,
            )
            logger.info(f"[{request_id}] Pre-routing: {pre_route.match_type} - responded without LLM")
            return {
                "response": pre_route.response,
                "escalated": False,
                "cached": False,
                "relevance_score": 1.0,
                "request_id": request_id,
                "input_tokens": 0,
                "output_tokens": 0,
                "model": "pre_routing",
            }

        # CAPA 2 y 3: RAG + LLM (flujo original)
        try:
            candidates = await retriever.retrieve(message, top_k=settings.top_k)
        except Exception as e:
            logger.error(f"[{request_id}] Retrieval failed: {e}")
            response_time = (time.time() - start_time) * 1000
            await metrics_service.record_query(
                user_id=user_id,
                request_id=request_id,
                response_time_ms=response_time,
            )
            return {
                "response": "Lo siento, hubo un error al procesar tu consulta. Por favor, intenta de nuevo.",
                "escalated": False,
                "cached": False,
                "relevance_score": 0.0,
                "request_id": request_id,
                "input_tokens": 0,
                "output_tokens": 0,
                "model": "",
            }

        if not candidates:
            response_time = (time.time() - start_time) * 1000
            await metrics_service.record_query(
                user_id=user_id,
                request_id=request_id,
                relevance_score=0.0,
                response_time_ms=response_time,
            )
            return {
                "response": "Soy AcademiaBot, el asistente virtual de la Academia de Idiomas. Puedo ayudarte con información sobre nuestros cursos, horarios, precios e inscripciones. ¿En qué puedo ayudarte?",
                "escalated": False,
                "cached": False,
                "relevance_score": 0.0,
                "request_id": request_id,
                "input_tokens": 0,
                "output_tokens": 0,
                "model": "pre_routing",
            }

        reranked = await reranker.rerank(message, candidates)
        best_score = normalize_relevance_score(reranked[0]["rerank_score"])

        if not is_above_threshold(best_score, settings.rag_score_threshold):
            response_time = (time.time() - start_time) * 1000
            await metrics_service.record_query(
                user_id=user_id,
                request_id=request_id,
                relevance_score=best_score,
                response_time_ms=response_time,
            )
            return {
                "response": "Soy AcademiaBot, el asistente virtual de la Academia de Idiomas. No encontré información exacta sobre eso, pero puedo ayudarte con:\n\n• Precios de cursos de inglés, francés y portugués\n• Horarios de las clases\n• Inscripciones y requisitos\n• Certificaciones\n• Formas de pago y descuentos\n• Ubicación y contacto\n\n¿Qué te gustaría saber?",
                "escalated": False,
                "cached": False,
                "relevance_score": best_score,
                "request_id": request_id,
                "input_tokens": 0,
                "output_tokens": 0,
                "model": "pre_routing",
            }

        context_chunks = [d["text"] for d in reranked if d["rerank_score"] > 0.1]
        if not context_chunks:
            context_chunks = [d["text"] for d in reranked[:3]]

        context_text = "\n\n".join(context_chunks)
        logger.info(f"[{request_id}] Context chunks: {len(context_chunks)}, rerank_scores: {[f'{d['rerank_score']:.3f}' for d in reranked[:3]]}")
        logger.info(f"[{request_id}] Context preview: {context_text[:300]}")

        truncated_history = None
        if history:
            truncated_history = history[-settings.max_history_messages:]

        # inyectar perfil del usuario en el contexto
        full_context = context_text
        if user_context:
            full_context = f"{user_context}\n\n{context_text}"

        llm_response = await llm_client.generate_response(
            system_prompt=SYSTEM_PROMPT,
            user_message=message,
            context=full_context,
            history=truncated_history,
        )

        response_text = llm_response.get("content", "")
        input_tokens = llm_response.get("input_tokens", 0)
        output_tokens = llm_response.get("output_tokens", 0)
        model_name = llm_response.get("model", "")
        logger.info(f"[{request_id}] LLM response: {response_text[:200]}")

        if not response_text or llm_response.get("error"):
            logger.error(f"[{request_id}] LLM error: {llm_response.get('error', 'Empty response')}")
            response_time = (time.time() - start_time) * 1000
            return {
                "response": "Lo siento, hubo un error al generar la respuesta. Por favor, intenta de nuevo.",
                "escalated": False,
                "cached": False,
                "relevance_score": best_score,
                "request_id": request_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model_name,
            }

        if escalation_service.is_escalation(response_text):
            context_for_escalation = "\n\n".join([d["text"] for d in reranked[:3]])
            escalation_result = await escalation_service.handle_escalation(
                user_id=user_id,
                user_name=user_name,
                original_message=message,
                llm_response=response_text,
                context_retrieved=context_for_escalation,
            )
            response_time = (time.time() - start_time) * 1000
            await metrics_service.record_query(
                user_id=user_id,
                request_id=request_id,
                relevance_score=best_score,
                llm_called=True,
                escalated=True,
                response_time_ms=response_time,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            return {
                "response": "Un representante de soporte te contactará pronto para ayudarte con tu consulta.",
                "escalated": True,
                "cached": False,
                "relevance_score": best_score,
                "request_id": request_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model_name,
            }

        await cache_service.set(
            query=message,
            response=response_text,
            relevance_score=best_score,
        )

        response_time = (time.time() - start_time) * 1000
        await metrics_service.record_query(
            user_id=user_id,
            request_id=request_id,
            relevance_score=best_score,
            llm_called=True,
            escalated=False,
            response_time_ms=response_time,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        logger.info(
            f"[{request_id}] Response generated. Score: {best_score:.2f}, "
            f"Tokens: {input_tokens}/{output_tokens}, Time: {response_time:.0f}ms"
        )

        return {
            "response": response_text,
            "escalated": False,
            "cached": False,
            "relevance_score": best_score,
            "request_id": request_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model": model_name,
        }


chat_service = ChatService()
