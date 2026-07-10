# VisionGuard

AI-powered real-time monitoring system for elderly individuals and patients. Uses a live camera feed (CCTV/RTSP or webcam) with pose estimation to detect **falls** and **raised-hand help gestures**, then alerts caregivers instantly via **email** and **SMS**.

---

## Features

- **Live Camera Stream** — Real-time video feed accessible through a web dashboard via WebSocket
- **CCTV / RTSP Support** — Connects to a network CCTV camera (e.g. TP-Link Tapo) over RTSP, with automatic fallback to the local webcam if the CCTV drops
- **Low-Latency Streaming** — A background reader keeps only the newest frame and detection runs on a downscaled copy, so the feed stays near real-time
- **PTZ Camera Control** — Pan/tilt the CCTV camera live from the admin dashboard using the keyboard arrow keys (over ONVIF)
- **Fall Detection** — Detects a rapid drop into a horizontal torso posture using MediaPipe pose landmarks
- **Continuous Fall Alerting** — While a fallen person stays on the ground, the alert repeats every 30 seconds until they get up or are helped
- **Hand Gesture Detection** — Detects raised hand (wrist above shoulder) as a help signal
- **Countdown Confirmation** — 5-second countdown before confirming events, cancels if condition clears (reduces false positives)
- **Email Alerts** — Sends email with event image attachment to admin and all active caregivers
- **SMS Alerts** — Sends SMS via Vonage to admin and caregiver phone numbers
- **Event Logging** — Saves timestamped clean snapshots (no overlay) for each confirmed event
- **Role-Based Access** — Admin (full control) and Caregiver (read-only) dashboards
- **Caregiver Management** — Admin can add, view, and delete caregiver accounts

---

## Tech Stack

| Component        | Technology                          |
|------------------|-------------------------------------|
| Backend          | Flask, Flask-SocketIO (threading)   |
| Database         | PostgreSQL, Flask-SQLAlchemy        |
| Authentication   | Flask-Login                         |
| Computer Vision  | OpenCV, MediaPipe Pose Landmarker   |
| Camera Control   | ONVIF (onvif-zeep) for PTZ          |
| Email            | Flask-Mail (Gmail SMTP)             |
| SMS              | Vonage SMS API                      |
| Frontend         | Bootstrap 5, Font Awesome, Socket.IO|

---

## Project Structure

```
VisionGuard_FYP/
├── run.py                        # Entry point
├── config.py                     # Loads .env configuration
├── requirements.txt
├── pose_landmarker.task          # MediaPipe pose model
├── app/
│   ├── __init__.py               # App factory (Flask, SocketIO, SQLAlchemy, Mail)
│   ├── models.py                 # Caregiver, Event, Alert models
│   ├── ptz.py                    # ONVIF pan/tilt camera controller
│   ├── routes/
│   │   ├── auth.py               # Login/logout, User class
│   │   ├── admin.py              # Admin CRUD routes
│   │   ├── caregiver.py          # Caregiver read-only routes
│   │   └── stream.py             # Camera streaming, detection loop, event/alert pipeline
│   ├── detection/
│   │   ├── fall_detection.py     # Fall detector
│   │   └── hand_gesture.py       # Raised hand detector
│   ├── alerts/
│   │   ├── email_alert.py        # Email sending
│   │   └── sms_alert.py          # SMS sending via Vonage
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── admin/                # Admin dashboard pages
│   │   └── caregiver/            # Caregiver dashboard pages
│   └── static/
│       ├── favicon.svg
│       └── events/               # Captured event images
```

---

## Prerequisites

- Python 3.10+
- PostgreSQL
- A camera — either a CCTV/RTSP camera (e.g. TP-Link Tapo, with RTSP + ONVIF enabled) or a local webcam
- Gmail account with [App Password](https://support.google.com/accounts/answer/185833) for email alerts
- Vonage account for SMS alerts

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/UswaKhan/VisionGuard.git
   cd VisionGuard
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate        # Linux/Mac
   venv\Scripts\activate           # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL**

   Create a database for the project:

   ```sql
   CREATE DATABASE visionguard;
   ```

5. **Configure environment variables**

   Create a `.env` file in the project root:

   ```env
   # Admin Account
   ADMIN_NAME=Admin
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=your_admin_password
   ADMIN_PHONE=923001234567

   # Flask
   SECRET_KEY=your_secret_key

   # Database
   DATABASE_URL=postgresql://username:password@localhost:5432/visionguard

   # Email (Gmail SMTP)
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_gmail_app_password

   # Vonage SMS
   VONAGE_API_KEY=your_vonage_api_key
   VONAGE_API_SECRET=your_vonage_api_secret
   VONAGE_FROM_NUMBER=your_vonage_number

   # CCTV / RTSP camera (optional — omit to use the local webcam)
   # Username/password are the Camera Account set in the Tapo app.
   RTSP_URL=rtsp://username:password@192.168.1.x:554/cam/stream2
   ONVIF_PORT=2020
   ```

   If `RTSP_URL` is not set, the system uses the local webcam automatically.

6. **Run the application**

   ```bash
   python run.py
   ```

   The app will be available at `http://localhost:5000`.

---

## Usage

### Admin

1. Log in with the admin credentials configured in `.env`
2. **Start the stream** from the Live Stream page to begin monitoring
3. **Move the camera** (CCTV only) — click the live stream, then use the keyboard **arrow keys** to pan/tilt (hold to move, release to stop)
4. **Add caregivers** from the Caregivers page (name, email, phone, password)
5. View detected events and sent alerts from their respective pages
6. Delete events or alerts as needed

### Caregiver

1. Log in with credentials created by the admin
2. View the live stream (read-only)
3. View event history (read-only)
4. Receive email and SMS alerts automatically when events are detected

---

## Detection Logic

- **Fall Detection**: Pose landmarks detect a rapid downward drop into a horizontal torso posture (shoulders level with hips). Requires 4+ consecutive detection frames, then starts a 5-second countdown before the first alert.
- **Continuous Fall Alerting**: After a confirmed fall, the system keeps watching. As long as the person stays lying down, it repeats the alert every 30 seconds. Alerting stops automatically once the person is upright again.
- **Hand Gesture**: Detects if either wrist is above the corresponding shoulder. Requires 3+ consecutive detection frames, then starts a 5-second countdown. No cooldown — the person can signal again immediately.
- **Countdown Cancellation**: If the person recovers (stands up or lowers hand) before the countdown finishes, the event is cancelled and no alert is sent.
- **Camera Handling**: On start the system connects to the CCTV over RTSP; if that fails or drops mid-stream, it falls back to the local webcam. A background reader keeps only the newest frame and pose detection runs on a downscaled copy to keep latency low.

---

## Data Model

| Table     | Key Fields                                           |
|-----------|------------------------------------------------------|
| Caregiver | id, name, email, phone, password, is_active, created_at |
| Event     | id, event_type, image_path, created_at               |
| Alert     | id, event_id (FK), message, sent_to, created_at      |

---

## License

This project was developed as a Final Year Project (FYP).
