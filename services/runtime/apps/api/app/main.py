from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router as api_v1_router
from app.api.v1.health import router as health_router

app = FastAPI(
    title="PFIOS API (Financial AI Operating System)",
    description="模块化、可治理的个人金融智能操作系统 API",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router)
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "PFIOS API v1.1.0 energized.", "docs": "/docs"}
