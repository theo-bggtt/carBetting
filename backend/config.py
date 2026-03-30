import os

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_PATH = os.path.join(BASE_DIR, "videos", "sample.mp4")

# Modèle YOLO
YOLO_MODEL = "yolov8n.pt"
# Classes COCO pour véhicules : 2=car, 3=motorcycle, 5=bus, 7=truck
VEHICLE_CLASSES = [2, 3, 5, 7]

# Dimensions de traitement
FRAME_WIDTH = 960
FRAME_HEIGHT = 540

# Ligne de détection (position Y en fraction de la hauteur, 0.0 = haut, 1.0 = bas)
DETECTION_LINE_RATIO = 0.72

# Qualité JPEG pour le stream MJPEG
JPEG_QUALITY = 75

# Round de paris
ROUND_DURATION_SECONDS = 30
BETTING_WINDOW_SECONDS = 10

# Balance initiale
INITIAL_BALANCE = 1000

# Seuils de paris par défaut (ajustables)
BET_THRESHOLD_LOW = 5
BET_THRESHOLD_HIGH = 10
