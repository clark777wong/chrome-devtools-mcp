# 本地开发隐私保护指南

## 概述

当你从 GitHub 下载项目并添加自己的功能时，需要注意隐私和安全问题。本指南将帮助你：

1. ✅ 保持与上游项目同步更新
2. ✅ 自动检查安全漏洞
3. 🔒 保护本地隐私不被泄露到上游

---

## 隐私风险识别

### 可能泄露隐私的文件类型

| 文件类型 | 示例 | 风险等级 |
|----------|------|----------|
| 配置文件 | `.env`, `config/secrets.json` | 🔴 高 |
| API 密钥 | `api-key.txt`, `token.json` | 🔴 高 |
| 登录脚本 | `login.ts`, `auth.ts` | 🟡 中 |
| 证书文件 | `.pem`, `.key`, `.cert` | 🔴 高 |
| 数据库配置 | `db.config.js` | 🔴 高 |

---

## 保护措施

### 1. 使用 .gitignore

项目已有 `.gitignore`，确保你的敏感文件被排除：

```bash
# 在 .gitignore 中添加
.env
.env.*
*.local
config/secrets.*
credentials.json
api-key*
token*
*.pem
*.key
*.cert
```

### 2. 敏感文件存放位置

将敏感文件放在项目外的目录：

```bash
# 方案 1: 用户主目录
~/my-secrets/
  ├── api-key.json
  └── login-credentials.json

# 方案 2: 环境变量（推荐）
export MY_API_KEY="your-key-here"
```

### 3. 使用环境变量加载敏感配置

```typescript
// ✅ 推荐方式：环境变量
const apiKey = process.env.MY_API_KEY;
if (!apiKey) {
  throw new Error('MY_API_KEY environment variable not set');
}

// ❌ 避免：硬编码密钥
const apiKey = 'sk-1234567890'; // 不要这样做！
```

---

## 同步上游更新的安全流程

### 推荐的同步脚本使用方式

```bash
# 同步上游并检查漏洞（推荐）
npm run sync-upstream

# 单独检查漏洞
npm run check-vulnerabilities

# 手动同步步骤（如果需要更多控制）
git fetch upstream
git stash                    # 暂存本地修改
git merge upstream/main     # 合并上游
git stash pop               # 恢复本地修改
npm install                 # 更新依赖
npm audit                   # 检查漏洞
```

### 同步前的安全检查

同步脚本会自动检测潜在的敏感文件。检测逻辑包括：

1. 文件名包含敏感关键词：`password`, `secret`, `token`, `apiKey`, `credential`
2. 特定扩展名：`.key`, `.pem`, `.cert`
3. 隐藏的 `.env` 文件

如果检测到，脚本会发出警告。

---

## 本地添加功能的最佳实践

### 1. 创建独立的本地配置文件

```typescript
// src/config/local-config.ts - 此文件应在 .gitignore 中
export const localConfig = {
  // 只放开发/本地配置
  devMode: true,
  logLevel: 'debug'
};

// src/config/index.ts - 导出安全的默认配置
export const config = {
  ...defaultConfig,
  ...(process.env.LOCAL_CONFIG && require('./local-config'))
};
```

### 2. 使用条件导入

```typescript
// 只在本地环境加载
let localAuth;
if (process.env.LOCAL_DEV === 'true') {
  localAuth = await import('../local/auth.js');
}
```

### 3. 将本地功能模块化

```
src/
├── features/           # 上游功能
├── local/             # 本地功能（确保在 .gitignore）
│   ├── login/
│   ├── auth/
│   └── secrets/
└── main.ts
```

---

## 验证你的设置

### 检查哪些文件会被提交

```bash
# 查看哪些文件会被提交
git status

# 查看哪些文件在 .gitignore 中
git check-ignore -v .
```

### 运行隐私检查

```bash
# 运行同步脚本，它会自动检查敏感文件
npm run sync-upstream
```

---

## 常见问题

### Q: 我可以直接提交到上游仓库吗？

**不要这样做！** 这会暴露你的隐私。应该：
- Fork 上游仓库
- 在你的 fork 中添加功能
- 向上游发送 Pull Request（移除敏感信息后）

### Q: 如果上游更新破坏了我的本地功能怎么办？

```bash
# 1. 查看冲突
git status

# 2. 手动解决冲突
# 编辑冲突的文件

# 3. 标记解决
git add .

# 4. 提交
git commit

# 5. 运行测试
npm test
```

### Q: 如何安全地在多台机器上同步配置？

**方案 1**：使用密码管理器（如 1Password, Bitwarden）

**方案 2**：使用加密的 dotfiles 仓库

**方案 3**：使用环境变量或 Docker secrets

---

## 快速命令参考

| 命令 | 说明 |
|------|------|
| `npm run sync-upstream` | 同步上游并检查漏洞 |
| `npm run check-vulnerabilities` | 仅检查漏洞 |
| `git remote -v` | 查看远程仓库 |
| `git stash` | 暂存本地修改 |
| `git stash pop` | 恢复本地修改 |
| `npm audit` | 检查安全漏洞 |
| `npm audit fix` | 自动修复漏洞 |
