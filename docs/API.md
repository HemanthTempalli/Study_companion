# API Reference

Base URL: `http://localhost:8000`

## Authentication

### POST `/api/auth/register`
Register a new user.
```json
Request:  { "email": "...", "password": "...", "full_name": "..." }
Response: { "access_token": "...", "user": {...} }
```

### POST `/api/auth/login`
```json
Request:  { "email": "...", "password": "..." }
Response: { "access_token": "...", "user": {...} }
```

### GET `/api/auth/me`
Returns current user profile. **Auth required.**

---

## Spaces

### POST `/api/spaces/`
Create a new space. **Auth required.**
```json
Request: { "name": "CS 101", "description": "...", "color": "#6366f1" }
```

### GET `/api/spaces/`
List all user's spaces. **Auth required.**

### GET `/api/spaces/{id}`
Get space detail. **Auth required.**

### PUT `/api/spaces/{id}`
Update space. **Auth required.**

### DELETE `/api/spaces/{id}`
Delete space and all projects within. **Auth required.**

---

## Projects

### POST `/api/projects/`
Create a project within a space. **Auth required.**
```json
Request: { "name": "ML Basics", "space_id": "uuid", "learning_goal": "..." }
```

### GET `/api/projects/`
List projects, optionally filtered by `?space_id=...`. **Auth required.**

### GET `/api/projects/{id}`
Get project detail. **Auth required + ownership.**

### GET `/api/projects/{id}/dashboard`
Get project dashboard with mastery summary, quiz stats, recommendations, and recent activity. **Auth required + ownership.**

---

## Materials

### POST `/api/projects/{id}/materials/`
Upload a PDF file (multipart form data). **Auth required + ownership.**

### GET `/api/projects/{id}/materials/`
List materials with processing status. **Auth required + ownership.**

### DELETE `/api/projects/{id}/materials/{material_id}`
Delete material and associated chunks. **Auth required + ownership.**

### POST `/api/projects/{id}/materials/{material_id}/retry`
Retry failed material processing. **Auth required + ownership.**

---

## AI Tutor

### POST `/api/projects/{id}/tutor/chat`
Send a message and get a RAG-grounded response. **Auth required + ownership.**
```json
Request:  { "message": "What is gradient descent?", "conversation_id": "uuid or null" }
Response: { "answer": "...", "citations": [...], "has_sufficient_evidence": true, "conversation_id": "uuid" }
```

### GET `/api/projects/{id}/tutor/conversations`
List conversations. **Auth required + ownership.**

### GET `/api/projects/{id}/tutor/conversations/{conv_id}/messages`
Get messages in a conversation. **Auth required + ownership.**

---

## Quiz

### POST `/api/projects/{id}/quiz/generate`
Generate an adaptive quiz. **Auth required + ownership.**
```json
Request:  { "num_questions": 5, "difficulty": null }
Response: { "id": "uuid", "questions": [...] }
```

### POST `/api/projects/{id}/quiz/{quiz_id}/submit`
Submit answers and get evaluation. **Auth required + ownership.**
```json
Request:  [{ "question_id": "uuid", "user_answer": "..." }, ...]
Response: { "score": 80, "question_results": [...], "mastery_updates": [...] }
```

### GET `/api/projects/{id}/quiz/history`
Get past quiz attempts. **Auth required + ownership.**

---

## Mastery & Growth

### GET `/api/projects/{id}/mastery`
Get concept mastery records with trends. **Auth required + ownership.**

### GET `/api/projects/{id}/growth`
Get growth analysis (improving/stable/needs attention). **Auth required + ownership.**

---

## Recommendations

### POST `/api/projects/{id}/recommendations/generate`
Generate an AI-powered recommendation. **Auth required + ownership.**

### GET `/api/projects/{id}/recommendations/`
List recommendations. **Auth required + ownership.**

### POST `/api/projects/{id}/recommendations/{rec_id}/dismiss`
Dismiss a recommendation. **Auth required + ownership.**

---

## Analytics

### GET `/api/projects/{id}/analytics`
Project-level analytics. **Auth required + ownership.**

### GET `/api/admin/analytics`
Global analytics. **Admin required.**

---

## Admin

### GET `/api/admin/users`
List all users with activity stats. **Admin required.**

### GET `/api/admin/users/{user_id}/journey`
Inspect a user's learning journey. **Admin required.**

### GET `/api/admin/health`
System health check. **Admin required.**

### GET `/api/admin/ai-logs`
AI usage logs with filtering. **Admin required.**

### GET `/api/admin/jobs`
Background job monitoring. **Admin required.**

### POST `/api/admin/make-admin/{user_id}`
Promote user to admin. **Admin required.**

---

## Health

### GET `/api/health`
Public health check endpoint. No auth required.
```json
Response: { "status": "healthy", "service": "AI Study Companion" }
```
