# API Handbook: AI Access Approval via Notifications

This document outlines the end-to-end API flow for the **AI Access Request & Approval** feature. This allows doctors to request AI-specific data access from patients, and allows patients to approve or reject these requests directly from their notification center.

## Overview Flow

1.  **Doctor** requests AI access for a specific patient.
2.  **Patient** receives a real-time notification containing a `grant_id` and `action_metadata`.
3.  **Patient** clicks "Approve" (or "Reject") in the UI.
4.  **Frontend** calls the notification-specific approval/rejection API.
5.  **Doctor** receives a notification that their request was approved/rejected.

---

## 1. Request AI Access (Doctor Side)

**Endpoint:** `POST /api/v1/permissions/request`  
**Role:** Doctor

### Request
```json
{
  "patient_id": "1996ea3f-64e6-4f37-822f-1adf636e2e17",
  "reason": "Need AI to generate SOAP note for today's visit"
}
```

### Response (200 OK)
```json
{
  "id": "b53843d3-0032-47f2-825b-cd1a2c23e361",
  "patient_id": "1996ea3f-64e6-4f37-822f-1adf636e2e17",
  "doctor_id": "1478be71-c3f7-4037-8b4f-cb9c0f1e2d3f",
  "status": "pending",
  "ai_access_permission": true,
  "is_active": false
}
```

---

## 2. Fetch Notifications (Patient Side)

**Endpoint:** `GET /api/v1/notifications`  
**Role:** Patient

The notification object now includes two critical fields for the frontend:
- `grant_id`: Link to the pending access request.
- `action_metadata`: Contains contextual hints for rendering buttons (e.g., doctor ID, reason, and allowed actions).

### Response Example
```json
[
  {
    "id": "13b9d6b2-d05f-497e-8f0f-05b59a3311b7",
    "type": "access_requested",
    "title": "AI Data Access Request",
    "message": "A doctor has requested permission to use AI to analyze your medical records. You can approve or reject this request.",
    "is_read": false,
    "action_url": "/settings/permissions",
    "grant_id": "b53843d3-0032-47f2-825b-cd1a2c23e361",
    "action_metadata": {
      "grant_id": "b53843d3-0032-47f2-825b-cd1a2c23e361",
      "doctor_id": "1478be71-c3f7-4037-8b4f-cb9c0f1e2d3f",
      "reason": "Need AI to generate SOAP note for today's visit",
      "actions": ["approve", "reject"]
    },
    "created_at": "2026-03-06T17:34:21Z"
  }
]
```

---

## 3. Approve AI Access (Patient Side)

**Endpoint:** `POST /api/v1/notifications/{notification_id}/approve-ai-access`  
**Role:** Patient

Calling this endpoint will:
- Set the linked `DataAccessGrant` to `status: "active"`.
- Set `ai_access_permission: true`.
- Mark the notification as **read**.
- Notify the doctor of the approval.

### Request URL (Example)
`POST /api/v1/notifications/13b9d6b2-d05f-497e-8f0f-05b59a3311b7/approve-ai-access`

### Response (200 OK)
```json
{
  "status": "approved",
  "message": "AI access approved. The doctor has been notified.",
  "grant_id": "b53843d3-0032-47f2-825b-cd1a2c23e361",
  "doctor_id": "1478be71-c3f7-4037-8b4f-cb9c0f1e2d3f"
}
```

---

## 4. Reject AI Access (Patient Side)

**Endpoint:** `POST /api/v1/notifications/{notification_id}/reject-ai-access`  
**Role:** Patient

Calling this endpoint will:
- Set the linked `DataAccessGrant` to `status: "revoked"`.
- Mark the notification as **read**.
- Notify the doctor of the rejection.

### Request URL (Example)
`POST /api/v1/notifications/604c7da9-906d-42ee-a461-a9ad4e735b8d/reject-ai-access`

### Response (200 OK)
```json
{
  "status": "rejected",
  "message": "AI access request rejected. The doctor has been notified.",
  "grant_id": "2437c8cb-c3de-4638-bd94-aced1d8c1a95",
  "doctor_id": "1478be71-c3f7-4037-8b4f-cb9c0f1e2d3f"
}
```

---

## Summary for Frontend Developers

1.  **Check for `type == "access_requested"`** in the notification list.
2.  **Display Buttons**: If `action_metadata.actions` contains `"approve"` and `"reject"`, render the action buttons in the notification card.
3.  **Call Action Endpoint**: When a button is clicked, use the notification's `id` (the notification GUID, not the grant ID) to call the `approve` or `reject` endpoint.
4.  **Real-time Update**: The doctor receives a notification once the status is updated.
