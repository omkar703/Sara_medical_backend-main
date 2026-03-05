# AI Integration Guide: Sara Medical Platform

This document outlines the end-to-end integration flow for the Sara Medical AI Chat feature. The underlying AI system has been extended to support **persistent, ChatGPT-style chat sessions** scoped to specific doctor-patient relationships, along with strict **medical AI guardrails**.

## 1. System Architecture

The AI module implements a highly secure, stateful RAG (Retrieval-Augmented Generation) pipeline:

```
Doctor Query 
  ↓
AIChatService (Backend)
  ↓
Load Chat Session History (Conversation Memory)
  ↓
RAG Retrieval (Titan Vector Search on MinIO documents + SOAP Notes)
  ↓
Apply Medical Guardrails (Hallucination Prevention, Source Citations)
  ↓
Claude 3.5 Sonnet (via AWS Bedrock)
  ↓
Structured Evidence-Based Medical Response (Streamed via SSE)
```

**Guardrail Protections Included:**
- **Evidence-Grounded**: The AI will absolutely not hallucinate. If evidence does not exist in the patient's records, it returns a fallback response.
- **Source Citations**: Every claim the AI makes cites the specific medical document.
- **Confidence Scoring**: Returned dynamically (`High`, `Medium`, `Low`) based on document context.
- **Context Limits**: Prompts are restricted to Top 5 chunks, Top 3 SOAP notes, and the last 10 session messages.

---

## 2. API Endpoints Documentation

*Note: All endpoints require a standard Bearer token (`Authorization: Bearer <token>`) from an authenticated doctor. The doctor must also have an active Data Access Grant (`ai_access_permission = true`) for the targeted patient.*

### 3.1. Create Chat Session
**`POST /api/v1/doctor/ai/chat/session`**

Creates a new blank conversation thread. If `title` is not provided, the database will save it as `null` initially, and the backend will automatically generate a title upon the first sent message.

**Sample Input Data (Request Body):**
```json
{
  "patient_id": "4855ed79-e3bb-4187-82b2-a8bc046113b8",
  "title": "Initial Lab Review" 
}
```

**Sample Output Data (Response Body):**
```json
{
  "session_id": "8c2726b1-0509-48e2-b61d-c7754ed92313",
  "title": "Checkup Review",
  "patient_id": "4855ed79-e3bb-4187-82b2-a8bc046113b8",
  "created_at": "2026-03-05T11:35:02.018398+00:00",
  "updated_at": "2026-03-05T11:35:02.018398+00:00"
}
```

---

### 3.2. List Chat Sessions
**`GET /api/v1/doctor/ai/chat/sessions?patient_id={uuid}`**

Fetches all past conversation sessions a doctor has had regarding a specific patient. Ordered starting from the most recently updated. Ideal for populating the sidebar history.

**Sample Input Data (Query Parameters):**
- `patient_id` = `4855ed79-e3bb-4187-82b2-a8bc046113b8`

**Sample Output Data (Response Body):**
```json
[
  {
    "session_id": "8c2726b1-0509-48e2-b61d-c7754ed92313",
    "title": "Checkup Review",
    "updated_at": "2026-03-05T11:35:08.449171+00:00"
  },
  {
    "session_id": "6811c91e-0de9-417d-84a7-5114aee11c4f",
    "title": "Allergy Investigation",
    "updated_at": "2026-03-05T11:25:45.094765+00:00"
  }
]
```

---

### 3.3. Get Chat History
**`GET /api/v1/doctor/ai/chat/session/{session_id}`**

Loads the entire stored message history of a specific session (useful when opening a historical chat window). 

**Sample Input Data (Path Parameter):**
- `session_id` = `8c2726b1-0509-48e2-b61d-c7754ed92313`

**Sample Output Data (Response Body):**
```json
{
  "session_id": "8c2726b1-0509-48e2-b61d-c7754ed92313",
  "title": "Checkup Review",
  "patient_id": "4855ed79-e3bb-4187-82b2-a8bc046113b8",
  "messages": [
    {
      "id": "47018177-39de-42dc-8435-2e202f5bc620",
      "role": "doctor",
      "content": "Please summarize the latest lab results.",
      "sources": null,
      "confidence": null,
      "created_at": "2026-03-05T11:35:02.064923+00:00"
    },
    {
      "id": "9ecef98f-253e-4283-9ddb-bd30dc15e496",
      "role": "assistant",
      "content": "**Patient Summary:** Patient shows improved laboratory values between April and November 2025 during treatment for community-acquired pneumonia.\n\n**Key Findings:**\n- Current glucose: 158 (improved from 198)\n- Current CRP: 4.3 (improved from 12.4)\n\n**Clinical Evidence:**\n- [Source: Synthetic_Patient_02_es.pdf | Page: 13]\n\n**Answer:** The most recent labs show improvement in both glucose and CRP levels.\n\n**Confidence:** High",
      "sources": ["TIER_1_TEXT"],
      "confidence": "high",
      "created_at": "2026-03-05T11:35:02.064923+00:00"
    }
  ]
}
```

---

### 3.4. Send Message (Streaming)
**`POST /api/v1/doctor/ai/chat/message`**

Processes the message dynamically, retrieves RAG context, and responds incrementally with Server-Sent Events (SSE). It automatically saves both the user's message and the assistant's AI response to the database at the end of the stream.

**Sample Input Data (Request Body):**
```json
{
  "session_id": "8c2726b1-0509-48e2-b61d-c7754ed92313",
  "patient_id": "4855ed79-e3bb-4187-82b2-a8bc046113b8",
  "message": "Please summarize the latest lab results.",
  "document_id": null 
}
```
*(Note: `document_id` is optional and restricts RAG retrieval strictly to one specific document if provided).*

**Sample Output Data (Streamed `text/event-stream` format):**
*(The response buffers text tokens one by one. The fully combined payload string will resemble the following Markdown structure)*:

```markdown
**Patient Summary:** 
Patient shows improved laboratory values between April and November 2025 during treatment for community-acquired pneumonia.

**Key Findings:**
- Current glucose: 158 (improved from 198)
- Current CRP: 4.3 (improved from 12.4)
- Previous values from 2025-04-30:
  * Glucose: 198
  * CRP: 12.4

**Clinical Evidence:**
- [Source: Synthetic_Patient_02_es.pdf | Page: 13] - Contains lab value comparisons

**Answer:** 
The most recent labs from November 2025 show improvement in both glucose and CRP levels compared to April 2025, with glucose decreasing from 198 to 158 and CRP decreasing from 12.4 to 4.3.

**Confidence:** High
```

---

### 3.5. Extract Doctor Credentials (Vision OCR)
**`POST /api/v1/doctor/extract-credentials`**

Uses Claude Vision via Bedrock to automatically extract doctor credentials from an uploaded certificate image. It accepts `image/jpeg`, `image/jpg`, `image/png`, and `image/webp`. Maximum file size is 10MB.

**Sample Request (Multipart Form-Data):**
```bash
curl -X POST http://localhost:8000/api/v1/doctor/extract-credentials \
  -H "Authorization: Bearer <token>" \
  -F "certificate_image=@MBBS-DEGREE-rotated-1.jpg"
```

**Sample Output Data (JSON Response) for MBBS:**
```json
{
  "universityName": "Maharashtra University of Health Sciences, Nashik",
  "doctorName": "PATIL VIRENDRA ASHOKRAO",
  "degreeName": "Bachelor of Medicine & Bachelor of Surgery",
  "licenseNumber": "PRN 0104140566",
  "issueDate": "25th May 2009"
}
```

**Sample Output Data (JSON Response) for MD:**
```json
{
  "universityName": "Maharashtra University of Health Sciences, Nashik",
  "doctorName": "Patil Virendra Ashokrao",
  "degreeName": "Doctor of Medicine (General Medicine)",
  "licenseNumber": "PRN 2112112657",
  "issueDate": "5th October, 2012"
}
```

---

## 3. Frontend Integration Guide

To integrate this effectively on the web client:

### 1. View Layout
Create a standard ChatGPT-like messaging app layout. 
- **Sidebar (Left Panel):** Call **`GET /api/v1/doctor/ai/chat/sessions?patient_id={x}`** to render the session list.
- **New Chat Button:** When clicked, fire **`POST /api/v1/doctor/ai/chat/session`** to initialize a new session.
- **Main Chat Window:** Call **`GET /api/v1/doctor/ai/chat/session/{y}`** when a sidebar list item is clicked. Iterate over the `messages` array and render text bubbles according to `"role"`.

### 2. Handling SSE Streams
Since Claude is streaming responses, a standard `axios.post()` will not visualize properly for UX until the very end. You must implement a parser that reads text chunks continuously using the browser's native `fetch` API (`ReadableStream`) or an event source parser. Look for packages like `@microsoft/fetch-event-source` if using React/Next.js.

### 3. Markdown Rendering
The streamed AI outputs adhere to strict Markdown structuring (with `**` bold headers and bullet points). The UI should pass this continuous string into a Markdown parser (e.g., `react-markdown`) so it displays cleanly to the clinician.

### 4. Guardrails & Refusals (Fallback)
If a question falls outside the bounds of the patient's records or breaks medical safety bounds (e.g. asking to prescribe unrelated unrecorded medicine, or asking general non-medical facts), the backend AI intercepts it entirely without calling the LLM API, quickly streaming back:  
*"I cannot find sufficient information in the patient's medical records to answer this question."*

No special UI handling is needed—simply let the Markdown parser render the refusal message as a standard Assistant bubble.

---

## 4. Security Summary

1. **Role Access:** Only users with `role = "doctor"` are permitted.
2. **Access Rights:** API automatically bounces requests lacking backend Data Access Grant permission tables (`ai_access_permission = true`).
3. **Data Localization:** Sessions naturally query and store messages entirely isolated per specific doctor and specific patient boundaries.
4. **No Side-channel Logic:** Confidence scores are pre-computed locally, reducing the risk of hallucination overrides. Empty embedding results skip the LLM entirely, saving cost and guaranteeing safety.
