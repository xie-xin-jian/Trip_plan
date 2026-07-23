"""FastAPI主应用"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..config import get_settings, validate_config, print_config
from ..database import Base, engine
from .routes import trip, poi, map as map_routes, auth_routes, trip_langgraph

# 获取配置
settings = get_settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于LangGraph和HelloAgents框架的智能旅行规划助手API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 注册路由
app.include_router(trip.router, prefix="/api")
app.include_router(poi.router, prefix="/api")
app.include_router(map_routes.router, prefix="/api")
app.include_router(auth_routes.router, prefix="/api")
app.include_router(trip_langgraph.router, prefix="/api")  # LangGraph 版本


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("\n" + "="*60)
    print(f"[START] {settings.app_name} v{settings.app_version}")
    print("="*60)

    # 打印配置信息
    print_config()

    # 验证配置
    try:
        validate_config()
        print("\n[OK] Config validation passed")
    except ValueError as e:
        print(f"\n[ERROR] Config validation failed:\n{e}")
        print("\nPlease check .env file and ensure all required config is set")
        raise

    print("\n" + "="*60)
    print(f"[DOCS] API docs: http://localhost:{settings.port}/docs")
    print(f"[DOCS] ReDoc docs: http://localhost:{settings.port}/redoc")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("\n" + "="*60)
    print("[SHUTDOWN] App is shutting down...")
    print("="*60 + "\n")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )

