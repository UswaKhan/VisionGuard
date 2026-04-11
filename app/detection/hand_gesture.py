import cv2


class HandGestureDetector:
    def __init__(self):
        self.consecutive_frames = 0
        self.required_frames = 3

    def detect(self, frame, landmarks, h, w):
        detected_this_frame = False

        if landmarks:
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_wrist = landmarks[15]
            right_wrist = landmarks[16]

            left_raised = (
                left_wrist.visibility > 0.5
                and left_shoulder.visibility > 0.5
                and left_wrist.y < left_shoulder.y - 0.05
            )
            right_raised = (
                right_wrist.visibility > 0.5
                and right_shoulder.visibility > 0.5
                and right_wrist.y < right_shoulder.y - 0.05
            )

            if left_raised or right_raised:
                detected_this_frame = True

        if detected_this_frame:
            self.consecutive_frames += 1
        else:
            self.consecutive_frames = 0

        is_help_gesture = self.consecutive_frames >= self.required_frames

        return frame, is_help_gesture

    def close(self):
        pass
