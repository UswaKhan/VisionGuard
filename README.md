# VisionGuard

AI-powered real-time monitoring system for elderly individuals and patients. Uses a live camera feed with pose estimation to detect **falls** and **raised-hand help gestures**, then alerts caregivers instantly via **email** and **SMS**.

---

## Features

- **Live Camera Stream** — Real-time video feed accessible through a web dashboard via WebSocket
- **Fall Detection** — Detects horizontal torso orientation using MediaPipe pose landmarks
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
- A connected camera (webcam)
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
   ```

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
3. **Add caregivers** from the Caregivers page (name, email, phone, password)
4. View detected events and sent alerts from their respective pages
5. Delete events or alerts as needed

### Caregiver

1. Log in with credentials created by the admin
2. View the live stream (read-only)
3. View event history (read-only)
4. Receive email and SMS alerts automatically when events are detected

---

## Detection Logic

- **Fall Detection**: Pose landmarks determine if the torso (shoulders relative to hips) is horizontal. Requires 4+ consecutive detection frames, then starts a 5-second countdown. A 30-second cooldown prevents duplicate alerts.
- **Hand Gesture**: Detects if either wrist is above the corresponding shoulder. Requires 3+ consecutive detection frames, then starts a 5-second countdown. No cooldown — the person can signal again immediately.
- **Countdown Cancellation**: If the person recovers (stands up or lowers hand) before the countdown finishes, the event is cancelled and no alert is sent.

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
