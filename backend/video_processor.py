import cv2
import numpy as np
import threading
import time
from ultralytics import YOLO
from backend.config import (
    VIDEO_PATH, YOLO_MODEL, VEHICLE_CLASSES,
    FRAME_WIDTH, FRAME_HEIGHT, DETECTION_LINE_RATIO, JPEG_QUALITY,
)


class VideoProcessor:
    def __init__(self):
        self.model = YOLO(YOLO_MODEL)
        self.cap = None
        self.lock = threading.Lock()
        self.current_frame = None
        self.current_detections = []
        self.running = False
        self._open_video()

    def _open_video(self):
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(VIDEO_PATH)
        if not self.cap.isOpened():
            raise RuntimeError(f"Impossible d'ouvrir la vidéo : {VIDEO_PATH}")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25.0

    def _reset_tracker(self):
        """Réinitialise l'état interne du tracker YOLO (ByteTrack/BoTSORT)."""
        try:
            if (self.model.predictor is not None
                    and hasattr(self.model.predictor, "trackers")):
                for tracker in self.model.predictor.trackers:
                    tracker.reset()
        except Exception:
            # Si le reset échoue, forcer la recréation du predictor au prochain appel
            self.model.predictor = None

    def _read_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            # Boucle la vidéo : reset du tracker pour éviter la confusion entre
            # les tracks de la fin de vidéo et les frames du début
            self._reset_tracker()
            self._open_video()
            ret, frame = self.cap.read()
            if not ret:
                return None
            return frame, True  # flag: video looped
        return frame, False

    def process_frame(self):
        """Lit une frame, exécute YOLO, retourne (frame annotée, détections, looped)."""
        result = self._read_frame()
        if result is None:
            return None, [], False

        frame, looped = result
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Détection + tracking
        results = self.model.track(
            frame,
            persist=True,
            classes=VEHICLE_CLASSES,
            verbose=False,
            imgsz=640,
        )

        detections = []
        annotated = frame.copy()

        if results and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                track_id = int(box.id[0]) if box.id is not None else -1

                # Centroïde
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2

                detections.append({
                    "track_id": track_id,
                    "bbox": (x1, y1, x2, y2),
                    "center": (cx, cy),
                    "confidence": conf,
                    "class": cls,
                })

                # Dessiner bounding box
                color = (0, 255, 0)
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

                # Label
                label = f"ID:{track_id}" if track_id >= 0 else ""
                if label:
                    cv2.putText(
                        annotated, label, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
                    )

        # Dessiner la ligne de détection
        line_y = int(FRAME_HEIGHT * DETECTION_LINE_RATIO)
        cv2.line(annotated, (0, line_y), (FRAME_WIDTH, line_y), (0, 0, 255), 2)
        cv2.putText(
            annotated, "DETECTION ZONE", (10, line_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2,
        )

        with self.lock:
            self.current_frame = annotated
            self.current_detections = detections

        return annotated, detections, looped

    def encode_frame(self, frame):
        """Encode une frame en JPEG."""
        _, buffer = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
        )
        return buffer.tobytes()

    def generate_mjpeg(self, get_overlay_info=None):
        """Générateur MJPEG pour le streaming HTTP."""
        frame_delay = 1.0 / self.fps

        while True:
            annotated, detections, looped = self.process_frame()
            if annotated is None:
                time.sleep(0.1)
                continue

            # Overlay optionnel (compteur, timer, etc.)
            if get_overlay_info:
                overlay_info = get_overlay_info()
                self._draw_overlay(annotated, overlay_info)

            jpeg = self.encode_frame(annotated)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            )

            time.sleep(frame_delay)

    def _draw_overlay(self, frame, info):
        """Dessine les informations de jeu sur la frame."""
        count = info.get("count", 0)
        timer = info.get("timer", 0)
        phase = info.get("phase", "")

        # Fond semi-transparent pour le HUD
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (280, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Compteur
        cv2.putText(
            frame, f"Vehicules: {count}", (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2,
        )

        # Timer
        cv2.putText(
            frame, f"Timer: {timer}s", (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2,
        )

        # Phase
        phase_color = (0, 255, 0) if phase == "betting" else (0, 165, 255)
        cv2.putText(
            frame, phase.upper(), (20, 95),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, phase_color, 2,
        )

    def release(self):
        if self.cap is not None:
            self.cap.release()
