# 🚗 carBetting

Un mini-jeu de paris en temps réel basé sur la détection de véhicules dans un flux vidéo.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-ultralytics-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📖 Présentation

**carBetting** affiche un flux vidéo d'une route sur lequel une intelligence artificielle détecte et suit chaque véhicule en temps réel. Toutes les **30 secondes**, un round se termine et le score de véhicules ayant traversé la zone de détection est révélé.

L'utilisateur peut **parier** (en coins virtuels) sur le nombre de véhicules qui passeront pendant le round, en choisissant parmi 3 options :
- 🟢 **Moins de X** véhicules
- 🟡 **Entre X et Y** véhicules
- 🔴 **Plus de Y** véhicules

### Aperçu

```
┌─────────────────────────────────────────┬──────────────────┐
│                                         │  Round 4         │
│   [Flux vidéo avec bounding boxes]      │  ████████░░  18s │
│                                         │  Véhicules : 7   │
│   ─────────── DETECTION ZONE ────────── │                  │
│                                         │  [Moins de 5]    │
│                                         │  [Entre 5 et 10] │
│                                         │  [Plus de 10]    │
│                                         │  Solde : 1250 ★  │
└─────────────────────────────────────────┴──────────────────┘
```

---

## 🛠️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| Détection véhicules | [YOLOv8 nano](https://docs.ultralytics.com/) (ultralytics) |
| Tracking inter-frames | ByteTrack (intégré à ultralytics) |
| Traitement vidéo | OpenCV |
| Backend web | FastAPI + uvicorn |
| Streaming vidéo | MJPEG over HTTP |
| Temps réel jeu | WebSocket |
| Frontend | HTML / CSS / JavaScript vanilla |

---

## 📋 Prérequis

- Python **3.9 ou supérieur**
- pip
- Une vidéo de route (`.mp4`) avec des voitures qui traversent l'écran

> Les poids du modèle YOLOv8n (~6 Mo) sont téléchargés automatiquement au premier lancement.

---

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/theo-bggtt/carBetting.git
cd carBetting
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r backend/requirements.txt
```

### 4. Ajouter une vidéo

Place une vidéo de route dans le dossier `videos/` sous le nom `sample.mp4` :

```
carBetting/
└── videos/
    └── sample.mp4   ← ta vidéo ici
```

> La vidéo doit montrer une route vue de dessus ou de côté avec des véhicules qui traversent l'image horizontalement.

### 5. Lancer l'application

```bash
python run.py
```

Ouvre ensuite **http://localhost:8000** dans ton navigateur.

---

## 🎮 Comment jouer

1. **Attends l'ouverture des paris** (phase verte "PARIS OUVERTS", les 10 premières secondes du round)
2. **Choisis une option** : "Moins de 5", "Entre 5 et 10" ou "Plus de 10"
3. **Saisis ta mise** en coins (tu commences avec 1000 ★)
4. **Clique sur l'option** pour confirmer le pari
5. **Attends la fin du round** (30 secondes) pour voir le résultat
6. En cas de victoire, tu remportes ta mise multipliée par le coefficient affiché (x2.0 à x2.5)

---

## ⚙️ Configuration

Tous les paramètres sont centralisés dans `backend/config.py` :

```python
# Chemin de la vidéo
VIDEO_PATH = "videos/sample.mp4"

# Modèle YOLO (yolov8n.pt = nano, le plus rapide)
YOLO_MODEL = "yolov8n.pt"

# Position de la ligne de comptage (0.0 = haut, 1.0 = bas)
DETECTION_LINE_RATIO = 0.72

# Durée d'un round (secondes)
ROUND_DURATION_SECONDS = 30

# Fenêtre de paris (secondes depuis le début du round)
BETTING_WINDOW_SECONDS = 10

# Seuils des options de paris
BET_THRESHOLD_LOW = 5    # "Moins de X"
BET_THRESHOLD_HIGH = 10  # "Plus de X"

# Balance de départ
INITIAL_BALANCE = 1000
```

### Choisir un modèle YOLO plus précis

| Modèle | Vitesse | Précision | Usage recommandé |
|--------|---------|-----------|-------------------|
| `yolov8n.pt` | ⚡⚡⚡ | ★★☆ | CPU, vidéo temps réel |
| `yolov8s.pt` | ⚡⚡☆ | ★★★ | CPU puissant ou GPU |
| `yolov8m.pt` | ⚡☆☆ | ★★★★ | GPU recommandé |

---

## 🗂️ Structure du projet

```
carBetting/
├── backend/
│   ├── __init__.py
│   ├── config.py            # Constantes et paramètres
│   ├── main.py              # App FastAPI (routes + WebSocket)
│   ├── video_processor.py   # Détection YOLO + stream MJPEG
│   ├── vehicle_counter.py   # Comptage par franchissement de ligne
│   ├── betting_manager.py   # Lifecycle des rounds et paris
│   └── requirements.txt     # Dépendances Python
├── frontend/
│   ├── index.html           # Page principale
│   ├── style.css            # Thème casino sombre
│   └── app.js               # Client WebSocket + logique UI
├── videos/                  # Dossier pour les vidéos (non versionné)
├── run.py                   # Point d'entrée
└── README.md
```

---

## 🔌 API

### `GET /video_feed`
Stream MJPEG du flux vidéo annoté (bounding boxes + ligne de détection + HUD).

### `WebSocket /ws?user_id=<id>`
Canal temps réel bidirectionnel.

**Messages reçus (serveur → client) :**
```json
{
  "type": "state",
  "round_id": 4,
  "phase": "betting",
  "count": 7,
  "timer_seconds_remaining": 18,
  "balance": 1150,
  "bet_options": [
    {"id": "under",   "label": "Moins de 5",    "multiplier": 2.5},
    {"id": "between", "label": "Entre 5 et 10", "multiplier": 2.0},
    {"id": "over",    "label": "Plus de 10",    "multiplier": 2.5}
  ]
}
```

**Messages envoyés (client → serveur) :**
```json
{ "action": "bet", "option": "between", "amount": 200 }
```

---

## 🧠 Fonctionnement de la détection

1. **YOLOv8** détecte les véhicules (voitures, motos, bus, camions) sur chaque frame
2. **ByteTrack** assigne un ID persistant à chaque véhicule entre les frames
3. Quand le centroïde d'un véhicule **traverse la ligne de détection**, le compteur s'incrémente de 1
4. Chaque ID n'est compté **qu'une seule fois** pour éviter les doublons
5. Le tracker est **réinitialisé** à chaque boucle de la vidéo pour éviter la dégradation du tracking

---

## 🗺️ Roadmap

- [ ] Support flux live (RTSP / webcam)
- [ ] Multi-joueurs avec lobby partagé
- [ ] Persistance des scores (SQLite)
- [ ] Cotes dynamiques basées sur l'historique du trafic
- [ ] Interface mobile responsive

---

## 📄 Licence

MIT — libre d'utilisation, de modification et de distribution.
