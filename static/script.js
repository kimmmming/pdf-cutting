document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const uploadBtn = document.getElementById('uploadBtn');
    const progressSection = document.getElementById('progressSection');
    const resultSection = document.getElementById('resultSection');
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.getElementById('progressText');

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('pdfFile');
        const file = fileInput.files[0];
        
        if (!file) {
            showAlert('请选择一个PDF文件', 'error');
            return;
        }
        
        if (file.type !== 'application/pdf') {
            showAlert('请选择PDF文件', 'error');
            return;
        }
        
        if (file.size > 50 * 1024 * 1024) {
            showAlert('文件大小不能超过50MB', 'error');
            return;
        }
        
        // 显示进度条
        showProgress();
        
        // 创建FormData
        const formData = new FormData();
        formData.append('file', file);
        formData.append('custom_patterns', document.getElementById('customPatterns').value);
        
        try {
            // 模拟进度更新
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress > 90) progress = 90;
                updateProgress(progress, '正在处理PDF文件...');
            }, 500);
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            clearInterval(progressInterval);
            
            const result = await response.json();
            
            if (result.success) {
                updateProgress(100, '处理完成！');
                setTimeout(() => {
                    hideProgress();
                    showResult(result);
                }, 1000);
            } else {
                hideProgress();
                showAlert(result.error || '处理失败', 'error');
            }
        } catch (error) {
            hideProgress();
            showAlert('网络错误，请重试', 'error');
            console.error('Upload error:', error);
        }
    });

    function showProgress() {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            <span class="btn-content">
                <span class="btn-text">正在处理文档...</span>
                <small class="btn-subtext">请稍候，系统正在工作</small>
            </span>
        `;
        progressSection.style.display = 'block';
        progressSection.classList.add('fade-in-up');
        resultSection.style.display = 'none';
        updateProgress(0, '正在上传并验证PDF文件...');
    }

    function hideProgress() {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = `
            <i class="fas fa-scissors me-2"></i>
            <span class="btn-content">
                <span class="btn-text">开始智能分割PDF</span>
                <span class="btn-subtext">点击此按钮开始处理您的文档</span>
            </span>
        `;
        progressSection.style.display = 'none';
    }

    function updateProgress(percent, text) {
        progressBar.style.width = percent + '%';
        progressText.innerHTML = `
            <i class="fas fa-info-circle me-1"></i>
            ${text}
        `;
        
        // 根据进度更新文字
        if (percent < 30) {
            progressText.innerHTML = `
                <i class="fas fa-upload me-1"></i>
                ${text}
            `;
        } else if (percent < 70) {
            progressText.innerHTML = `
                <i class="fas fa-cog fa-spin me-1"></i>
                正在智能分析文档结构和章节...
            `;
        } else if (percent < 95) {
            progressText.innerHTML = `
                <i class="fas fa-cut me-1"></i>
                正在分割PDF文档为章节文件...
            `;
        } else {
            progressText.innerHTML = `
                <i class="fas fa-check me-1"></i>
                ${text}
            `;
        }
    }

    function showResult(result) {
        document.getElementById('originalFilename').textContent = result.original_filename;
        
        // 设置下载全部按钮
        const downloadAllBtn = document.getElementById('downloadAllBtn');
        downloadAllBtn.onclick = () => {
            window.location.href = `/download/${result.task_id}`;
        };
        
        // 显示章节列表
        displayChapterList(result.task_id, result.output_files);
        
        resultSection.style.display = 'block';
        resultSection.classList.add('fade-in-up');
        
        // 滚动到结果区域
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }

    function displayChapterList(taskId, files) {
        const chapterList = document.getElementById('chapterList');
        chapterList.innerHTML = '';
        
        files.forEach((filename, index) => {
            const listItem = document.createElement('div');
            listItem.className = 'chapter-item';
            listItem.style.animationDelay = `${index * 0.1}s`;
            listItem.classList.add('fade-in-up');
            
            listItem.innerHTML = `
                <div class="chapter-info">
                    <div class="chapter-title">
                        <i class="fas fa-file-pdf text-danger me-2"></i>
                        ${filename}
                    </div>
                    <div class="chapter-size">
                        <i class="fas fa-layer-group me-1 text-muted"></i>
                        第 ${index + 1} 个章节文件
                        <span class="badge bg-light text-dark ms-2">PDF</span>
                    </div>
                </div>
                <div class="chapter-actions">
                    <button class="btn btn-outline-primary btn-sm download-chapter-btn" 
                            onclick="downloadSingle('${taskId}', '${filename}')"
                            data-filename="${filename}">
                        <i class="fas fa-download me-1"></i>
                        <span class="btn-content">
                            <span class="btn-text">下载</span>
                            <small class="btn-subtext">单独下载此章节</small>
                        </span>
                    </button>
                </div>
            `;
            
            chapterList.appendChild(listItem);
        });
        
        // 添加总结信息
        const summaryItem = document.createElement('div');
        summaryItem.className = 'list-group-item text-center summary-item';
        summaryItem.innerHTML = `
            <div class="summary-content">
                <i class="fas fa-check-circle text-success me-2"></i>
                <strong>分割完成！</strong>共生成 <span class="badge bg-primary">${files.length}</span> 个章节文件
            </div>
            <small class="text-muted mt-2 d-block">
                <i class="fas fa-info-circle me-1"></i>
                所有文件已准备就绪，您可以单独下载或批量下载全部文件
            </small>
        `;
        chapterList.appendChild(summaryItem);
    }

    // 全局函数：下载单个文件
    window.downloadSingle = function(taskId, filename) {
        // 添加视觉反馈
        const button = document.querySelector(`[data-filename="${filename}"]`);
        if (button) {
            const originalContent = button.innerHTML;
            button.disabled = true;
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-1"></span>
                正在准备下载...
            `;
            
            // 短暂延迟后恢复按钮状态
            setTimeout(() => {
                button.disabled = false;
                button.innerHTML = originalContent;
            }, 2000);
        }
        
        window.location.href = `/download/${taskId}/${encodeURIComponent(filename)}`;
    };

    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`;
        alertDiv.style.borderRadius = '12px';
        alertDiv.style.border = 'none';
        alertDiv.style.boxShadow = '0 4px 20px rgba(102, 126, 234, 0.15)';
        
        const icon = type === 'error' ? 'fas fa-exclamation-triangle' : 'fas fa-check-circle';
        alertDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${icon} me-2"></i>
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // 插入到container的顶部
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // 添加动画效果
        alertDiv.classList.add('fade-in-up');
        
        // 5秒后自动消失
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => alertDiv.remove(), 300);
            }
        }, 5000);
    }

    // 文件拖拽上传增强
    const fileInput = document.getElementById('pdfFile');
    const uploadZone = document.getElementById('uploadZone');
    const uploadCard = document.querySelector('.main-upload-card');

    // 设置拖拽事件
    [uploadZone, uploadCard].forEach(element => {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            element.addEventListener(eventName, preventDefaults, false);
        });
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // 拖拽时的视觉效果
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        uploadZone.style.borderColor = '#667eea';
        uploadZone.style.background = 'rgba(102, 126, 234, 0.08)';
        uploadZone.style.transform = 'scale(1.02)';
        uploadZone.querySelector('.upload-zone-icon').style.color = '#667eea';
        uploadZone.querySelector('.upload-zone-icon').style.transform = 'scale(1.1)';
    }

    function unhighlight(e) {
        uploadZone.style.borderColor = '#a0aec0';
        uploadZone.style.background = 'rgba(102, 126, 234, 0.02)';
        uploadZone.style.transform = 'scale(1)';
        uploadZone.querySelector('.upload-zone-icon').style.color = '#a0aec0';
        uploadZone.querySelector('.upload-zone-icon').style.transform = 'scale(1)';
    }

    // 点击上传区域触发文件选择
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });

    uploadZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            const file = files[0];
            if (file.type === 'application/pdf') {
                fileInput.files = files;
                updateUploadZoneWithFile(file);
                showAlert(`文件已选择: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`, 'success');
            } else {
                showAlert('请选择PDF文件格式的文档', 'error');
            }
        }
    }

    // 文件选择时更新上传区域显示
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            updateUploadZoneWithFile(file);
        }
    });

    function updateUploadZoneWithFile(file) {
        const sizeText = (file.size / 1024 / 1024).toFixed(2);
        uploadZone.innerHTML = `
            <div class="text-center">
                <i class="fas fa-file-pdf text-danger mb-3" style="font-size: 3rem;"></i>
                <h5 class="text-success">文件已选择</h5>
                <p class="mb-2"><strong>${file.name}</strong></p>
                <p class="text-muted">文件大小: ${sizeText}MB</p>
                <small class="text-muted">
                    <i class="fas fa-info-circle me-1"></i>
                    点击下方按钮开始处理，或重新选择其他文件
                </small>
            </div>
        `;
        uploadZone.style.borderColor = '#48bb78';
        uploadZone.style.background = 'rgba(72, 187, 120, 0.05)';
    }

    // 添加CSS动画
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(-20px); }
        }
        
        .summary-item {
            background: rgba(72, 187, 120, 0.08) !important;
            border: 1px solid rgba(72, 187, 120, 0.2) !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            margin-top: 1rem !important;
        }
        
        .summary-content {
            font-size: 1.1rem;
            color: #2d3748;
        }
        
        .download-chapter-btn .btn-content {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .download-chapter-btn .btn-subtext {
            font-size: 0.7rem;
            opacity: 0.8;
        }
    `;
    document.head.appendChild(style);
});