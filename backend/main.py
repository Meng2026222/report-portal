"""
价值投资门户 · 认证后端
FastAPI + GitHub OAuth + SQLite 留言板
"""
import os, jwt, time, secrets, json
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
import httpx

from database import upsert_user, get_user, update_nickname, add_comment, get_comments

# ── Config ──────────────────────────────────────────────
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
SITE_URL = os.environ.get("SITE_URL", "http://localhost:8765")
CALLBACK_URL = f"{SITE_URL}/api/auth/callback"

JWT_ALGO = "HS256"
JWT_EXPIRE_DAYS = 30

# ── App ─────────────────────────────────────────────────
app = FastAPI(title="价值投资门户 API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── OAuth ───────────────────────────────────────────────
oauth = OAuth()
oauth.register(
    name="github",
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    client_kwargs={"scope": "read:user"},
)

# ── Helpers ─────────────────────────────────────────────

def make_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": time.time() + JWT_EXPIRE_DAYS * 86400,
        "iat": time.time(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    payload = verify_token(token)
    if not payload:
        return None
    user = get_user(payload["user_id"])
    return user

async def get_github_user(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if resp.status_code != 200:
            raise HTTPException(400, "Failed to fetch GitHub user")
        data = resp.json()
        return {
            "id": str(data["id"]),
            "login": data["login"],
            "avatar_url": data.get("avatar_url", ""),
        }

# ── Auth Routes ────────────────────────────────────────

@app.get("/api/auth/github-url")
async def github_login_url():
    """返回 GitHub OAuth 授权链接"""
    state = secrets.token_urlsafe(16)
    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={CALLBACK_URL}"
        f"&scope=read:user"
        f"&state={state}"
    )
    return {"url": auth_url, "state": state}

@app.get("/api/auth/callback")
async def github_callback(code: str = "", state: str = ""):
    """GitHub OAuth 回调 — 换取 access_token → 获取用户信息 → 签发 JWT"""
    if not code:
        raise HTTPException(400, "Missing authorization code")

    # 用 code 换 access_token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": CALLBACK_URL,
            },
            headers={"Accept": "application/json"},
        )
        token_data = resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(400, f"Failed to get access token: {token_data.get('error_description', 'unknown')}")

    # 获取 GitHub 用户信息
    gh_user = await get_github_user(access_token)

    # 存入/更新本地用户
    user = upsert_user(gh_user["id"], gh_user["login"], gh_user["avatar_url"])

    # 签发 JWT
    jwt_token = make_token(user["id"])

    # Redirect back to the portal with token in URL fragment
    redirect_to = f"{SITE_URL}/?token={jwt_token}&is_new={str(user['is_new']).lower()}"
    return RedirectResponse(url=redirect_to)

@app.get("/api/me")
async def whoami(request: Request):
    """获取当前登录用户信息"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    return {
        "id": user["id"],
        "github_id": user["github_id"],
        "github_login": user["github_login"],
        "avatar_url": user["avatar_url"],
        "nickname": user["nickname"] or user["github_login"],
    }

# ── Profile ────────────────────────────────────────────

class NicknameBody(BaseModel):
    nickname: str

@app.put("/api/profile/nickname")
async def set_nickname(body: NicknameBody, request: Request):
    """设置/修改昵称"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    nick = body.nickname.strip()[:30]
    if not nick:
        raise HTTPException(400, "昵称不能为空")
    update_nickname(user["id"], nick)
    return {"ok": True, "nickname": nick}

# ── Comments ────────────────────────────────────────────

class CommentBody(BaseModel):
    company_id: str
    text: str

@app.get("/api/comments/{company_id}")
async def list_comments(company_id: str):
    """获取某企业的留言列表"""
    return get_comments(company_id)

@app.post("/api/comments")
async def create_comment(body: CommentBody, request: Request):
    """发表留言（需登录）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "请先登录后再留言")
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "留言内容不能为空")
    if len(text) > 1000:
        raise HTTPException(400, "留言内容不能超过 1000 字")

    nickname = user.get("nickname") or user["github_login"]
    avatar = user.get("avatar_url") or ""

    result = add_comment(body.company_id, user["id"], nickname, avatar, text)
    return result

# ── Health ──────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "time": time.time()}

# ── Dev runner ─────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print(f"→ 启动认证后端 (callback: {CALLBACK_URL})")
    print(f"   JWT_SECRET: {JWT_SECRET[:10]}...")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8766, reload=True)
