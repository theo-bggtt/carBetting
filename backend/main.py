import asyncio
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.video_processor import VideoProcessor
from backend.vehicle_counter import VehicleCounter
from backend.betting_manager import BettingManager

app = FastAPI(title="carBetting")

# Instances globales
counter = VehicleCounter()
processor = VideoProcessor()
manager = BettingManager(counter)

# Connecter le VideoProcessor au counter et au manager
_original_process_frame = processor.process_frame

def _process_frame_with_count():
    frame, detections, looped = _original_process_frame()
    if looped:
        pass
    if detections:
        counter.update(detections)
    manager.tick()
    return frame, detections, looped

processor.process_frame = _process_frame_with_count


def get_overlay_info():
    elapsed_import = __import__("time").time() - manager.round_start_time
    timer = max(0, int(30 - elapsed_import))
    return {
        "count": counter.count,
        "timer": timer,
        "phase": manager.phase,
    }


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        processor.generate_mjpeg(get_overlay_info=get_overlay_info),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = websocket.query_params.get("user_id", f"user_{id(websocket)}")

    try:
        async def send_state():
            while True:
                state = manager.get_state(user_id=user_id)
                await websocket.send_text(json.dumps(state))
                await asyncio.sleep(0.2)

        send_task = asyncio.create_task(send_state())

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("action") == "bet":
                option = msg.get("option")
                amount = int(msg.get("amount", 0))
                success, message = manager.place_bet(user_id, option, amount)
                await websocket.send_text(json.dumps({
                    "type": "bet_response",
                    "success": success,
                    "message": message,
                    "balance": manager.get_balance(user_id),
                }))

    except WebSocketDisconnect:
        send_task.cancel()
    except Exception:
        send_task.cancel()


# Servir le frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
