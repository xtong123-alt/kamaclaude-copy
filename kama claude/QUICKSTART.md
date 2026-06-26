# 快速开始

## 5分钟上手 KamaClaude

### 1. 克隆或下载项目

```bash
# 如果在 GitHub 上
git clone <your-repository-url>
cd kama-claude
```

### 2. 安装

```bash
pip install -e .
```

### 3. 配置

```bash
# Windows:
copy .env.example .env

# Linux/Mac:
cp .env.example .env
```

然后编辑 `.env` 文件，填入你的 API Key：

```env
ALIYUN_API_KEY=sk-your-real-api-key-here
```

### 4. 启动！

```bash
kamaclaude
```

---

## 就是这么简单！

现在你可以和你的 KamaClaude 对话了！

试试这些：

```
> 列出当前目录的文件
> 创建一个 hello.py 文件
> 分析这个项目的结构
```

---

## 有问题？

- 检查 Python 版本 >= 3.11
- 确保 API Key 正确
- 运行 `python 验证.py` 来诊断问题
