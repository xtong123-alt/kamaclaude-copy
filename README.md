# KamaClaude 启动说明

## 🚀 快速开始

### 方式一：使用美化后的 TUI（推荐！）

这是最漂亮的方式，界面如你展示的截图那样：

```powershell
# 进入项目目录
cd "c:\Users\Administrator\Documents\trae_projects\kama claude"

# 运行美化后的 TUI
python kamaclaude_tui.py
```

### 方式二：使用简单 CLI

如果你想要更简单的界面：

```powershell
python simple_cli.py
```

---

## 📋 功能对比

| 功能 | kamaclaude_tui.py | simple_cli.py |
|------|------------------|--------------|
| 美观的界面 | ✅ 非常漂亮 | ❌ 简单 |
| 大 Logo 显示 | ✅ | ❌ |
| 状态显示栏 | ✅ | ❌ |
| Token 统计 | ✅ | ❌ |
| 进度条 | ✅ | ❌ |
| 简单易用 | ✅ | ✅ |

---

## 🎮 使用示例

启动后，你可以输入以下任务：

```
> 列出当前目录的所有文件
> 创建一个 hello.py 文件
> 读取 README.md
> 分析这个项目
```

---

## 🎯 界面说明

```
┌─────────────────────────────────────────┐
│ KamaClaude  127.0.0.1:7437  sess-xxxxx [ready] │ ← 顶部状态栏
├─────────────────────────────────────────┤
│                                         │
│    ██╗  ██╗ █████╗ ...                 │ ← 大 Logo
│    (美观的 Logo)                       │
│                                         │
│ 输入消息开始对话...                     │ ← 提示文字
├─────────────────────────────────────────┤
│                                         │
│ > 列出当前目录                          │ ← 用户输入
│ run 列出当前目录...                    │
│ step 1                                  │
│ 💭 我需要先看看当前目录...              │ ← Agent 思考
│ 🔧 tool list_dir path=.                │ ← 工具调用
│ ✓ ... (结果)                           │ ← 工具结果
│ ✓ completed                             │ ← 完成
│                                         │
├─────────────────────────────────────────┤
│ type a message - enter to send...       │ ← 输入框
└─────────────────────────────────────────┘
```

---

## ⚠️ 注意事项

1. 确保已安装依赖：
   ```powershell
   pip install -e .
   ```

2. 确保 `.env` 文件中有正确的 API Key

3. 按 `Ctrl+C` 退出程序

---

## 🔧 故障排除

如果遇到问题：

1. 检查 API Key 是否正确
2. 检查网络连接
3. 确保 Python 版本 >= 3.11

---
### 💻 核心代码（程序内部工作，不用理）
| 目录/文件 | 作用 |
|----------|------|
| `kamaclaude/` | 核心包目录 |
| `kamaclaude/main.py` | 程序入口 |
| `kamaclaude/core/agent.py` | Agent 大脑 |
| `kamaclaude/core/llm.py` | 连接 AI |
| `kamaclaude/core/tools.py` | 工具箱 |
| `kamaclaude/core/*.py` | 其他核心模块 |


现在去试试 `python kamaclaude_tui.py` 吧！
