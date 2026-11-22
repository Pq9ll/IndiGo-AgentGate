# Prompts Used for IndiGo Agent Gatekeeper Prototype
**Student Enrolment Number:** PGD202564690  
**Coding Tool Used:** Google Antigravity  

## Prompt 1: Initial Web App & Rule Engine Setup
Create a simple, clean Python web app using Flask called "IndiGo Agent Gatekeeper" in a single file `app.py` with Enrolment Number "PGD202564690" at the top, `agents.json`, `audit_log.csv`, and 7 sequential rules (Unknown Agent, Revoked Agent, Read-Only view fares, Booking <= ₹15,000, Booking > ₹15,000, Change <= ₹5,000, Refund).

## Prompt 2: Locating Project Files
Show me the full folder path where `app.py` is saved.

## What I Checked and Verified Myself
1. Verified in `app.py` that Rule 1 (Unknown) and Rule 2 (Revoked) run before `view fares`.
2. Verified in `agents.json` that clicking Revoke saves the exact date and time in `revoked_at`.
