import threading
from urllib.parse import urlparse

from onvif import ONVIFCamera


class PTZController:
    """Controls the camera's pan/tilt motor over ONVIF.

    Uses the same account as the RTSP stream (the Camera Account set in the
    Tapo app). The ONVIF service is created lazily on first use and reused.
    """

    DIRECTIONS = {
        "left": (-1.0, 0.0),
        "right": (1.0, 0.0),
        "up": (0.0, 1.0),
        "down": (0.0, -1.0),
    }

    def __init__(self, host, port, user, password, speed=0.5):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.speed = speed
        self.ptz = None
        self.token = None
        self.lock = threading.Lock()

    def _ensure_connected(self):
        if self.ptz is None:
            cam = ONVIFCamera(self.host, self.port, self.user, self.password)
            media = cam.create_media_service()
            self.ptz = cam.create_ptz_service()
            self.token = media.GetProfiles()[0].token

    def move(self, direction):
        if direction not in self.DIRECTIONS:
            return
        x, y = self.DIRECTIONS[direction]
        with self.lock:
            self._ensure_connected()
            req = self.ptz.create_type("ContinuousMove")
            req.ProfileToken = self.token
            req.Velocity = {
                "PanTilt": {"x": x * self.speed, "y": y * self.speed}
            }
            self.ptz.ContinuousMove(req)

    def stop(self):
        with self.lock:
            self._ensure_connected()
            self.ptz.Stop({"ProfileToken": self.token})


def build_ptz_controller(app):
    """Create a PTZController from the app's RTSP_URL + ONVIF port config."""
    url = app.config.get("RTSP_URL")
    if not url:
        return None
    parsed = urlparse(url)
    if not parsed.hostname:
        return None
    port = app.config.get("ONVIF_PORT", 2020)
    return PTZController(
        parsed.hostname, port, parsed.username, parsed.password
    )
