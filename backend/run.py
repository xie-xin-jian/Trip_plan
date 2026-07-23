"""启动脚本"""

import sys
import os

# 修复 Windows 控制台 GBK 编码无法输出 emoji 的问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ["PYTHONIOENCODING"] = "utf-8"

import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower()
    )

