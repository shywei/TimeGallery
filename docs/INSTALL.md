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
  └─ 用户相册存储目录/            # 支持配置一个或多个本地/移动硬盘目录 (由首次向导或系统管理配置)
       ├─ YYMMDD.jpg            # 每日主图 (如 241111.jpg)
       ├─ YYMMDD/               # 特别时刻文件夹 (容纳多张照片和视频)
       └─ .trash/               # 自动版本化回收站 (隐藏目录，扫描器天然忽略)
```

---

## 3. 快速启动与局域网多设备访问

### 3.1 方式一：下载绿色免安装包直接运行 (推荐普通用户 · 零环境依赖)

> **适用场景**：日常浏览与家庭归档，**完全无需在电脑上安装 Python、Node.js 或任何运行库**。

1. 下载最新发行包压缩包：`TimeGallery-v1.0.0-win64.zip`。
2. 解压至电脑任意目录（如 `D:\TimeGallery`）。
3. 双击运行根目录下的 **`一键启动拾光记.bat`**（或进入 `TimeGallery` 目录双击 `TimeGallery.exe`）。
4. 服务启动后将自动呼出系统默认浏览器打开：
   ```text
   http://127.0.0.1:8765
   ```
5. 首次启动将进入初始化向导，配置相册照片目录即可开始使用。数据与日志均自动存放在同级 `data/` 目录中。

---

### 3.2 方式二：从源码运行与二次开发 (开发者模式)

> **适用场景**：功能二次开发、代码修改或从 Git 仓库拉取运行。

1. **一键启动**：
   双击运行项目根目录下的：
   ```bat
   run.bat
   ```
   `run.bat` 将自动检查 Python 环境，检查前端静态编译资源（若无则自动编译），并启动单端口服务。

2. **命令行管理**：
   - **启动服务**：`scripts\start.bat`
   - **停止服务**：`scripts\stop.bat`
   - **编译前端**：`scripts\build.bat`
   - **构建独立安装包**：`scripts\package.bat`
   - **数据库备份**：`scripts\backup.bat`

---

### 3.3 家庭局域网多设备访问 (手机 / 平板 / 电视)

> [!WARNING]
> **安全警示：切勿暴露至公网**  
> 拾光记专为家庭私密环境打造，**系统内未内置用户登录鉴权与操作权限隔离机制**。  
> **仅建议在受信任的家庭内部局域网（家庭 Wi-Fi）中使用，强烈不建议部署至公网或进行外网端口映射**（包括但不限于公网服务器部署、路由器 DMZ / 端口转发、DDNS 以及无身份验证的内网穿透服务），避免家庭私密照片与回忆遭到外网未经授权的访问与篡改。

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

---

## 5. 打包为 Windows 独立可执行程序 (.exe) 指南

本项目基于 FastAPI + SQLite + 静态构建的 React 前端开发，**天然支持脱离任何外部环境打包为纯绿色、无依赖的 Windows 可执行应用**。

> [!NOTE]
> **终态用户是否需要安装 Python？**
> **完全不需要！** 打包完成后分发给普通用户或部署到新电脑时，该程序自包含精简版 Python 运行内核与所有第三方依赖库（FastAPI、SQLAlchemy、Pillow、OpenCV 等），目标电脑无需安装 Python、无需配置环境变量、无需安装 Node.js，直接双击运行。

### 5.1 开发者一键打包命令 (推荐)

项目已内置自动化打包脚本与规范配置：

直接在项目根目录下双击运行（或在终端执行）：
```bat
scripts\package.bat
```

脚本将自动执行以下全流程：
1. 检查 Python 虚拟环境并自动就绪 `pyinstaller` 打包工具；
2. 自动触发前端生产编译（`npm run build`），生成最新的 `frontend/dist` 静态资源；
3. 执行 `pyinstaller TimeGallery.spec --clean --noconfirm`，将 Python 内核、第三方依赖与前端页面打包为独立可执行程序；
4. 组织生成绿色发行包目录 `dist\TimeGallery-v1.0.0-win64\`，包含 `TimeGallery.exe`、一键启动批处理与中文说明；
5. 自动压缩生成最终交付文件：`dist\TimeGallery-v1.0.0-win64.zip`。


