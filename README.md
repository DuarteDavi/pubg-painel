# Survival Macro - Access Control Panel

Admin panel for managing licenses and client access to Survival Macro.

## Structure

```
survival-panel/
├── backend/      # FastAPI + SQLAlchemy
├── frontend/     # React + Vite
└── README.md
```

## Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python app/scripts/hash_password.py
# Update .env with the password hash and secure JWT_SECRET
python main.py
```

Server runs at `http://localhost:3014`

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend runs at `http://localhost:6666`

## Architecture

### Backend
- **FastAPI** - API framework
- **SQLAlchemy** - ORM
- **SQLite** - Development database (PostgreSQL for production)
- **JWT** - Token-based authentication
- **BCrypt** - Password hashing

### Frontend
- **React** - UI library
- **Vite** - Build tool
- **React Router** - Navigation
- **Axios** - HTTP client
- **CSS** - Styling (no external CSS framework, all custom)

## Security Features

✅ Backend validation for all operations  
✅ No sensitive data in localStorage (only token)  
✅ JWT with expiration  
✅ Refresh token rotation  
✅ Rate limiting on login  
✅ Audit logging (never logs passwords/tokens)  
✅ Session management in database  
✅ Device hashing (never stores raw hardware IDs)  
✅ CORS restricted to frontend origin  
✅ Secrets in .env (never hardcoded)  

## API Endpoints

See `backend/README.md` for full API documentation.

### Authentication (Public)
- `POST /api/auth/login` - Client login
- `POST /api/auth/verify` - Verify session
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - Logout

### Admin (Protected)
- `POST /api/admin/login` - Admin login
- `GET /api/admin/dashboard` - Stats
- `GET /api/admin/clients` - List clients
- `POST /api/admin/clients` - Create client
- ... (see backend/README.md for full list)

## Development

### Backend Tests

```bash
cd backend
pytest
```

### Deployment

1. **Database Migration**
   - PostgreSQL in production
   - Run migrations with Alembic

2. **Environment**
   - Set `ENVIRONMENT=production`
   - Set strong `JWT_SECRET`
   - Set `DEBUG=False`

3. **Frontend Build**
   ```bash
   cd frontend
   npm run build
   # Deploy dist/ to web server
   ```

4. **Backend Deployment**
   - Use Gunicorn + Nginx
   - SSL certificates
   - Configure CORS for production domain

5. **Domain & DNS**
   - Point `survival.techduarte.tech` to server
   - Configure SSL

## Next Steps

- [ ] PostgreSQL setup for production
- [ ] Nginx reverse proxy configuration
- [ ] SSL certificate setup
- [ ] 2FA for admin (future version)
- [ ] Audit log export functionality
- [ ] Mass client operations
- [ ] Device fingerprinting improvements

## Files Overview

### Backend Core
- `app/models.py` - Database models
- `app/schemas.py` - Pydantic validation
- `app/auth.py` - Authentication & hashing
- `app/database.py` - Database configuration

### Backend Routes
- `app/routes/auth.py` - Client authentication (public)
- `app/routes/admin.py` - Admin management (protected)

### Frontend Pages
- `src/pages/Login.jsx` - Admin login
- `src/pages/Dashboard.jsx` - Stats dashboard
- `src/pages/ClientList.jsx` - Client list + create
- `src/pages/ClientDetail.jsx` - Client management

### Utilities
- `src/api/client.js` - API calls
- `src/context/AuthContext.jsx` - Authentication state
- `src/components/Header.jsx` - Navigation
- `src/components/Modal.jsx` - Reusable modal

## Configuration

### Backend .env

```
ENVIRONMENT=development
DATABASE_URL=sqlite:///./survival_macro.db
ADMIN_LOGIN=admin
ADMIN_PASSWORD_HASH=<hash from password script>
JWT_SECRET=<random string>
CORS_ORIGINS=http://localhost:6666
DEBUG=True
```

### Frontend .env

```
VITE_API_URL=http://localhost:3014
VITE_ENVIRONMENT=development
```

## Admin Credentials

Generated via `python app/scripts/hash_password.py`

Default login: `admin` (changeable in .env)

## License

Private project - Survival Macro
