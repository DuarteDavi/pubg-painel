# Survival Macro - Backend API

Admin panel backend for managing licenses and access control.

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create `.env` file:

```bash
cp .env.example .env
```

3. Generate admin password hash:

```bash
python app/scripts/hash_password.py
```

Copy the output and update `ADMIN_PASSWORD_HASH` in `.env`.

4. Update `.env` with secure values:

```
ADMIN_LOGIN=admin
ADMIN_PASSWORD_HASH=<output from step 3>
JWT_SECRET=<generate a secure random string>
```

### Running the Server

Development:

```bash
python main.py
```

Production:

```bash
uvicorn main:app --host 0.0.0.0 --port 3014
```

The API will be available at `http://localhost:3014`

Swagger docs (development only): `http://localhost:3014/docs`

## API Endpoints

### Authentication (Public)

- `POST /api/auth/login` - Client login
- `POST /api/auth/verify` - Verify session
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - Logout

### Admin (Protected)

- `POST /api/admin/login` - Admin login
- `POST /api/admin/logout` - Admin logout
- `GET /api/admin/dashboard` - Dashboard stats
- `GET /api/admin/clients` - List clients
- `POST /api/admin/clients` - Create client
- `GET /api/admin/clients/{id}` - Get client
- `PUT /api/admin/clients/{id}` - Update client
- `POST /api/admin/clients/{id}/reset-password` - Reset password
- `POST /api/admin/clients/{id}/renew-license` - Renew license
- `POST /api/admin/clients/{id}/revoke-sessions` - Revoke sessions
- `GET /api/admin/clients/{id}/devices` - List devices
- `DELETE /api/admin/clients/{id}/devices/{device_id}` - Remove device
- `POST /api/admin/clients/{id}/activate` - Activate client
- `POST /api/admin/clients/{id}/deactivate` - Deactivate client
- `DELETE /api/admin/clients/{id}` - Delete client

## Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT tokens with expiration
- ✅ Refresh token rotation
- ✅ Rate limiting (5 attempts per 15 minutes)
- ✅ Session validation in database
- ✅ Audit logging (no sensitive data)
- ✅ Backend validation for all operations
- ✅ Device hashing (never store real hardware serials)
- ✅ Transaction protection for concurrent access
- ✅ CORS restricted to frontend origin
- ✅ Secrets in .env (never hardcoded)
- ✅ Admin credentials from environment variables

## Database

SQLite for development, PostgreSQL for production.

Tables:
- `products` - Available products
- `clients` - Client accounts
- `licenses` - Client licenses
- `license_devices` - Devices linked to licenses
- `client_sessions` - Active client sessions
- `admin_sessions` - Active admin sessions
- `audit_logs` - Action audit trail

## Testing

```bash
pytest
```

## Deployment

For production deployment:

1. Use PostgreSQL instead of SQLite
2. Set `ENVIRONMENT=production`
3. Set `DEBUG=False`
4. Use strong `JWT_SECRET`
5. Set up HTTPS
6. Configure backup strategy

## Next Steps

1. Deploy with PostgreSQL
2. Configure Nginx reverse proxy
3. Set up SSL certificates
4. Deploy frontend
5. Configure domain DNS
