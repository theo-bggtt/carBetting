from backend.config import FRAME_HEIGHT, DETECTION_LINE_RATIO


class VehicleCounter:
    def __init__(self):
        self.line_y = int(FRAME_HEIGHT * DETECTION_LINE_RATIO)
        self._count = 0
        self._tracked_positions = {}  # track_id -> last_cy
        self._counted_ids = set()     # IDs déjà comptés

    @property
    def count(self):
        return self._count

    def update(self, detections):
        """Met à jour le compteur avec les nouvelles détections.

        Compte un véhicule quand son centroïde traverse la ligne de détection
        du haut vers le bas (ou inversement).
        """
        for det in detections:
            track_id = det["track_id"]
            if track_id < 0:
                continue

            cx, cy = det["center"]

            if track_id in self._counted_ids:
                # Déjà compté, on met juste à jour la position
                self._tracked_positions[track_id] = cy
                continue

            if track_id in self._tracked_positions:
                last_cy = self._tracked_positions[track_id]
                # Franchissement de la ligne (dans les deux sens)
                if (last_cy < self.line_y <= cy) or (last_cy > self.line_y >= cy):
                    self._count += 1
                    self._counted_ids.add(track_id)

            self._tracked_positions[track_id] = cy

    def reset(self):
        """Remet le compteur à zéro pour un nouveau round."""
        self._count = 0
        self._tracked_positions.clear()
        self._counted_ids.clear()
