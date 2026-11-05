import os
import sys
import time
import threading
import webbrowser
from pathlib import Path

# Prevent UnicodeEncodeError on Windows systems with non-UTF8 console codepages (e.g. CP932, CP437, CP936)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend root is on sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.core.config import settings
from backend.app.main import app
import uvicorn


def open_browser():
    """Wait for uvicorn server startup and launch system default browser."""
    time.sleep(1.2)
    url = f"http://127.0.0.1:{settings.port}"
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[提示] 自动打开浏览器失败，请在浏览器中手动访问: {url} ({e})")


def main():
    print("==================================================================")
    print(f"        拾光记 · TimeGallery (v{settings.app_version}) 本地独立服务正在启动")
    print("==================================================================")
    print(f"[*] 运行端口: {settings.port}")
    print(f"[*] 本地访问: http://127.0.0.1:{settings.port}")
    print(f"[*] 数据目录: {settings.data_dir}")
    print("==================================================================")
    print("[*] 正在拉起系统默认浏览器...")
    print("[*] 提示: 请保持此控制台窗口开启。按 Ctrl + C 或直接关闭此窗口即可退出。")
    print("==================================================================\n")

    # Start browser launcher thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Run Uvicorn directly with the FastAPI app instance
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=settings.port,
        log_level="info",
        access_log=False
    )


if __name__ == "__main__":
    main()
