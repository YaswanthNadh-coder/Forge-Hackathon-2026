"""
WebSocket endpoints for real-time audit updates and browser frame streaming.
"""

import json
import logging
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()

audit_connections: Dict[str, List[WebSocket]] = {}
browser_connections: Dict[str, List[WebSocket]] = {}


@router.websocket("/ws/audit/{audit_id}")
async def audit_websocket(websocket: WebSocket, audit_id: str):
    """Real-time updates for the bill extraction & audit pipeline."""
    await websocket.accept()

    if audit_id not in audit_connections:
        audit_connections[audit_id] = []
    audit_connections[audit_id].append(websocket)
    logger.info(f"Audit WebSocket connected for audit_id: {audit_id}")

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        if audit_id in audit_connections and websocket in audit_connections[audit_id]:
            audit_connections[audit_id].remove(websocket)
        logger.info(f"Audit WebSocket disconnected for audit_id: {audit_id}")


@router.websocket("/ws/browser/{thread_id}")
async def browser_websocket(websocket: WebSocket, thread_id: str):
    """Real-time base64 frame streaming for the Playwright CGRMS browser agent."""
    await websocket.accept()

    if thread_id not in browser_connections:
        browser_connections[thread_id] = []
    browser_connections[thread_id].append(websocket)
    logger.info(f"Browser WebSocket connected for thread_id: {thread_id}")

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        if thread_id in browser_connections and websocket in browser_connections[thread_id]:
            browser_connections[thread_id].remove(websocket)
        logger.info(f"Browser WebSocket disconnected for thread_id: {thread_id}")


async def broadcast_audit_update(audit_id: str, update: dict):
    """Broadcast state transitions to all active viewers of an audit session."""
    if audit_id not in audit_connections:
        return

    message = json.dumps(update)
    disconnected = []

    for ws in list(audit_connections[audit_id]):
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        if ws in audit_connections[audit_id]:
            audit_connections[audit_id].remove(ws)


async def broadcast_browser_frame(thread_id: str, frame_data: dict):
    """Broadcast live Playwright viewport screenshots to frontend."""
    if thread_id not in browser_connections:
        return

    message = json.dumps(frame_data)
    disconnected = []

    for ws in list(browser_connections[thread_id]):
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        if ws in browser_connections[thread_id]:
            browser_connections[thread_id].remove(ws)

