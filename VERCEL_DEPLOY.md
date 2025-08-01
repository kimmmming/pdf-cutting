# Vercel部署指南

## 🚀 快速部署到Vercel

### 方法一：通过Vercel CLI
```bash
# 安装Vercel CLI
npm install -g vercel

# 登录Vercel
vercel login

# 部署项目
vercel --prod
```

### 方法二：通过GitHub集成
1. 将项目推送到GitHub
2. 访问 [vercel.com](https://vercel.com)
3. 点击 "Import Project"
4. 选择你的GitHub仓库
5. Vercel会自动检测并部署

## ⚙️ 配置文件说明

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "./app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/"
    }
  ]
}
```

### api/index.py
这是Vercel无服务器函数的入口点，导入主应用。

## 🔧 已解决的Vercel兼容性问题

### 1. 文件存储路径
- **本地**: `uploads/`, `outputs/`
- **Vercel**: `/tmp/uploads/`, `/tmp/outputs/`
- 自动检测环境并使用正确路径

### 2. 后台线程
- 在Vercel环境中禁用清理线程
- 无服务器函数不支持长期运行的后台任务

### 3. 依赖包优化
- 使用`requirements-vercel.txt`减少包大小
- 移除了gunicorn等Vercel不需要的包

## ⚠️ Vercel限制

### 文件大小限制
- **请求体**: 4.5MB (Hobby plan)
- **响应体**: 4.5MB (Hobby plan)
- **函数执行时间**: 10秒 (Hobby plan)

### 存储限制
- `/tmp`目录在函数执行间不持久化
- 每次请求都是全新环境

## 💡 建议的替代方案

### 对于大文件处理
如果需要处理超过4.5MB的PDF文件，建议使用：

1. **Railway** - 支持更大文件
```bash
# 安装Railway CLI
npm install -g @railway/cli

# 登录并部署
railway login
railway deploy
```

2. **Render** - 免费plan支持更大文件
```bash
# 连接GitHub仓库到Render
# 设置构建命令: pip install -r requirements.txt
# 设置启动命令: gunicorn app:app
```

3. **Heroku** - 传统PaaS平台
```bash
# 使用已配置的Procfile部署
git push heroku main
```

## 🛠️ 调试Vercel部署

### 查看日志
```bash
vercel logs [deployment-url]
```

### 本地测试Vercel环境
```bash
vercel dev
```

### 环境变量设置
在Vercel仪表板中设置：
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key`

## 📋 部署检查清单

- [ ] `vercel.json` 配置正确
- [ ] `api/index.py` 入口文件存在
- [ ] 环境变量已设置
- [ ] 依赖包版本兼容
- [ ] 文件路径适配无服务器环境
- [ ] 测试上传和下载功能

## 🔗 有用链接

- [Vercel Python文档](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Flask on Vercel指南](https://vercel.com/guides/using-flask-with-vercel)
- [Vercel限制说明](https://vercel.com/docs/concepts/limits/overview)