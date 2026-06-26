# GitHub 上传指南

## 把你的 KamaClaude 上传到 GitHub 开源！

### 第一步：准备工作

#### 1. 注册 GitHub 账号（如果还没有）
- 访问 https://github.com
- 注册一个免费账号

#### 2. 安装 Git（已经安装了！✅）
你的电脑上已经有 git version 2.54.0

---

### 第二步：在你的电脑上操作

在 PowerShell 中执行以下命令：

```powershell
# 进入项目目录
cd "c:\Users\Administrator\Documents\trae_projects\kama claude"

# 1. 初始化 Git 仓库
git init

# 2. 添加所有文件
git add .

# 3. 提交
git commit -m "Initial commit: KamaClaude - A local AI Agent system"

# 4. 切换到 main 分支
git branch -M main
```

---

### 第三步：在 GitHub 上创建仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: kamaclaude（或其他你喜欢的名字）
   - **Description**: A local AI Agent system, like Claude but locally!
   - **Public/Private**: 选择 Public（开源）
   - ❌ **不要**勾选 "Initialize this repository with a README"
   - ❌ **不要**勾选 .gitignore
   - ❌ **不要**勾选 License
3. 点击 "Create repository"

---

### 第四步：连接并推送

GitHub 创建完成后，页面会显示类似这样的命令（复制 GitHub 页面上显示的命令）：

```powershell
# 替换 <你的用户名> 和 <你的仓库名>
git remote add origin https://github.com/<你的用户名>/<你的仓库名>.git

# 推送到 GitHub
git push -u origin main
```

---

### 第五步：完成！

刷新 GitHub 页面，你的 KamaClaude 已经开源了！

---

## 完整示例

假设你的 GitHub 用户名是 `john-doe`，仓库名是 `kamaclaude`：

```powershell
cd "c:\Users\Administrator\Documents\trae_projects\kama claude"

git init
git add .
git commit -m "Initial commit: KamaClaude - A local AI Agent system"
git branch -M main
git remote add origin https://github.com/john-doe/kamaclaude.git
git push -u origin main
```

---

## 配置 Git 用户信息（如果是第一次用 Git）

如果 Git 提示你配置用户信息：

```powershell
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

把 Your Name 和 your@email.com 换成你自己的。

---

## 完成后

你的项目就可以被别人这样安装使用了：

```bash
git clone https://github.com/<你的用户名>/kamaclaude.git
cd kamaclaude
pip install -e .
kamaclaude
```

---

## 常见问题

### Q: Git 提示需要登录？
A: 现在 GitHub 需要用 Personal Access Token 而不是密码。
   - 访问 https://github.com/settings/tokens
   - 生成一个 token，权限选 repo
   - 在 push 时，用户名填你 GitHub 用户名，密码填这个 token

### Q: 想添加新功能后更新？
A: 以后只需：
   ```bash
   git add .
   git commit -m "描述你做的更新"
   git push
   ```

### Q: 不小心提交了 .env 文件？
A: 没关系，.gitignore 已经包含 .env 了，所以不会上传！
