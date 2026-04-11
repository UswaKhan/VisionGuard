import cv2
import time


class FallDetector:
    def __init__(self):
        self.consecutive_frames = 0
        self.required_frames = 4
        self.cooldown_duration = 30
        self.last_fall_time = None

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

                if x_diff > 0.01 and y_diff / x_diff < 0.5:
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
        if is_fall:
            self.consecutive_frames = 0
            self.last_fall_time = time.time()

        return frame, is_fall

    def close(self):
        pass
