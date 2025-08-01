# PDF章节分割工具 - Web版本

一个基于Flask的在线PDF章节分割工具，支持智能章节检测和批量下载。

## 🌟 功能特性

### 核心功能
- 🔍 **智能章节检测** - 自动识别中英文章节标题
- 📄 **多格式支持** - 支持多种章节标题格式（第一章、Chapter 1、1.等）
- ⚙️ **自定义模式** - 支持添加自定义章节匹配正则表达式
- 📦 **批量下载** - 支持单个文件下载和ZIP打包下载
- 🛡️ **安全可靠** - 完善的文件验证和错误处理
- 🗂️ **自动清理** - 定时清理临时文件，节省存储空间

### 用户体验
- 📱 **响应式设计** - 支持手机、平板、桌面设备
- 🎨 **现代化UI** - 美观的界面设计和动画效果
- 📊 **实时进度** - 文件处理进度实时显示
- 🖱️ **拖拽上传** - 支持文件拖拽上传
- 💬 **友好提示** - 详细的错误提示和使用说明

## 🚀 快速开始

### 本地运行

1. **克隆项目**
```bash
git clone https://github.com/kimmmming/pdf-cutting.git
cd pdf-cutting
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动应用**
```bash
python app.py
```

4. **访问应用**
打开浏览器访问 `http://localhost:5000`

### Docker部署

1. **构建镜像**
```bash
docker build -t pdf-splitter-web .
```

2. **运行容器**
```bash
docker run -p 5000:5000 pdf-splitter-web
```

### 云平台部署

#### Heroku部署
```bash
# 安装Heroku CLI后
heroku create your-app-name
git push heroku main
```

#### 阿里云/腾讯云部署
1. 上传代码到服务器
2. 安装Python和依赖
3. 使用gunicorn启动：
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

## 📋 使用方法

### 基本流程
1. 🗂️ **选择PDF文件** - 点击选择或拖拽PDF文件到页面
2. ⚙️ **配置选项** - 可选择添加自定义章节匹配模式
3. ⚡ **开始处理** - 点击"开始分割PDF"按钮
4. ⏳ **等待完成** - 查看实时处理进度
5. 📥 **下载结果** - 单独下载章节或打包下载全部

### 支持的章节格式
- **中文格式**：第一章、第1章、第1节、第一部分
- **英文格式**：Chapter 1、Section 1
- **数字格式**：1.、2.、3.（后面需要有内容）
- **自定义格式**：通过正则表达式自定义

### 自定义章节模式示例
```
^附录.*
^序言
^目录
^参考文献
^索引.*
```

## 🛠️ 技术架构

### 后端技术栈
- **Flask** - Web框架
- **PyPDF2** - PDF处理库
- **Werkzeug** - WSGI工具库
- **Gunicorn** - WSGI服务器

### 前端技术栈
- **Bootstrap 5** - CSS框架
- **Font Awesome** - 图标库
- **原生JavaScript** - 交互逻辑
- **Fetch API** - 异步请求

### 核心特性
- **异步文件处理** - 非阻塞文件上传和处理
- **内存管理** - 合理的文件缓存和清理机制
- **错误处理** - 全面的异常捕获和用户友好提示
- **安全防护** - 文件类型验证、大小限制、路径安全

## ⚙️ 配置选项

### 环境变量
```bash
export SECRET_KEY="your-secret-key"
export MAX_CONTENT_LENGTH=52428800  # 50MB
export UPLOAD_FOLDER="uploads"
export OUTPUT_FOLDER="outputs"
```

### 应用配置
```python
# app.py 中的配置
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
```

## 📊 API接口

### 上传和处理PDF
```
POST /upload
Content-Type: multipart/form-data

参数:
- file: PDF文件
- custom_patterns: 自定义章节模式（可选）

返回:
{
  "success": true,
  "task_id": "uuid",
  "original_filename": "document.pdf",
  "output_files": ["第01章_标题.pdf", ...],
  "total_files": 5
}
```

### 下载文件
```
GET /download/<task_id>                    # 下载所有章节（ZIP）
GET /download/<task_id>/<filename>         # 下载单个章节
```

### 预览章节
```
GET /preview/<task_id>

返回:
{
  "task_id": "uuid",
  "chapters": [
    {
      "filename": "第01章_标题.pdf",
      "size": "123.4 KB"
    }
  ],
  "total": 5
}
```

## 🔧 开发和扩展

### 添加新的章节检测模式
```python
# 在 PDFChapterSplitter 类中添加
self.chapter_patterns.append(r'^新的模式.*')
```

### 自定义文件处理逻辑
```python
# 继承并重写方法
class CustomPDFSplitter(PDFChapterSplitter):
    def find_chapter_breaks(self):
        # 自定义章节检测逻辑
        pass
```

### 添加新的导出格式
```python
# 在 app.py 中扩展下载功能
@app.route('/export/<task_id>/<format>')
def export_chapters(task_id, format):
    # 支持不同格式导出
    pass
```

## 🐛 故障排除

### 常见问题

1. **上传失败**
   - 检查文件大小（最大50MB）
   - 确认文件格式为PDF
   - 检查网络连接

2. **处理失败**
   - 确认PDF文件没有损坏
   - 检查PDF是否加密
   - 查看服务器日志

3. **下载问题**
   - 检查浏览器下载设置
   - 确认文件未被杀毒软件拦截
   - 重试下载

### 日志查看
```bash
# 生产环境
tail -f /var/log/pdf-splitter.log

# 开发环境
python app.py  # 控制台输出
```

## 📈 性能优化

### 服务器配置建议
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **存储**: SSD，至少10GB可用空间
- **网络**: 10Mbps以上带宽

### 生产环境优化
```bash
# 使用多进程
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

# 配置nginx反向代理
# /etc/nginx/sites-available/pdf-splitter
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目链接: [https://github.com/kimmmming/pdf-cutting](https://github.com/kimmmming/pdf-cutting)
- 问题反馈: [Issues](https://github.com/kimmmming/pdf-cutting/issues)

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - 优秀的Python Web框架
- [PyPDF2](https://pypdf2.readthedocs.io/) - 强大的PDF处理库
- [Bootstrap](https://getbootstrap.com/) - 现代化的CSS框架
- [Font Awesome](https://fontawesome.com/) - 丰富的图标库