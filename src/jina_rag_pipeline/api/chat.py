"""Chat API endpoints with WebSocket support."""

import asyncio
import json
import logging
import re
import time
from typing import Dict, Any
from urllib.parse import quote

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse

from .models import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionInfo,
    ChatConfig,
    ContextMessage,
    CompleteMessage,
)
from .session import SessionManager, Session
from ..generation import QwenGenerator, GenerationConfig, RAGConfig, ContextFormatter, get_system_prompt
from ..embeddings import JinaEmbeddingsV4
from ..embeddings.config import EmbeddingConfig
from ..storage import ChromaVectorStore
from ..retrieval import JinaReranker, RetrievalMetrics

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_TEXT_RESULTS = 5
DEFAULT_IMAGE_RESULTS = 3
DEFAULT_RETRIEVAL_BATCH_SIZE = 10


def safe_filename(path: str) -> str:
    """
    Extract safe filename from path, preventing path traversal attacks.

    Args:
        path: File path that may contain directory traversal attempts

    Returns:
        Safe filename with path traversal characters removed

    Examples:
        >>> safe_filename("../../etc/passwd")
        'passwd'
        >>> safe_filename("foo/../bar.txt")
        'bar.txt'
        >>> safe_filename("")
        ''
    """
    if not path:
        return ""

    # Extract basename (last component after /)
    filename = path.split('/')[-1]

    # Remove any remaining path traversal patterns
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")

    # Remove any null bytes or control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)

    return filename


def build_safe_image_url(base_path: str, collection_name: str, image_path: str) -> str:
    """
    Build a safe image URL with proper encoding and path traversal prevention.

    Args:
        base_path: Base URL path (e.g., "/api/images/thumbnail")
        collection_name: Collection name
        image_path: Image file path

    Returns:
        Safely constructed URL, or empty string if inputs are invalid
    """
    filename = safe_filename(image_path)
    if not filename or not collection_name:
        return ""

    # URL encode both collection name and filename
    safe_collection = quote(collection_name, safe='')
    safe_file = quote(filename, safe='')

    return f"{base_path}/{safe_collection}/{safe_file}"

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatState:
    """Global chat state."""

    def __init__(self):
        self.session_manager: SessionManager = SessionManager()
        self.generator: QwenGenerator | None = None
        self.embedder: JinaEmbeddingsV4 | None = None
        self.vector_store: ChromaVectorStore | None = None
        self.context_formatter: ContextFormatter = ContextFormatter()
        self.reranker: JinaReranker | None = None
        self.rag_config: RAGConfig = RAGConfig()  # Default RAG configuration


# Global state instance
chat_state = ChatState()


def get_chat_state() -> ChatState:
    """Dependency to get chat state."""
    return chat_state


@router.post("/session", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest, state: ChatState = Depends(get_chat_state)
) -> CreateSessionResponse:
    """
    Create a new chat session.

    Args:
        request: Session creation request
        state: Chat state

    Returns:
        Created session information
    """
    # Convert ChatConfig to GenerationConfig
    gen_config = GenerationConfig()
    if request.config:
        if request.config.enable_thinking:
            gen_config = GenerationConfig.for_thinking_mode(
                max_tokens=request.config.max_tokens,
                temperature=request.config.temperature,
            )
        else:
            gen_config = GenerationConfig.for_non_thinking_mode(
                max_tokens=request.config.max_tokens,
                temperature=request.config.temperature,
            )

    session = state.session_manager.create_session(request.collection_name, gen_config)

    session_info = SessionInfo(
        session_id=session.session_id,
        collection_name=session.collection_name,
        created_at=session.created_at.isoformat(),
        last_accessed=session.last_accessed.isoformat(),
        message_count=0,
        image_references_count=0,
    )

    return CreateSessionResponse(session_id=session.session_id, session_info=session_info)


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str, state: ChatState = Depends(get_chat_state)) -> SessionInfo:
    """
    Get session information.

    Args:
        session_id: Session identifier
        state: Chat state

    Returns:
        Session information
    """
    session = state.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionInfo(
        session_id=session.session_id,
        collection_name=session.collection_name,
        created_at=session.created_at.isoformat(),
        last_accessed=session.last_accessed.isoformat(),
        message_count=len(session.conversation_history),
        image_references_count=len(session.image_references),
    )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str, state: ChatState = Depends(get_chat_state)
) -> JSONResponse:
    """
    Delete a chat session.

    Args:
        session_id: Session identifier
        state: Chat state

    Returns:
        Success response
    """
    deleted = state.session_manager.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return JSONResponse(content={"success": True, "message": "Session deleted"})


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat.

    Args:
        websocket: WebSocket connection
        session_id: Session identifier
    """
    await websocket.accept()

    # Get session
    session = chat_state.session_manager.get_session(session_id)
    if not session:
        await websocket.send_json({"type": "error", "content": "Session not found"})
        await websocket.close()
        return

    # Ensure generator is available
    if chat_state.generator is None:
        await websocket.send_json(
            {"type": "error", "content": "Chat service not initialized"}
        )
        await websocket.close()
        return

    logger.info(f"WebSocket connected for session {session_id}")

    try:
        while True:
            # Receive user message
            data = await websocket.receive_text()
            message = json.loads(data)

            user_content = message.get("content", "")
            if not user_content:
                continue

            # Add user message to history
            session.add_message("user", user_content)

            # Retrieve context
            start_time = time.time()
            text_results, image_results, retrieval_metrics = await retrieve_context(
                session, user_content, chat_state
            )

            # Format context for LLM (this populates citation_map in formatter)
            formatted_context = chat_state.context_formatter.format_multimodal_context(
                text_results, image_results
            )

            # Get citation map and enhance with document URLs for text citations
            citation_map = chat_state.context_formatter.get_citation_map()

            # Add document_url to text citations
            for citation_id, citation_data in citation_map.items():
                if citation_data.get("type") == "text":
                    metadata = citation_data.get("metadata", {})
                    document_path = metadata.get("document_path")
                    if document_path:
                        # Extract filename from path for URL
                        filename = safe_filename(document_path)
                        if filename:
                            citation_data["document_url"] = f"/api/documents/{session.collection_name}/{filename}"

            # Send context to client with citation map
            context_msg = ContextMessage(
                text_results=[
                    {"content": r.get("content", ""), "source": r.get("source", ""), "score": r.get("score", 0)}
                    for r in text_results
                ],
                image_results=[
                    {
                        "document_id": r.get("document_id", ""),
                        "image_metadata": r.get("image_metadata", {}),
                        "score": r.get("score", 0),
                    }
                    for r in image_results
                ],
                retrieved_docs=len(text_results),
                retrieved_images=len(image_results),
                retrieval_metrics=retrieval_metrics.to_dict(),
                citation_map=citation_map,
            )
            await websocket.send_json(context_msg.dict())

            # Track image references
            image_refs = chat_state.context_formatter.extract_image_references(image_results)
            for doc_id, metadata in image_refs.items():
                session.track_image(doc_id, metadata)

            # Build messages for generation
            system_prompt = get_system_prompt(
                prompt_type="multimodal" if image_results else "default",
                context=formatted_context,
            )

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(session.get_recent_history(max_turns=session.config.max_history_turns))
            messages.append({"role": "user", "content": user_content})

            # Generate response with streaming
            generated_text = ""
            token_count = 0

            async for token in chat_state.generator.generate_stream(
                messages,
                max_tokens=session.config.max_tokens,
                temperature=session.config.temperature,
            ):
                generated_text += token
                token_count += 1

                # Send token to client
                await websocket.send_json(
                    {"type": "assistant_chunk", "content": token, "metadata": {}}
                )

            # Add assistant response to history
            session.add_message("assistant", generated_text)

            # Send completion message
            duration_ms = (time.time() - start_time) * 1000
            complete_msg = CompleteMessage(
                tokens_generated=token_count,
                duration_ms=duration_ms,
                thinking_mode=session.config.enable_thinking,
            )
            await websocket.send_json(complete_msg.dict())

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


async def retrieve_context(
    session: Session,
    query: str,
    state: ChatState,
    max_text_results: int = DEFAULT_TEXT_RESULTS,
    max_image_results: int = DEFAULT_IMAGE_RESULTS,
) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]], RetrievalMetrics]:
    """
    Retrieve and optionally re-rank context documents.

    Args:
        session: Chat session
        query: User query
        state: Chat state
        max_text_results: Maximum number of text results to return
        max_image_results: Maximum number of image results to return

    Returns:
        Tuple of (text_results, image_results, metrics)

    Raises:
        TypeError: If query_embedding doesn't have expected type
    """
    # Initialize metrics
    metrics = RetrievalMetrics(
        reranking_enabled=state.rag_config.enable_reranking,
        hybrid_search_used=state.rag_config.enable_hybrid_search,
        compression_enabled=state.rag_config.enable_compression,
    )
    retrieval_start = time.time()

    if state.embedder is None or state.vector_store is None:
        logger.warning("Embedder or vector store not initialized")
        return [], [], metrics

    # Encode query
    try:
        config = EmbeddingConfig.for_query()
        query_embedding = state.embedder.embed_with_config([query], config)[0]

        # Validate embedding has tolist method
        if not hasattr(query_embedding, 'tolist'):
            raise TypeError(
                f"Expected array with tolist() method, got {type(query_embedding)}"
            )
    except Exception as e:
        logger.error(f"Failed to encode query: {e}")
        return [], [], metrics

    # Use RAG config for retrieval batch size
    retrieval_batch_size = state.rag_config.initial_retrieval_k

    # Vector search with timing
    vector_search_start = time.time()
    try:
        search_results = state.vector_store.similarity_search(
            collection_name=session.collection_name,
            query_embedding=query_embedding.tolist(),
            top_k=retrieval_batch_size,
        )
        metrics.vector_search_time_ms = (time.time() - vector_search_start) * 1000
    except Exception as e:
        logger.error(f"Vector store search failed: {e}")
        return [], [], metrics

    # Separate text and image results
    text_results = []
    image_results = []

    for result in search_results:
        metadata = result.metadata or {}
        result_type = metadata.get("modality", "text")

        result_data = {
            "document_id": result.id,
            "score": result.score,
            "content": result.document or "",
            "metadata": metadata,
        }

        if result_type == "image":
            # Build safe URLs with path traversal protection
            thumbnail_url = build_safe_image_url(
                "/api/images/thumbnail",
                session.collection_name,
                metadata.get('thumbnail_path', '')
            )
            full_image_url = build_safe_image_url(
                "/api/images/full",
                session.collection_name,
                metadata.get('image_path', '')
            )

            result_data["image_metadata"] = {
                "width": metadata.get("width", 0),
                "height": metadata.get("height", 0),
                "format": metadata.get("format", ""),
                "file_size": metadata.get("file_size", 0),
                "thumbnail_url": thumbnail_url,
                "full_image_url": full_image_url,
                "mean_rgb": [
                    metadata.get("mean_r", 0),
                    metadata.get("mean_g", 0),
                    metadata.get("mean_b", 0)
                ],
                "description": metadata.get("description", ""),
                "filename": safe_filename(metadata.get("source", "")),
            }
            image_results.append(result_data)
        else:
            result_data["source"] = metadata.get("source", "Unknown")
            text_results.append(result_data)

    # Update initial counts
    metrics.documents_retrieved = len(text_results)
    metrics.images_retrieved = len(image_results)

    # Apply reranking to text results if enabled
    if state.rag_config.enable_reranking and text_results and state.reranker is not None:
        rerank_start = time.time()
        try:
            logger.info(f"Applying reranking to {len(text_results)} text results")
            text_results = await state.reranker.rerank(
                query=query,
                documents=text_results,
                top_n=state.rag_config.rerank_top_n,
            )
            metrics.reranking_time_ms = (time.time() - rerank_start) * 1000
            metrics.documents_after_rerank = len(text_results)
            logger.info(f"Reranking complete, kept top {len(text_results)} results")
        except Exception as e:
            logger.error(f"Reranking failed: {e}. Using original results.")
            metrics.documents_after_rerank = len(text_results)
    else:
        metrics.documents_after_rerank = len(text_results)

    # Limit to configured maximum
    text_results = text_results[:max_text_results]
    image_results = image_results[:max_image_results]

    # Calculate total time
    metrics.total_time_ms = (time.time() - retrieval_start) * 1000

    logger.info(
        f"Retrieved {len(text_results)} text and {len(image_results)} image results "
        f"(total: {metrics.total_time_ms:.1f}ms, vector: {metrics.vector_search_time_ms:.1f}ms, "
        f"rerank: {metrics.reranking_time_ms:.1f}ms)"
    )

    return text_results, image_results, metrics
