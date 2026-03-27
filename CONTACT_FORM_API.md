# Contact Form API Documentation

## Overview

The Contact Form API allows visitors and users to submit contact messages through your application. The system automatically:
1. **Stores the message** in the database
2. **Sends a formatted email** to `enterprise@saramedico.com`
3. **Tracks read/unread status** for admin management

---

## Database Schema

### ContactMessage Table

```sql
CREATE TABLE contact_messages (
    id UUID PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Indexes:**
- `first_name` - For searching by sender name
- `email` - For finding messages from specific email
- `read` - For filtering unread messages
- `created_at` - For sorting by date

---

## API Endpoints

### 1. Submit Contact Form
**POST** `/api/v1/contact/submit`

#### Request Body
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com",
  "phone": "+1-555-123-4567",
  "subject": "Inquiry about our services",
  "message": "I would like to know more about your medical platform..."
}
```

#### Response (Success - 201)
```json
{
  "success": true,
  "message": "Your message has been received. We will get back to you shortly.",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Response (Error - 400)
```json
{
  "detail": "Invalid email format"
}
```

**Field Validation:**
| Field | Type | Constraints |
|-------|------|-------------|
| `firstName` | String | 1-255 chars, required |
| `lastName` | String | 1-255 chars, required |
| `email` | Email | Valid email format, required |
| `phone` | String | 7-20 chars, required |
| `subject` | String | 1-255 chars, required |
| `message` | String | 1-5000 chars, required |

---

### 2. Get All Contact Messages (Admin Only)
**GET** `/api/v1/contact/messages`

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | Integer | 0 | Number of records to skip (pagination) |
| `limit` | Integer | 10 | Maximum records to return |
| `unread_only` | Boolean | false | Filter to only unread messages |

#### Response (200)
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "subject": "Inquiry about services",
    "read": false,
    "created_at": "2024-03-16T10:30:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "subject": "Feature Request",
    "read": true,
    "created_at": "2024-03-15T14:20:00Z"
  }
]
```

**Authentication:** Required (Admin role)

---

### 3. Get Single Contact Message (Admin Only)
**GET** `/api/v1/contact/messages/{message_id}`

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `message_id` | UUID | Contact message ID |

#### Response (200)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+1-555-123-4567",
  "subject": "Inquiry about services",
  "message": "I would like to know more about your medical platform and pricing...",
  "read": false,
  "created_at": "2024-03-16T10:30:00Z",
  "updated_at": "2024-03-16T10:30:00Z"
}
```

**Authentication:** Required (Admin role)

---

### 4. Mark Message as Read (Admin Only)
**PATCH** `/api/v1/contact/messages/{message_id}/read`

#### Response (200)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+1-555-123-4567",
  "subject": "Inquiry about services",
  "message": "I would like to know more about your medical platform and pricing...",
  "read": true,
  "created_at": "2024-03-16T10:30:00Z",
  "updated_at": "2024-03-16T10:35:00Z"
}
```

**Authentication:** Required (Admin role)

---

### 5. Delete Contact Message (Admin Only)
**DELETE** `/api/v1/contact/messages/{message_id}`

#### Response (204 No Content)
No response body on success.

**Authentication:** Required (Admin role)

---

### 6. Get Unread Count (Admin Only)
**GET** `/api/v1/contact/stats/unread-count`

#### Response (200)
```json
{
  "unread_count": 3
}
```

**Authentication:** Required (Admin role)

---

## Email Notification

When a contact form is submitted, an automated email is sent to `enterprise@saramedico.com` with:

### Email Template

**Subject:** `[Contact Form] {subject} - from {sender_name}`

**Body (HTML):**
```html
From: John Doe
Email: john@example.com
Phone: +1-555-123-4567

Subject: Inquiry about our services

Message:
I would like to know more about your medical platform...
```

### Configuration

The enterprise email is configured in `.env`:

```bash
# Default value
ENTERPRISE_EMAIL=enterprise@saramedico.com

# Or customize:
ENTERPRISE_EMAIL=contact@yourdomain.com
ENTERPRISE_EMAIL=support@yourdomain.com
```

---

## Frontend Implementation Example

### React with Axios

```javascript
import axios from 'axios';

const submitContactForm = async (formData) => {
  try {
    const response = await axios.post(
      'http://backend:8000/api/v1/contact/submit',
      {
        firstName: formData.firstName,
        lastName: formData.lastName,
        email: formData.email,
        phone: formData.phone,
        subject: formData.subject,
        message: formData.message,
      }
    );

    if (response.status === 201) {
      console.log('Message submitted successfully!', response.data);
      // Show success message to user
      alert(response.data.message);
    }
  } catch (error) {
    console.error('Error submitting form:', error);
    // Show error message to user
    alert(error.response?.data?.detail || 'Failed to submit form');
  }
};
```

### React with React Query

```javascript
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';

const useSubmitContactForm = () => {
  return useMutation({
    mutationFn: (formData) =>
      axios.post('/api/v1/contact/submit', formData),
    onSuccess: (data) => {
      console.log('Message submitted:', data);
    },
    onError: (error) => {
      console.error('Failed to submit:', error);
    },
  });
};

// Usage in component:
export const ContactForm = () => {
  const { mutate, isLoading, error } = useSubmitContactForm();

  const handleSubmit = (formData) => {
    mutate(formData);
  };

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleSubmit(new FormData(e.target));
    }}>
      {/* form fields */}
      <button disabled={isLoading}>Submit</button>
      {error && <p>{error.message}</p>}
    </form>
  );
};
```

---

## Admin Dashboard Usage

### Viewing Messages

```javascript
// Get all unread messages
const getUnreadMessages = async (token) => {
  const response = await axios.get(
    'http://backend:8000/api/v1/contact/messages?unread_only=true',
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  return response.data;
};

// Get all messages with pagination
const getAllMessages = async (token, skip = 0, limit = 10) => {
  const response = await axios.get(
    `http://backend:8000/api/v1/contact/messages?skip=${skip}&limit=${limit}`,
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  return response.data;
};
```

### Marking as Read

```javascript
const markAsRead = async (messageId, token) => {
  const response = await axios.patch(
    `http://backend:8000/api/v1/contact/messages/${messageId}/read`,
    {},
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  return response.data;
};
```

### Delete Message

```javascript
const deleteMessage = async (messageId, token) => {
  await axios.delete(
    `http://backend:8000/api/v1/contact/messages/${messageId}`,
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
};
```

---

## Database Migration

To create the new table, run this migration:

```sql
CREATE TABLE IF NOT EXISTS contact_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contact_messages_first_name ON contact_messages(first_name);
CREATE INDEX idx_contact_messages_email ON contact_messages(email);
CREATE INDEX idx_contact_messages_read ON contact_messages(read);
CREATE INDEX idx_contact_messages_created_at ON contact_messages(created_at);
```

---

## Error Handling

### Validation Errors (400)
```json
{
  "detail": "ensure this value has at least 1 characters"
}
```

### Not Found (404)
```json
{
  "detail": "Contact message not found"
}
```

### Unauthorized (401)
```json
{
  "detail": "Not authenticated"
}
```

### Forbidden (403)
```json
{
  "detail": "Only admin users can view contact messages"
}
```

### Server Error (500)
```json
{
  "detail": "Failed to submit contact form. Please try again later."
}
```

---

## Features

✅ **Public Submission** - No authentication required to submit  
✅ **Email Notification** - Automatic emails to enterprise address  
✅ **Admin Dashboard** - View, read/unread, and delete messages  
✅ **Validation** - Email format and field length validation  
✅ **Database Persistence** - All messages stored for record-keeping  
✅ **Read Status Tracking** - Track which messages have been reviewed  
✅ **Pagination** - Efficient message listing for large volumes  
✅ **HIPAA Compliant** - Secure email transport and data storage  

---

## Testing

### Using cURL

```bash
# Submit form
curl -X POST http://localhost:8000/api/v1/contact/submit \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "subject": "Test Message",
    "message": "This is a test message"
  }'

# Get all messages (requires admin token)
curl http://localhost:8000/api/v1/contact/messages \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Mark as read
curl -X PATCH http://localhost:8000/api/v1/contact/messages/{message_id}/read \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

---

## Troubleshooting

### Email Not Sending

1. Check SMTP configuration in `.env`:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_FROM_EMAIL=your-email@gmail.com
   SMTP_FROM_NAME="Saramedico"
   SMTP_TLS=true
   ```

2. Check logs for SMTP errors:
   ```bash
   tail -f logs/saramedico.log | grep -i "email\|smtp"
   ```

3. Verify `ENTERPRISE_EMAIL` is set correctly in `.env`

### Database Connection Issues

1. Ensure PostgreSQL is running
2. Check `DATABASE_URL` in `.env`
3. Run migrations: `alembic upgrade head`

---

## Configuration

All configuration is done through environment variables in `.env`:

```bash
# Contact Form Email Configuration
ENTERPRISE_EMAIL=enterprise@saramedico.com

# SMTP Configuration (used for sending emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Saramedico
SMTP_TLS=true
SMTP_SSL=false
```

---

## Summary

The Contact Form API provides a complete solution for:
- ✅ Collecting visitor inquiries
- ✅ Storing messages in the database
- ✅ Notifying enterprise team via email
- ✅ Managing messages through admin dashboard
- ✅ Tracking message read status

**No authentication required to submit** → Anyone can contact you  
**Admin-only access** → Only admins can view and manage messages
