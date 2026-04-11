# VisionGuard — Project Document

## Overview

VisionGuard is an AI-powered real-time monitoring system designed to ensure the safety of elderly individuals and patients. It uses a live camera feed combined with computer vision and pose estimation to detect critical events such as falls and help gestures. When an event is detected, the system alerts caregivers and administrators through email and SMS notifications, enabling rapid response.

The system is accessed through a web-based dashboard with role-based access for administrators and caregivers.

---

## Problem Statement

Elderly individuals and patients, particularly those living alone or in care facilities, are at constant risk of falls and medical emergencies. Traditional monitoring relies on periodic check-ins or wearable devices, both of which have significant gaps. Falls often go unnoticed for extended periods, leading to worsened outcomes. There is a need for a non-intrusive, continuous, automated monitoring solution that can detect emergencies in real-time and immediately notify responsible caregivers.

---

## Objectives

1. Provide continuous, real-time video monitoring using a standard camera
2. Automatically detect fall events using AI-based pose estimation
3. Detect help hand gestures (raised hand) as a deliberate distress signal
4. Alert all registered caregivers and the system administrator immediately upon confirmed events
5. Log all detected events with timestamped image evidence
6. Provide a web-based interface for administrators to manage the system and for caregivers to monitor activity
7. Minimize false positives through sustained-detection confirmation and countdown cancellation

---

## System Users / Roles

### Administrator
- Single account, configured at system setup
- Full control over the system: start/stop the camera stream, manage caregivers, view and delete events and alerts
- Receives all alerts

### Caregiver
- Multiple accounts, created and managed by the administrator
- Can view the live stream (view-only, cannot start/stop)
- Can view event history
- Receives email and SMS alerts when events are detected

---

## Features

### 1. Live Camera Stream
- Real-time video feed from a connected camera
- Accessible through the web dashboard via WebSocket
- Administrator can start and stop the stream
- Caregivers can view the stream in read-only mode
- AI detection overlays (pose skeleton, detection labels, countdown) displayed on the live feed

### 2. Fall Detection
- Uses pose estimation to extract body landmarks (shoulders, hips)
- Determines if the person's torso orientation is horizontal (fallen posture)
- Requires sustained detection across multiple consecutive frames to confirm
- 30-second cooldown after each confirmed fall to prevent duplicate alerts
- Triggers a countdown before raising an alert, allowing the system to cancel if the person recovers

### 3. Hand Gesture Detection (Help Signal)
- Detects a raised hand using wrist-to-shoulder position from pose landmarks
- Either left or right hand qualifies
- Requires sustained detection across multiple consecutive frames to confirm
- Triggers a countdown before raising an alert, allowing the system to cancel if the hand is lowered
- No cooldown — the person can signal for help again immediately

### 4. Event Countdown and Confirmation
- When a fall or hand gesture is detected, a countdown timer begins (default: 5 seconds)
- The countdown is displayed on the live stream
- If the condition persists for the full duration, the event is confirmed
- If the condition clears before the countdown completes (hand lowered, person stands up), the countdown is cancelled and no event is recorded
- This mechanism reduces false positives

### 5. Event Logging
- Each confirmed event is saved with:
  - Event type (fall or hand gesture)
  - Timestamp
  - A captured image (clean snapshot without overlays)
- Events are viewable in the dashboard as a grid of image cards
- Administrator can delete individual events or all events

### 6. Email Alerts
- Sent automatically when an event is confirmed
- Recipients: administrator + all active caregivers
- Includes event type, timestamp, and the captured image as an attachment
- Uses SMTP (Gmail)

### 7. SMS Alerts
- Sent automatically when an event is confirmed
- Recipients: administrator phone + all active caregiver phones
- Includes a short text message describing the event type

### 8. Authentication and Access Control
- Single login page for both roles
- Administrator credentials configured via environment variables
- Caregiver credentials stored in the database
- Role-based redirection after login (admin dashboard vs caregiver dashboard)
- Protected routes — admin pages require admin role, caregiver pages require caregiver role

### 9. Admin Dashboard
- **Overview**: Summary statistics (total events, total alerts, total caregivers)
- **Live Stream**: Start/stop stream, view real-time feed with detection overlays
- **Events**: Grid view of all captured events with images, type badges, timestamps, and delete actions
- **Alerts**: Table of all sent alerts with message, recipient, timestamp, and delete actions
- **Caregivers**: Add new caregivers (name, email, phone, password), view list, delete caregivers

### 10. Caregiver Dashboard
- **Overview**: Summary statistics (total events) and quick links
- **Live Stream**: View-only real-time feed (no start/stop control)
- **Events**: Read-only grid view of all captured events

---

## Functional Requirements

| ID    | Requirement |
|-------|-------------|
| FR-01 | The system shall capture a real-time video feed from a connected camera |
| FR-02 | The system shall perform pose estimation on the video feed to extract body landmarks |
| FR-03 | The system shall detect fall events based on the orientation of the torso (shoulders relative to hips) |
| FR-04 | The system shall detect raised hand gestures based on wrist position relative to shoulders |
| FR-05 | The system shall require multiple consecutive frames of detection before confirming an event |
| FR-06 | The system shall start a countdown timer upon initial detection, visible on the live stream |
| FR-07 | The system shall cancel the countdown if the detected condition clears before the timer expires |
| FR-08 | The system shall save a clean image snapshot (without overlays) for each confirmed event |
| FR-09 | The system shall store event records in the database with type, image path, and timestamp |
| FR-10 | The system shall send email alerts with image attachments to the admin and all active caregivers upon event confirmation |
| FR-11 | The system shall send SMS alerts to the admin and all active caregivers upon event confirmation |
| FR-12 | The system shall store alert records in the database with message, recipients, and timestamp |
| FR-13 | The system shall enforce a cooldown period after a confirmed fall to prevent duplicate alerts |
| FR-14 | The system shall stream video frames to the web dashboard in real-time via WebSocket |
| FR-15 | The system shall display detection overlays (pose skeleton, labels, countdown) on the live stream |
| FR-16 | The system shall provide a login page that authenticates both admin and caregiver users |
| FR-17 | The system shall redirect users to their respective dashboards based on role after login |
| FR-18 | The system shall restrict admin routes to admin users only |
| FR-19 | The system shall restrict caregiver routes to caregiver users only |
| FR-20 | The admin shall be able to start and stop the camera stream |
| FR-21 | The admin shall be able to add new caregivers with name, email, phone, and password |
| FR-22 | The admin shall be able to delete caregivers |
| FR-23 | The admin shall be able to view and delete individual events or all events |
| FR-24 | The admin shall be able to view and delete individual alerts or all alerts |
| FR-25 | Caregivers shall be able to view the live stream in read-only mode |
| FR-26 | Caregivers shall be able to view event history |

---

## Non-Functional Requirements

| ID     | Requirement |
|--------|-------------|
| NFR-01 | The system shall process video frames with minimal latency to provide near real-time detection |
| NFR-02 | The system shall run detection and streaming without blocking the main web application |
| NFR-03 | Event saving and alert sending shall not block the video stream |
| NFR-04 | The system shall be accessible from any modern web browser (Chrome, Firefox, Edge, Safari) |
| NFR-05 | The web interface shall be responsive and usable on desktop and mobile devices |
| NFR-06 | The system shall handle camera disconnection or failure gracefully without crashing |
| NFR-07 | The system shall use environment variables for all sensitive configuration (credentials, database URL, mail settings) |
| NFR-08 | The system shall use a relational database (PostgreSQL) for persistent data storage |
| NFR-09 | The system shall support multiple simultaneous viewers on the live stream via WebSocket |
| NFR-10 | Detection accuracy shall be sufficient to distinguish between standing, sitting, and fallen postures |
| NFR-11 | The system shall minimize false positive detections through consecutive frame thresholds and countdown cancellation |
| NFR-12 | The UI shall provide clear visual feedback for stream status (live, stopped), event types (fall, gesture), and countdown state |

---

## Technology Stack

| Component       | Technology |
|-----------------|------------|
| Backend         | Python, Flask |
| Real-time       | Flask-SocketIO (WebSocket) |
| Database        | PostgreSQL, Flask-SQLAlchemy |
| Authentication  | Flask-Login |
| Email           | Flask-Mail (SMTP / Gmail) |
| Computer Vision | OpenCV |
| Pose Estimation | MediaPipe Pose Landmarker |
| Frontend        | HTML, CSS, JavaScript, Bootstrap 5, Font Awesome |
| WebSocket Client| Socket.IO |

---

## Data Model

### Caregiver
- id (primary key)
- name
- email (unique)
- phone
- password
- is_active (boolean, default true)
- created_at (timestamp)

### Event
- id (primary key)
- event_type (fall / hand_gesture)
- image_path
- created_at (timestamp)
- relationship: has many Alerts

### Alert
- id (primary key)
- event_id (foreign key to Event, nullable)
- message
- sent_to
- created_at (timestamp)

---

## Detection Flow

```
Camera Feed
    |
    v
Pose Estimation (MediaPipe) — extracts body landmarks every Nth frame
    |
    +--> Hand Gesture Detector — wrist above shoulder?
    |        |
    |        +--> Consecutive frame threshold met?
    |                 |
    |                 YES --> Start 5s countdown
    |                            |
    |                            +--> Hand still raised? --> Continue countdown
    |                            +--> Hand lowered?      --> Cancel countdown
    |                            +--> Countdown complete? --> Save event + Send alerts
    |
    +--> Fall Detector — torso horizontal?
             |
             +--> Consecutive frame threshold met?
                      |
                      YES --> Start 5s countdown
                                 |
                                 +--> Still fallen?      --> Continue countdown
                                 +--> Person recovered?  --> Cancel countdown
                                 +--> Countdown complete? --> Save event + Send alerts
                                 |
                                 (30s cooldown after confirmed fall)
```

---

## Alert Flow

```
Event Confirmed
    |
    +--> Save snapshot image to static/events/
    +--> Create Event record in database
    +--> Send email (with image attachment) to admin + all active caregivers
    |        +--> Create Alert record in database
    +--> Send SMS to admin phone + all active caregiver phones
```
