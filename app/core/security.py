from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

security = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    if settings.app_env == "development":
        return "dev-mode"
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization")
    if credentials.credentials != settings.secret_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials.credentials
