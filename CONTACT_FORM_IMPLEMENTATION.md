# Contact Form API - Implementation Guide

## ✅ What Has Been Built

A complete contact form submission system with:

1. **Database Model** - `ContactMessage` table in PostgreSQL
2. **API Endpoints** - 6 RESTful endpoints for form submission and admin management
3. **Email Service** - Automated email notifications to enterprise address
4. **Admin Dashboard** - Manage, read/unread, and delete messages
5. **Validation** - Input validation for all fields
6. **Documentation** - Full API documentation with examples

---

## 📁 Files Created/Modified

### New Files Created:

1. **`app/models/contact_message.py`**
   - SQLAlchemy model for contact messages
   - Defines table structure with all required fields

2. **`app/schemas/contact.py`**
   - Pydantic schemas for request/response validation
   - `ContactMessageCreate` - for form submission
   - `ContactMessageResponse` - for full message details
   - `ContactMessageListResponse` - for message listing
   - `ContactMessageSuccessResponse` - for submission success

3. **`app/services/contact_service.py`**
   - Business logic for contact message operations
   - Methods: create, get, update (read status), delete
   - Pagination and filtering support

4. **`app/api/v1/contact.py`**
   - 6 API endpoints (documented in CONTACT_FORM_API.md)
   - Public endpoint for form submission (no auth required)
   - Admin-only endpoints for management

5. **`alembic/versions/001_create_contact_messages.py`**
   - Database migration to create contact_messages table
   - Includes all necessary indexes

6. **`CONTACT_FORM_API.md`**
   - Complete API documentation
   - Frontend implementation examples
   - Configuration guide

### Files Modified:

1. **`app/api/v1/__init__.py`**
   - Added contact router import
   - Registered contact router with API

2. **`app/services/email.py`**
   - Added `send_contact_form_email()` function
   - Sends formatted HTML email to enterprise address

3. **`app/config.py`**
   - Added `ENTERPRISE_EMAIL` setting
   - Default: `enterprise@saramedico.com`

---

## 🚀 Quick Start

### Step 1: Apply Database Migration

```bash
# Navigate to project root
cd /home/nikh-on-linux/Documents/Sara_medical_backend-main

# Run migration to create table
alembic upgrade head
```

### Step 2: Set Environment Variables

Add to your `.env` file:

```bash
# Contact Form Email
ENTERPRISE_EMAIL=enterprise@saramedico.com

# OR customize to your email:
ENTERPRISE_EMAIL=contact@yourdomain.com
```

### Step 3: Verify Endpoints are Loaded

Restart your backend:

```bash
# Stop current backend
# (Ctrl+C if running locally, or stop Docker container)

# Start backend
python -m uvicorn app.main:app --reload

# Verify in Swagger UI:
# Visit: http://localhost:8000/docs
# Look for "Contact" tag in the API list
```

---

## 📝 API Endpoints Quick Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/contact/submit` | ❌ | Submit contact form |
| GET | `/api/v1/contact/messages` | ✅ Admin | Get all messages |
| GET | `/api/v1/contact/messages/{id}` | ✅ Admin | Get single message |
| PATCH | `/api/v1/contact/messages/{id}/read` | ✅ Admin | Mark as read |
| DELETE | `/api/v1/contact/messages/{id}` | ✅ Admin | Delete message |
| GET | `/api/v1/contact/stats/unread-count` | ✅ Admin | Get unread count |

---

## 🧪 Testing the API

### 1. Test Form Submission (No Auth Required)

```bash
curl -X POST http://localhost:8000/api/v1/contact/submit \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "subject": "I need information",
    "message": "Can you tell me more about your platform?"
  }'
```

**Expected Response (201):**
```json
{
  "success": true,
  "message": "Your message has been received. We will get back to you shortly.",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. Test Admin Access - Get Messages

```bash
# First, get an admin token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your-password"
  }'

# Copy the access_token from response, then:
curl http://localhost:8000/api/v1/contact/messages \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### 3. Test Email Sending

Monitor logs while submitting form:

```bash
# In another terminal, watch logs
tail -f logs/saramedico.log | grep -i "contact\|email"

# Then submit form in first terminal
# Check logs for:
# - "Contact message created successfully"
# - "Email sent to enterprise@saramedico.com"
# - Any SMTP errors
```

---

## 📧 Email Configuration

### For Gmail

```bash
# In .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password  # NOT your regular password!
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Saramedico
SMTP_TLS=true
SMTP_SSL=false
ENTERPRISE_EMAIL=enterprise@saramedico.com
```

**Get App Password:** https://myaccount.google.com/apppasswords

### For Other SMTP Providers

Update `SMTP_HOST` and `SMTP_PORT` accordingly.

---

## 🔍 Verify Installation

### Check if Model is Registered

```python
# In Python shell
from app.models.contact_message import ContactMessage
print(ContactMessage.__tablename__)  # Should print: contact_messages
```

### Check if Endpoint is Loaded

```bash
# Visit Swagger UI
# http://localhost:8000/docs

# Search for "contact" tag
# Should see 6 endpoints listed
```

### Check if Schema Works

```python
from app.schemas.contact import ContactMessageCreate
form = ContactMessageCreate(
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    phone="+1-555-123-4567",
    subject="Test",
    message="Test message"
)
print(form.model_dump_json())
```

---

## 🎯 Frontend Integration

### React Example - Simple Form

```javascript
import React, { useState } from 'react';
import axios from 'axios';

export const ContactForm = () => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/contact/submit',
        {
          firstName: e.target.firstName.value,
          lastName: e.target.lastName.value,
          email: e.target.email.value,
          phone: e.target.phone.value,
          subject: e.target.subject.value,
          message: e.target.message.value,
        }
      );

      if (response.status === 201) {
        setSuccess(true);
        e.target.reset();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error submitting form');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="firstName" required placeholder="First Name" />
      <input name="lastName" required placeholder="Last Name" />
      <input name="email" type="email" required placeholder="Email" />
      <input name="phone" required placeholder="Phone" />
      <input name="subject" required placeholder="Subject" />
      <textarea name="message" required placeholder="Message"></textarea>
      
      <button type="submit" disabled={loading}>
        {loading ? 'Submitting...' : 'Submit'}
      </button>

      {success && <p style={{ color: 'green' }}>Message sent successfully!</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </form>
  );
};
```

### React Example - Admin Dashboard

```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

export const AdminContactDashboard = ({ token }) => {
  const [messages, setMessages] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    fetchMessages();
    fetchUnreadCount();
  }, []);

  const fetchMessages = async () => {
    try {
      const response = await axios.get(
        'http://localhost:8000/api/v1/contact/messages?unread_only=false',
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const response = await axios.get(
        'http://localhost:8000/api/v1/contact/stats/unread-count',
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  const handleMarkAsRead = async (messageId) => {
    try {
      await axios.patch(
        `http://localhost:8000/api/v1/contact/messages/${messageId}/read`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchMessages();
      fetchUnreadCount();
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  const handleDelete = async (messageId) => {
    if (window.confirm('Delete this message?')) {
      try {
        await axios.delete(
          `http://localhost:8000/api/v1/contact/messages/${messageId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        fetchMessages();
        fetchUnreadCount();
      } catch (error) {
        console.error('Error deleting message:', error);
      }
    }
  };

  return (
    <div>
      <h2>Contact Messages ({unreadCount} unread)</h2>
      <table>
        <thead>
          <tr>
            <th>From</th>
            <th>Email</th>
            <th>Subject</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {messages.map((msg) => (
            <tr key={msg.id}>
              <td>{msg.first_name} {msg.last_name}</td>
              <td>{msg.email}</td>
              <td>{msg.subject}</td>
              <td>{msg.read ? '✅ Read' : '🔴 Unread'}</td>
              <td>
                {!msg.read && (
                  <button onClick={() => handleMarkAsRead(msg.id)}>Mark Read</button>
                )}
                <button onClick={() => handleDelete(msg.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## 🐛 Troubleshooting

### Issue: Module Not Found Error

```
ModuleNotFoundError: No module named 'app.api.v1.contact'
```

**Solution:** Make sure you restarted the server after creating the file.

### Issue: Email Not Sending

Check:
1. SMTP configuration in `.env` (especially `SMTP_PASSWORD`)
2. ENTERPRISE_EMAIL is set
3. Logs: `tail -f logs/saramedico.log | grep -i email`

### Issue: Database Error

```
ProgrammingError: relation "contact_messages" does not exist
```

**Solution:** Run migration: `alembic upgrade head`

### Issue: 404 on Contact Endpoint

**Solution:** Verify:
1. Router is imported in `app/api/v1/__init__.py`
2. Router is registered: `api_router.include_router(contact.router)`
3. Server is restarted

---

## 📊 Database Schema Reference

```sql
CREATE TABLE contact_messages (
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

-- Indexes for performance
CREATE INDEX idx_contact_messages_first_name ON contact_messages(first_name);
CREATE INDEX idx_contact_messages_email ON contact_messages(email);
CREATE INDEX idx_contact_messages_read ON contact_messages(read);
CREATE INDEX idx_contact_messages_created_at ON contact_messages(created_at);
```

---

## ✨ Features Implemented

- ✅ Public form submission (no auth required)
- ✅ Email validation
- ✅ Phone validation (7-20 characters)
- ✅ Subject & message length validation (1-5000 chars)
- ✅ Automatic email to enterprise address
- ✅ Database persistence
- ✅ Admin-only message management
- ✅ Read/unread status tracking
- ✅ Message deletion capability
- ✅ Unread count statistics
- ✅ Pagination support
- ✅ Comprehensive error handling
- ✅ HIPAA-compliant secure storage

---

## 📞 Support

For any issues or questions:

1. Check `CONTACT_FORM_API.md` for detailed documentation
2. Review error logs: `logs/saramedico.log`
3. Test with Swagger UI: `http://localhost:8000/docs`
4. Check `.env` configuration

---

## 🎉 You're All Set!

The Contact Form API is ready to use. Start by:

1. Running the migration
2. Setting up `.env` variables
3. Restarting the backend
4. Testing with Swagger UI or cURL
5. Integrating with your frontend

Happy coding! 🚀
