# Survival Macro - Admin Panel Frontend

React + Vite frontend for the Survival Macro access control panel.

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Frontend runs at `http://localhost:6666`

## Pages

- **Login** (`/login`) - Admin authentication
- **Dashboard** (`/`) - Stats and overview
- **Clients** (`/clients`) - List, search, and create clients
- **Client Detail** (`/clients/:id`) - Manage individual client

## Features

- Dark industrial theme
- Responsive design
- Real-time client management
- License renewal
- Device management
- Session management
- Search and filtering
- Pagination

## Build

```bash
npm run build
```

Output in `dist/`

## Environment

- `VITE_API_URL` - Backend API URL (default: http://localhost:3014)
- `VITE_ENVIRONMENT` - Environment name

## Security

- ✅ No hardcoded credentials
- ✅ Tokens stored only in memory/sessionStorage (never localStorage for sensitive data)
- ✅ Session validation on every request
- ✅ Auto redirect to login on 401
- ✅ Rate limiting on frontend (real limiting on backend)

## Styling

Custom CSS with industrial dark theme:
- Background: #0a0a0a
- Primary: #c84c2c (rust red)
- Secondary: #c9a961 (industrial yellow)
- Text: #e8e4d0 (beige)

No external CSS framework - all custom.
