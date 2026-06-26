
# KamaClaude

一个本地运行的 AI Agent 系统，像 Claude 一样使用！

```
██╗  ██╗ █████╗ ███╗   ███╗ █████╗  ██████╗██╗      █████╗ 
██║ ██╔╝██╔══██╗████╗ ████║██╔══██╗██╔════╝██║     ██╔══██╗
█████╔╝ ███████║██╔████╔██║███████║██║     ██║     ███████║
██╔═██╗ ██╔══██║██║╚██╔╝██║██╔══██║██║     ██║     ██╔══██║
██║  ██╗██║  ██║██║ ╚═╝ ██║██║  ██║╚██████╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝
```

## 特性

- 🤖 **智能 Agent** - 自主规划和执行任务
- 🔧 **内置工具** - 文件操作、命令执行
- ✋ **权限控制** - 安全的工具调用
- 📜 **事件流展示** - 实时查看执行过程
- 💾 **会话持久化** - 保存历史记录
- 🎨 **美观界面** - 终端 UI
- 🚀 **一键启动** - 像用命令行使用

## 快速开始

### 1. 安装

```bash
git clone <your-repository-url>
cd kama-claude
pip install -e .
```

### 2. 配置

复制配置模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key：

```env
# 阿里云百炼（推荐）
ALIYUN_API_KEY=your_api_key_here
ALIYUN_MODEL=qwen-plus
```

### 3. 运行

```bash
kamaclaude
```

就这么简单！

## 命令

| 命令 | 说明 |
|------|------|
| `kamaclaude` | ✨ 启动美观的 TUI（推荐） |
| `kama` | 简单 CLI |
| `kama-core` | 核心守护进程 |
| `kama-tui` | 高级 Textual TUI |

## 配置

KamaClaude 支持多种 LLM 提供商：

- 阿里云百炼（推荐）
- DeepSeek
- OpenAI（兼容模式）

编辑 `.env` 文件来选择你想使用的提供商。

## 使用示例

### 列出目录文件

```
> 列出当前目录的所有文件
```

### 执行任务

```
> 分析这个项目的结构
```

### 创建文件

```
> 创建一个 hello.py 文件
```

## 项目结构

```
kama-claude/
├── kamaclaude/
│   ├── core/              # 核心模块
│   │   ├── agent.py      # Agent 核心
│   │   ├── llm.py        # LLM 集成
│   │   ├── tools.py      # 工具系统
│   │   ├── eventbus.py   # 事件总线
│   │   ├── session.py    # 会话管理
│   │   └── types.py      # 数据类型
│   ├── tui/               # 界面模块
│   ├── cli.py            # 命令行
│   └── main.py           # 主入口
├── .env.example            # 配置模板
├── .gitignore             # Git 忽略
└── pyproject.toml         # 项目配置
└── README.md               # 本文件
```

## 开发

### 安装开发模式

```bash
pip install -e .
```

### 运行验证

```bash
python 验证.py
```

## 许可证

MIT

## 贡献

欢迎贡献！请提交 Issue 或 Pull Request。

---

**享受你的 KamaClaude！🚀
