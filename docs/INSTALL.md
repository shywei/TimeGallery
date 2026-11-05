# 拾光记 (Shiguangji) · 安装与运行指南

## 1. 运行环境要求

- **操作系统**：Windows 10 / Windows 11 (64位)
- **Python**：Python 3.12+ (本项目推荐并支持 Python 3.13)
- **Node.js**：Node.js 18+ (仅当修改前端源码并需重新执行构建时需要，运行预编译版本无需安装)
- **网络环境**：家庭私有局域网，不依赖公网 IP 与云服务，所有数据完全在本地存储。

---

## 2. 目录结构说明

```text
gallery/
  ├─ backend/                   # FastAPI 后端源码与虚拟环境 .venv/
  ├─ frontend/                  # React 19 + TypeScript + Vite 前端工程
  ├─ data/                      # 运行时独立数据目录
  │    ├─ growing_up.db         # SQLite 主数据库
  │    ├─ thumbnails/           # 每日主图 480px WebP 缓存
  │    ├─ previews/             # 每日主图 1600px WebP 缓存
  │    ├─ moment_thumbs/        # 特别时刻缩略图缓存 (含视频关键帧)
  │    ├─ moment_previews/      # 特别时刻照片高清预览缓存
  │    ├─ backups/              # 数据库自动与手动快照备份目录
  │    └─ logs/                 # 系统运行与错误日志
  ├─ scripts/                   # Windows 运维管理批处理脚本
  │    ├─ start.bat             # 启动后台服务 (默认端口 8765)
  │    ├─ stop.bat              # 停止后台服务 (按端口精准关闭)
  │    ├─ build.bat             # 编译前端静态资产至 dist/
  │    ├─ backup.bat            # 触发数据库快照备份
  │    └─ check_environment.bat # 检查 Python / Node 环境
  ├─ run.bat                    # Windows 一键启动脚本
  └─ 用户相册根目录/              # 由首次向导或系统配置指定
       ├─ YYMMDD.jpg            # 每日主图 (如 241111.jpg)
       ├─ YYMMDD/               # 特别时刻文件夹 (容纳多张照片和视频)
       └─ .trash/               # 自动版本化回收站 (隐藏目录，扫描器天然忽略)
```

---

## 3. 快速启动与局域网多设备访问

### 3.1 本机快速启动
双击运行项目根目录下的：
```bat
run.bat
```
`run.bat` 将自动检查 Python 环境，检查前端静态编译资源（若无则自动编译），并启动单端口服务。

启动后在浏览器打开：
```text
http://127.0.0.1:8765
```

### 3.2 家庭局域网多设备访问 (手机 / 平板 / 电视)
若需在家中手机、平板或智能电视上浏览画册：
1. 确保 Windows 防火墙允许 8765 端口入站连接（专用网络）。
2. 在 `scripts/start.bat` 中将监听地址改为 `0.0.0.0`：
   ```bat
   "%VENV_PYTHON%" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8765
   ```
3. 查看 Windows 电脑在家庭路由器下的局域网 IP（例如 `192.168.1.100`），即可在手机浏览器打开：
   ```text
   http://192.168.1.100:8765
   ```

---

## 4. 常见运维与故障排查

- **端口 8765 被占用**：运行 `scripts\stop.bat` 释放占用端口。
- **扫描未发现主图照片**：请检查主图文件名是否严格为 6 位数字格式（如 `241103.jpg`），避免出现 `IMG_241103.jpg` 等前缀。
- **特别时刻文件夹未识别**：特别时刻文件夹名称必须严格为 6 位纯数字（如 `241103`），其内部的照片与视频文件名无任何格式限制。
- **查看任务日志**：进入 `data/logs/` 目录下查看 `application.log` 与 `error.log`。
