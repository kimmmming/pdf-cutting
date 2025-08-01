from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import os
import uuid
import zipfile
import tempfile
import shutil
import urllib.parse
from werkzeug.utils import secure_filename
from pdf_chapter_splitter import PDFChapterSplitter
import logging
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = '/tmp/uploads' if os.environ.get('VERCEL') else 'uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/outputs' if os.environ.get('VERCEL') else 'outputs'

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建必要的目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files():
    """清理超过2小时的临时文件"""
    while True:
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=2)
            
            # 清理上传文件夹
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.getctime(filepath) < cutoff_time.timestamp():
                    try:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old upload file: {filename}")
                    except Exception as e:
                        logger.error(f"Error cleaning up {filename}: {e}")
            
            # 清理输出文件夹
            for dirname in os.listdir(app.config['OUTPUT_FOLDER']):
                dirpath = os.path.join(app.config['OUTPUT_FOLDER'], dirname)
                if os.path.isdir(dirpath) and os.path.getctime(dirpath) < cutoff_time.timestamp():
                    try:
                        shutil.rmtree(dirpath)
                        logger.info(f"Cleaned up old output directory: {dirname}")
                    except Exception as e:
                        logger.error(f"Error cleaning up {dirname}: {e}")
                        
        except Exception as e:
            logger.error(f"Error in cleanup thread: {e}")
        
        time.sleep(3600)  # 每小时运行一次

# 启动清理线程 - 在Vercel等无服务器环境中跳过
import os
if not os.environ.get('VERCEL'):
    cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
    cleanup_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '只支持PDF文件'}), 400
    
    try:
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        original_filename = filename
        filename = f"{task_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 获取自定义章节模式
        custom_patterns = request.form.get('custom_patterns', '').strip()
        patterns = [p.strip() for p in custom_patterns.split('\n') if p.strip()] if custom_patterns else []
        
        # 处理PDF
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], task_id)
        splitter = PDFChapterSplitter(filepath, output_dir)
        
        # 添加自定义模式
        for pattern in patterns:
            try:
                splitter.add_custom_pattern(pattern)
            except Exception as e:
                logger.warning(f"Invalid pattern '{pattern}': {e}")
        
        # 执行分割
        success = splitter.split_pdf_by_chapters()
        
        if success:
            # 获取分割结果
            output_files = []
            if os.path.exists(output_dir):
                for f in os.listdir(output_dir):
                    if f.endswith('.pdf'):
                        output_files.append(f)
            
            return jsonify({
                'success': True,
                'task_id': task_id,
                'original_filename': original_filename,
                'output_files': sorted(output_files),
                'total_files': len(output_files)
            })
        else:
            return jsonify({'error': 'PDF处理失败'}), 500
            
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return jsonify({'error': f'处理文件时出错: {str(e)}'}), 500

@app.route('/download/<task_id>')
def download_all(task_id):
    try:
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], task_id)
        if not os.path.exists(output_dir):
            return jsonify({'error': '文件不存在'}), 404
        
        # 创建ZIP文件
        zip_path = os.path.join(tempfile.gettempdir(), f"{task_id}_chapters.zip")
        
        # 如果ZIP文件已存在，先删除
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename in os.listdir(output_dir):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(output_dir, filename)
                    zipf.write(file_path, filename)
        
        def remove_file(response):
            try:
                os.remove(zip_path)
            except Exception:
                pass
            return response
        
        return send_file(
            zip_path, 
            as_attachment=True, 
            download_name=f"pdf_chapters_{task_id[:8]}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Error creating download: {e}")
        return jsonify({'error': f'下载文件时出错: {str(e)}'}), 500

@app.route('/download/<task_id>/<path:filename>')
def download_single(task_id, filename):
    try:
        # URL解码文件名
        decoded_filename = urllib.parse.unquote(filename, encoding='utf-8')
        logger.info(f"Decoded filename: {decoded_filename}")
        
        # 检查文件路径安全性
        if '..' in decoded_filename or '/' in decoded_filename or '\\' in decoded_filename:
            return jsonify({'error': '无效的文件名'}), 400
            
        # 构建文件路径
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], task_id)
        file_path = os.path.join(output_dir, decoded_filename)
        
        logger.info(f"Looking for file: {file_path}")
        logger.info(f"Output dir exists: {os.path.exists(output_dir)}")
        
        # 列出目录中的所有文件用于调试
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            logger.info(f"Files in directory: {files}")
            
            # 尝试精确匹配
            if decoded_filename in files:
                file_path = os.path.join(output_dir, decoded_filename)
            else:
                # 如果精确匹配失败，尝试找到相似的文件
                for f in files:
                    if f.endswith('.pdf') and decoded_filename.replace(' ', '') in f.replace(' ', ''):
                        file_path = os.path.join(output_dir, f)
                        logger.info(f"Found similar file: {f}")
                        break
        
        if not os.path.exists(file_path) or not file_path.endswith('.pdf'):
            logger.error(f"File not found: {file_path}")
            return jsonify({'error': f'文件不存在: {decoded_filename}'}), 404
        
        return send_file(
            file_path, 
            as_attachment=True, 
            download_name=os.path.basename(file_path),
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error downloading single file: {e}")
        return jsonify({'error': f'下载文件时出错: {str(e)}'}), 500

@app.route('/preview/<task_id>')
def preview_chapters(task_id):
    try:
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], task_id)
        if not os.path.exists(output_dir):
            return jsonify({'error': '文件不存在'}), 404
        
        chapters = []
        for filename in sorted(os.listdir(output_dir)):
            if filename.endswith('.pdf'):
                file_path = os.path.join(output_dir, filename)
                file_size = os.path.getsize(file_path)
                chapters.append({
                    'filename': filename,
                    'size': f"{file_size / 1024:.1f} KB"
                })
        
        return jsonify({
            'task_id': task_id,
            'chapters': chapters,
            'total': len(chapters)
        })
        
    except Exception as e:
        logger.error(f"Error previewing chapters: {e}")
        return jsonify({'error': '获取章节信息失败'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': '文件太大，最大支持50MB'}), 413

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)