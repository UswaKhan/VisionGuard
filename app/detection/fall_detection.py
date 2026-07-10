import cv2
import time


class FallDetector:
    def __init__(self):
        self.consecutive_frames = 0
        self.required_frames = 4
        self.cooldown_duration = 30
        self.last_fall_time = None
        self.was_upright = False
        self.prev_shoulder_y = None
        self.prev_time = None
        self.rapid_drop = False
        self.drop_velocity_threshold = 0.35

    def detect(self, frame, landmarks, h, w):
        if self.last_fall_time is not None:
            if time.time() - self.last_fall_time < self.cooldown_duration:
                return frame, False

        detected_this_frame = False

        if landmarks:
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_hip = landmarks[23]
            right_hip = landmarks[24]

            if (
                left_shoulder.visibility > 0.5
                and right_shoulder.visibility > 0.5
                and left_hip.visibility > 0.5
                and right_hip.visibility > 0.5
            ):
                avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
                avg_hip_y = (left_hip.y + right_hip.y) / 2
                avg_shoulder_x = (left_shoulder.x + right_shoulder.x) / 2
                avg_hip_x = (left_hip.x + right_hip.x) / 2

                y_diff = abs(avg_shoulder_y - avg_hip_y)
                x_diff = abs(avg_shoulder_x - avg_hip_x)

                is_horizontal = x_diff > 0.01 and y_diff / x_diff < 0.5
                is_upright = y_diff > 0.01 and y_diff / (x_diff + 0.001) > 1.0

                if is_upright:
                    self.was_upright = True
                    self.rapid_drop = False

                now = time.time()
                if self.was_upright and self.prev_shoulder_y is not None and self.prev_time is not None:
                    dt = now - self.prev_time
                    if dt > 0:
                        velocity = (avg_shoulder_y - self.prev_shoulder_y) / dt
                        if velocity > self.drop_velocity_threshold:
                            self.rapid_drop = True

                self.prev_shoulder_y = avg_shoulder_y
                self.prev_time = now

                if is_horizontal and self.was_upright and self.rapid_drop:
                    detected_this_frame = True
                    cv2.putText(
                        frame,
                        "FALL DETECTED!",
                        (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2,
                    )

        if detected_this_frame:
            self.consecutive_frames += 1
        else:
            self.consecutive_frames = 0

        is_fall = self.consecutive_frames >= self.required_frames

        return frame, is_fall

    def is_lying_down(self, landmarks):
        """Posture-only check: is the person horizontal right now?
        Unlike detect(), this needs no rapid drop — used to tell whether a
        fallen person is still on the ground."""
        if not landmarks:
            return False

        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        left_hip = landmarks[23]
        right_hip = landmarks[24]

        if not (
            left_shoulder.visibility > 0.5
            and right_shoulder.visibility > 0.5
            and left_hip.visibility > 0.5
            and right_hip.visibility > 0.5
        ):
            return False

        avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        avg_hip_y = (left_hip.y + right_hip.y) / 2
        avg_shoulder_x = (left_shoulder.x + right_shoulder.x) / 2
        avg_hip_x = (left_hip.x + right_hip.x) / 2

        y_diff = abs(avg_shoulder_y - avg_hip_y)
        x_diff = abs(avg_shoulder_x - avg_hip_x)

        return x_diff > 0.01 and y_diff / x_diff < 0.5

    def start_cooldown(self):
        self.consecutive_frames = 0
        self.last_fall_time = time.time()
        self.was_upright = False
        self.rapid_drop = False
        self.prev_shoulder_y = None
        self.prev_time = None

    def close(self):
        pass
