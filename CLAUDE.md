# VisionGuard — Development Context

## Project

AI-powered elderly/patient monitoring system. See `PROJECT.md` for the full specification.

## Tech Stack

- **Backend**: Flask, Flask-SocketIO (threading mode), Flask-SQLAlchemy (PostgreSQL), Flask-Mail, Flask-Login
- **AI/CV**: OpenCV, MediaPipe Pose Landmarker
- **Frontend**: Bootstrap 5, Font Awesome, Socket.IO client

## Key Files

- `run.py` — entry point
- `config.py` — loads `.env` config
- `app/__init__.py` — app factory
- `app/models.py` — Caregiver, Event, Alert models
- `app/routes/auth.py` — login/logout, User class
- `app/routes/admin.py` — admin CRUD routes
- `app/routes/caregiver.py` — caregiver read-only routes
- `app/routes/stream.py` — camera streaming + detection loop + event/alert pipeline
- `app/detection/hand_gesture.py` — raised hand detector
- `app/detection/fall_detection.py` — fall detector
- `app/alerts/email_alert.py` — email sending
- `app/alerts/sms_alert.py` — SMS stub (prints to console)

## Known Design Decisions

- Admin is a single hardcoded account from `.env`, not a DB model
- Caregiver passwords are stored in plaintext (no hashing)
- SocketIO uses `async_mode="threading"` (not eventlet)
- Camera index is hardcoded to `1` with `cv2.CAP_DSHOW` (Windows DirectShow)
- Detection runs every 3rd frame for performance
- SMS alerting is a stub — prints to console, no real SMS provider integrated
- Same-browser multi-role login is not supported (cookie-based session limitation — use separate browsers to test admin and caregiver simultaneously)

---

## System Test Plan

### 1. Authentication & Access Control — PASSED

| # | Test Case | Status |
|---|-----------|--------|
| 1.1 | Admin login with correct credentials → redirects to `/admin/dashboard` | PASS |
| 1.2 | Caregiver login with correct credentials → redirects to `/caregiver/dashboard` | PASS |
| 1.3 | Login with wrong password → shows error, stays on login page | PASS |
| 1.4 | Login with non-existent email → shows error, stays on login page | PASS |
| 1.5 | Access `/admin/dashboard` without login → redirects to login | PASS |
| 1.6 | Access `/caregiver/dashboard` without login → redirects to login | PASS |
| 1.7 | Caregiver tries to access `/admin/*` routes → access denied | PASS |
| 1.8 | Admin tries to access `/caregiver/*` routes → access denied | PASS |
| 1.9 | Logout → session cleared, redirects to login | PASS |

### 2. Caregiver Management (Admin) — PASSED

| # | Test Case | Status |
|---|-----------|--------|
| 2.1 | Add caregiver with valid details → appears in list, can log in | PASS |
| 2.2 | Add caregiver with duplicate email → shows error, not added | PASS |
| 2.3 | Delete a caregiver → removed from list, can no longer log in | PASS |
| 2.4 | Caregiver list displays name, email, phone, status correctly | PASS |

### 3. Live Stream — PASSED

| # | Test Case | Status |
|---|-----------|--------|
| 3.1 | Admin clicks "Start Stream" → stream starts, status "Live", feed appears | PASS |
| 3.2 | Admin clicks "Stop Stream" → stream stops, status "Stopped", feed disappears | PASS |
| 3.3 | Start stream with no camera connected → fails gracefully, no crash | PASS |
| 3.4 | Caregiver views stream while admin has it running → feed appears | PASS |
| 3.5 | Caregiver views stream page when stream is off → shows placeholder | PASS |
| 3.6 | Multiple browsers open simultaneously → all receive the live feed | PASS |
| 3.7 | Pose skeleton overlay → green skeleton drawn on person | PASS |
| 3.8 | Stream does not freeze or stutter during detection | PASS |

### 4. Hand Gesture Detection — NOT YET TESTED

| # | Test Case | Status |
|---|-----------|--------|
| 4.1 | Raise one hand above shoulder and hold → "RAISED HAND" label appears | |
| 4.2 | Hold hand raised for 3+ consecutive detection frames → countdown starts | |
| 4.3 | Keep hand raised through full countdown → event is created | |
| 4.4 | Raise hand, then lower before countdown completes → countdown cancels | |
| 4.5 | Brief hand raise (1-2 detection frames only) → no countdown starts | |
| 4.6 | Raise hand again immediately after a confirmed event → new countdown starts | |
| 4.7 | Raise hand while a fall countdown is active → waits, fall takes priority | |

### 5. Fall Detection — NOT YET TESTED

| # | Test Case | Status |
|---|-----------|--------|
| 5.1 | Simulate fall (lie down / go horizontal) → "FALL DETECTED!" label appears | |
| 5.2 | Stay horizontal for 4+ consecutive detection frames → countdown starts | |
| 5.3 | Stay down through full countdown → event is created | |
| 5.4 | Fall then get back up before countdown completes → countdown cancels | |
| 5.5 | Briefly go horizontal (1-3 detection frames) → no countdown starts | |
| 5.6 | Fall again within 30 seconds of a confirmed fall → no new detection (cooldown) | |
| 5.7 | Fall again after 30 seconds → new detection and countdown starts | |

### 6. Event Countdown Behavior — NOT YET TESTED

| # | Test Case | Status |
|---|-----------|--------|
| 6.1 | Countdown displays on the livestream → "Alert in Xs" visible | |
| 6.2 | Countdown decrements smoothly → 5, 4, 3, 2, 1, fires (no oscillation) | |
| 6.3 | Countdown cancellation → text disappears when condition clears | |
| 6.4 | Stream does not freeze when countdown completes | |

### 7. Event Logging — NOT YET TESTED

| # | Test Case | Status |
|---|-----------|--------|
| 7.1 | Confirmed event creates a record → appears in admin events page | |
| 7.2 | Event image is a clean snapshot → no overlay text or pose skeleton | |
| 7.3 | Event shows correct type → "Fall Detected" or "Hand Gesture" badge | |
| 7.4 | Event shows correct timestamp | |
| 7.5 | Event image loads in the browser → valid path, image renders | |
| 7.6 | Events appear in caregiver's event page too (read-only) | |

### 8. Email Alerts — NOT YET TESTED

| # | Test Case | Status |
|---|-----------|--------|
| 8.1 | Email sent on confirmed hand gesture → admin + active caregivers receive it | |
| 8.2 | Email sent on confirmed fall → admin + active caregivers receive it | |
| 8.3 | Email subject matches event type | |
| 8.4 | Email body contains timestamp | |
| 8.5 | Email has image attachment (clean snapshot) | |
| 8.6 | Alert record created in database → appears in admin alerts page | |
| 8.7 | Inactive caregiver does NOT receive email | |
| 8.8 | Email fails (bad SMTP config) → error logged, stream continues | |

### 9. SMS Alerts — NOT YET TESTED

| # | Test Case | Status |
|---|-----------|--------|
| 9.1 | SMS triggered on confirmed event → correct phones targeted | |
| 9.2 | SMS message matches event type | |
| 9.3 | SMS failure does not block the system | |

### 10. Admin Dashboard — NOT YET TESTED

| # | Test Case | Status |
|---|-----------|--------|
| 10.1 | Dashboard shows correct event count | |
| 10.2 | Dashboard shows correct alert count | |
| 10.3 | Dashboard shows correct caregiver count | |
| 10.4 | Delete individual event → removed from list, image file deleted | |
| 10.5 | Delete all events → all cleared, all image files deleted | |
| 10.6 | Delete individual alert → removed from list | |
| 10.7 | Delete all alerts → all cleared | |

### 11. Caregiver Dashboard — NOT YET TESTED

| # | Test Case | Status |
|---|-----------|--------|
| 11.1 | Dashboard shows correct event count | |
| 11.2 | Caregiver name displayed in sidebar and navbar | |
| 11.3 | No delete buttons on events → read-only view | |
| 11.4 | No start/stop buttons on livestream → view-only mode | |

### 12. UI / Responsiveness — NOT YET TESTED

| # | Test Case | Status |
|---|-----------|--------|
| 12.1 | All pages render on desktop (1920x1080) → no overflow | |
| 12.2 | All pages render on mobile (375px width) → sidebar collapses, cards stack | |
| 12.3 | Sidebar toggle works on mobile | |
| 12.4 | Empty states display correctly → placeholder messages shown | |
