"""Sequence management endpoints."""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status, Request
from loguru import logger
import asyncio

from mcs.utils.errors import create_error
from mcs.api.process.process_service import ProcessService
from mcs.api.process.models.process_models import (  # noqa: F401
    BaseResponse,
    Sequence,
    SequenceResponse,
    SequenceListResponse,
    ProcessStatus,
    StatusResponse
)

router = APIRouter(tags=["sequences"])


def get_process_service(request: Request) -> ProcessService:
    """Get service instance from app state."""
    return request.app.state.service


@router.get(
    "/",
    response_model=SequenceListResponse,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to list sequences"}
    }
)
async def list_sequences(
    service: ProcessService = Depends(get_process_service)
) -> SequenceListResponse:
    """List available sequences."""
    try:
        sequences = await service.sequence_service.list_sequences()
        return SequenceListResponse(sequences=sequences)
    except Exception as e:
        logger.error(f"Failed to list sequences: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list sequences: {str(e)}"
        )


@router.post(
    "/{sequence_id}/start",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Sequence not found"},
        status.HTTP_409_CONFLICT: {"description": "Sequence already running"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to start sequence"}
    }
)
async def start_sequence(
    sequence_id: str,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Start sequence execution."""
    try:
        await service.sequence_service.start_sequence(sequence_id)
        return BaseResponse(message=f"Sequence {sequence_id} started")
    except Exception as e:
        logger.error(f"Failed to start sequence {sequence_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to start sequence: {str(e)}"
        )


@router.post(
    "/{sequence_id}/stop",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Sequence not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to stop sequence"}
    }
)
async def stop_sequence(
    sequence_id: str,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Stop sequence execution."""
    try:
        await service.sequence_service.stop_sequence(sequence_id)
        return BaseResponse(message=f"Sequence {sequence_id} stopped")
    except Exception as e:
        logger.error(f"Failed to stop sequence {sequence_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to stop sequence: {str(e)}"
        )


@router.get(
    "/{sequence_id}/status",
    response_model=StatusResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Sequence not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get status"}
    }
)
async def get_status(
    sequence_id: str,
    service: ProcessService = Depends(get_process_service)
) -> StatusResponse:
    """Get sequence status."""
    try:
        status = await service.sequence_service.get_sequence_status(sequence_id)
        return StatusResponse(status=status)
    except Exception as e:
        logger.error(f"Failed to get sequence status {sequence_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get sequence status: {str(e)}"
        )


@router.websocket("/ws/{sequence_id}")
async def sequence_status(
    websocket: WebSocket,
    sequence_id: str
):
    """WebSocket endpoint for sequence status updates."""
    try:
        service = websocket.app.state.service
        if not service.is_running:
            await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
            return

        await websocket.accept()
        logger.info(f"Sequence {sequence_id} WebSocket client connected")

        # Create queue for status updates
        status_queue = asyncio.Queue()
        
        # Subscribe to status updates
        def status_changed(sequence_status: StatusResponse):
            asyncio.create_task(status_queue.put(sequence_status))
        
        service.sequence_service.on_status_changed(sequence_id, status_changed)

        try:
            while True:
                sequence_status = await status_queue.get()
                await websocket.send_json({
                    "type": "sequence_status",
                    "data": sequence_status.dict()
                })

        except WebSocketDisconnect:
            logger.info(f"Sequence {sequence_id} WebSocket client disconnected")
        finally:
            service.sequence_service.remove_status_changed_callback(sequence_id, status_changed)

    except Exception as e:
        logger.error(f"Sequence WebSocket error: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.get(
    "/{sequence_id}",
    response_model=SequenceResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Sequence not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get sequence"}
    }
)
async def get_sequence(
    sequence_id: str,
    service: ProcessService = Depends(get_process_service)
) -> SequenceResponse:
    """Get sequence by ID."""
    try:
        sequence = await service.sequence_service.get_sequence(sequence_id)
        return SequenceResponse(sequence=sequence)
    except Exception as e:
        logger.error(f"Failed to get sequence {sequence_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get sequence: {str(e)}"
        )
