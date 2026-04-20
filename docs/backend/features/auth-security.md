# Authentication and Security

## Goal
Protect user data and scope memory operations to the authenticated owner.

## Endpoints
- POST /auth/register
- POST /auth/login

## Security Features
- Password hashing with bcrypt + sha256 pre-hash
- JWT bearer authentication
- Token payload validation
- User ownership checks in memory APIs

## Configuration
Set secret and token settings in environment variables:
- JWT_SECRET_KEY
- JWT_ALGORITHM
- ACCESS_TOKEN_EXPIRE_MINUTES

## Files
- backend/app/api/auth.py
- backend/app/services/auth_service.py
- backend/app/services/jwt_service.py
- backend/app/services/dependency.py
