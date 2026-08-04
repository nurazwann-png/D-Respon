import httpx
from jose import jwt, JWTError
from fastapi import HTTPException, Header
from typing import Optional

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
ALLOWED_DOMAINS = {"moe.gov.my", "iegcampus.com", "ppd.moe.gov.my", "education.gov.my"}

_certs_cache: Optional[dict] = None

async def get_google_certs():
    global _certs_cache
    if _certs_cache is None:
        async with httpx.AsyncClient() as client:
            r = await client.get(GOOGLE_CERTS_URL)
            _certs_cache = r.json()
    return _certs_cache

async def verify_google_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token tidak sah")
    token = authorization[7:]
    try:
        # Decode header to get kid
        header = jwt.get_unverified_header(token)
        certs = await get_google_certs()
        # Find matching key
        key = next((k for k in certs["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            raise HTTPException(status_code=401, detail="Kunci tidak dijumpai")
        payload = jwt.decode(token, key, algorithms=["RS256"], options={"verify_aud": False})
        email = payload.get("email", "")
        domain = email.split("@")[1] if "@" in email else ""
        if domain not in ALLOWED_DOMAINS:
            raise HTTPException(status_code=403, detail="Domain tidak dibenarkan")
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token tidak sah: {e}")
