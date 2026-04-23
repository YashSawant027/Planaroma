# Planorama - AI Wedding Assistant

Planorama is an AI-powered wedding planning assistant that manages guests, events, and RSVPs with a chat-based interface.

## Architecture

The project follows a decoupled architecture designed for performance and flexibility:

- **Frontend (React + Vite + Tailwind CSS v4)**: A premium, light-themed chat interface using Framer Motion for smooth animations and streaming responses.
- **LLM Service (FastAPI)**: The "brain" of the application. It uses a Groq-powered LLM to translate natural language into SQL queries and natural responses. It communicates directly with the SQLite database for low-latency data access.
- **Backend (Django)**: Primarily used for data management, admin interface, and initial schema definition.
- **Database (SQLite)**: A shared database file used by both Django and FastAPI for maximum performance without network overhead between services.
- **Email Service (Resend)**: Handles automated follow-up and RSVP reminder emails.

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API Key
- Resend API Key

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_key
RESEND_API_KEY=your_resend_key
```

### 3. Backend Setup (Django & FastAPI)
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Setup Django Database
cd django_backend
python manage.py migrate
```

### 4. Frontend Setup
```bash
cd frontend-react
npm install
```

## Running the Application

You need to run three separate processes:

1. **Django Admin (Optional, for UI management)**:
   ```bash
   cd django_backend
   python manage.py runserver 8000
   ```

2. **FastAPI LLM Service (Critical)**:
   ```bash
   cd fastapi_llm
   python llm_service.py
   ```

3. **Frontend (Vite)**:
   ```bash
   cd frontend-react
   npm run dev
   ```

Open `http://localhost:3000` to start chatting with Planorama.
