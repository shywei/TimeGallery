import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

# Force UTF-8 stream output to prevent Windows console codepage encoding crashes (e.g. cp932/cp936)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_cmd(cmd, cwd=REPO_ROOT, check=True):
    print(f"[*] 执行命令: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    res = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str))
    if check and res.returncode != 0:
        print(f"[ERROR] 命令执行失败 (退出代码 {res.returncode}): {cmd}")
        sys.exit(res.returncode)
    return res.returncode


def main():
    print("====================================================")
    print("     拾光记 · TimeGallery 独立安装包构建工具")
    print("====================================================")

    # 1. 检查 Python 运行环境
    python_exe = sys.executable
    print(f"[*] Python 解释器: {python_exe}")

    # 2. 检查 PyInstaller
    print("\n[1/5] 检查 PyInstaller 打包依赖...")
    try:
        import PyInstaller
        print(f"[*] PyInstaller 已就绪 (版本: {PyInstaller.__version__})")
    except ImportError:
        print("[INFO] 正在自动安装 PyInstaller...")
        run_cmd([python_exe, "-m", "pip", "install", "pyinstaller"])

    # 3. 编译前端生产静态资源
    print("\n[2/5] 编译前端静态资源 (Vite SPA)...")
    frontend_dir = REPO_ROOT / "frontend"
    run_cmd("cmd.exe /c \"npm run build\"", cwd=frontend_dir)

    dist_index = frontend_dir / "dist" / "index.html"
    if not dist_index.exists():
        print(f"[ERROR] 前端构建产物缺失: {dist_index}")
        sys.exit(1)
    print(f"[*] 前端静态资源就绪: {dist_index}")

    # 4. 执行 PyInstaller 打包
    print("\n[3/5] 执行 PyInstaller 生成独立可执行程序...")
    spec_file = REPO_ROOT / "TimeGallery.spec"
    run_cmd([python_exe, "-m", "PyInstaller", str(spec_file), "--clean", "--noconfirm"])

    # 5. 组织发行包目录结构
    print("\n[4/5] 组织绿色免安装发行包结构...")
    release_dir = REPO_ROOT / "dist" / "TimeGallery-v1.0.0-win64"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)

    built_dir = REPO_ROOT / "dist" / "TimeGallery"
    if not built_dir.exists():
        print(f"[ERROR] 未找到 PyInstaller 编译输出目录: {built_dir}")
        sys.exit(1)

    # 拷贝 TimeGallery 目录
    dest_app_dir = release_dir / "TimeGallery"
    print(f"[*] 复制程序目录至: {dest_app_dir}")
    shutil.copytree(built_dir, dest_app_dir)

    # 写入一键启动批处理
    launcher_path = release_dir / "一键启动拾光记.bat"
    launcher_content = "@echo off\r\ncd /d \"%~dp0TimeGallery\"\r\nstart \"\" \"TimeGallery.exe\"\r\n"
    launcher_path.write_bytes(launcher_content.encode("ansi"))
    print(f"[*] 生成启动脚本: {launcher_path.name}")

    # 写入使用说明文档
    readme_template = REPO_ROOT / "templates" / "release_readme.txt"
    readme_dest = release_dir / "使用说明.txt"
    if readme_template.exists():
        shutil.copyfile(readme_template, readme_dest)
        print(f"[*] 生成说明文档: {readme_dest.name}")

    # 6. 生成 ZIP 压缩包
    print("\n[5/5] 打包生成 ZIP 发行文件...")
    zip_path = REPO_ROOT / "dist" / "TimeGallery-v1.0.0-win64.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(release_dir):
            for file in files:
                abs_file = Path(root) / file
                rel_path = abs_file.relative_to(release_dir.parent)
                zf.write(abs_file, rel_path.as_posix())

    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print("\n====================================================")
    print("[SUCCESS] 拾光记独立安装包构建完成！")
    print(f"[*] 绿色发行目录: {release_dir}")
    print(f"[*] ZIP 压缩归档: {zip_path} ({zip_size_mb:.1f} MB)")
    print("====================================================")


if __name__ == "__main__":
    main()
