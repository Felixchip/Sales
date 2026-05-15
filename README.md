# Verify & Personalize Engine

A standalone extraction of the EchoTray outreach stack, featuring high-fidelity email verification and autonomous lead personalization.

## Features

### 1. 📧 Email Verification
- **Syntax Check**: RFC compliant email validation.
- **MX Record Lookup**: Verifies domain mail server availability.
- **SMTP Handshake**: Real-time probe of recipient mailbox existence.
- **Catch-all Detection**: Identifies domains that accept all mail (risky for bounce rates).
- **Disposable & Role Check**: Flags temporary emails and generic addresses (e.g., info@).
- **Heuristic Scoring**: 0-100 score indicating deliverability confidence.

### 2. 🤖 Lead Personalization
- **Autonomous Signal Crawling**: Uses Tavily to discover fresh company news, funding, hiring, and product launches.
- **ICP Scoring**: Automatically scores signals against your Ideal Customer Profile.
- **Truly Dynamic Content**: Generates non-template-based subjects and openings using actual signal data.
- **Manual Overrides**: Pin specific signals or exclude irrelevant types.
- **Prospect Discovery**: Built-in workflows for finding new leads based on high-intent signals.

## Setup

### 1. Environment Variables
Create a `.env` file with:
```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
VERIFIER_FROM_EMAIL=your-sender@example.com
```

### 2. Start Backend
```bash
python -m src.app
```
The API will run on `http://localhost:8000`.

### 3. Start Frontend (Development)
```bash
cd frontend
npm run dev
```

### 4. Production Build
The frontend is already built into `frontend/dist`. The Flask app serves it automatically at the root `/`.

## Architecture
- **Backend**: Flask (Python) + SQLite for persistence.
- **Frontend**: React + Vite + Tailwind CSS.
- **Crawlers**: Specialized modules for News, Job Boards, Press Releases, and Product Launches.
