# 嘉行找人

轻量级局域网找人工具。系统托盘常驻，在线用户一目了然，一键找人全屏提醒。

## 功能

- 🟢 系统托盘常驻，不占桌面
- 👤 首次运行注册名字，自动绑定IP
- 👥 查看在线用户列表
- ⭐ 收藏常用联系人，方便下次找
- 🔔 找人功能：发送请求 → 对方全屏弹窗提醒
- 🔒 双方确认流程，尊重隐私

## 快速开始

### 1. 部署后端（PHP + SQLite）

将 `server/` 目录上传到你的PHP服务器，确保目录可写。

例如部署到 `http://你的IP:端口/findpeople`，PHP文件为 `index.php`，直接访问该URL即可。

无需额外数据库软件，SQLite自动创建。

### 2. 运行客户端

**方式一：直接运行exe（推荐）**

从 [Releases](../../releases) 下载最新版 `嘉行找人.exe`，双击运行。

首次运行输入服务器地址（如 `http://你的IP:端口/findpeople`）和你的名字即可。

**方式二：Python源码运行**

```bash
pip install -r requirements.txt
python client/main.py
```

## 使用说明

1. **首次运行**：输入服务器地址和你的名字
2. **查看用户**：右键托盘图标 → "查看在线用户"
3. **收藏用户**：在用户列表中点击"☆ 收藏"按钮
4. **找人**：在用户列表中点击"找 TA"按钮，确认后发送
5. **被找提醒**：收到找人请求时会弹出全屏提醒，可选择"我知道了"或"忽略"

## 项目结构

```
├── server/
│   └── index.php            # PHP后端（单文件，SQLite自动建库）
├── client/
│   ├── main.py              # 主程序入口
│   ├── api_client.py        # API封装
│   ├── gui.py               # GUI界面
│   └── config.py            # 配置管理
└── .github/workflows/
    └── build.yml            # GitHub Actions自动打包exe
```

## 技术细节

- **轮询间隔**：30秒（找人等待中自动加快到10秒）
- **离线判断**：5分钟无心跳视为离线
- **网络优化**：sync接口合并心跳+检查+结果，单次请求完成
- **用户标识**：自动使用本机IP作为唯一标识

## 配置文件位置

- Windows: `%APPDATA%/jiaxing-find-people/config.json`
