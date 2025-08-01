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
        uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>处理中...';
        progressSection.style.display = 'block';
        resultSection.style.display = 'none';
        updateProgress(0, '正在上传文件...');
    }

    function hideProgress() {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fas fa-scissors me-2"></i>开始分割PDF';
        progressSection.style.display = 'none';
    }

    function updateProgress(percent, text) {
        progressBar.style.width = percent + '%';
        progressText.textContent = text;
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
            
            listItem.innerHTML = `
                <div class="chapter-info">
                    <div class="chapter-title">
                        <i class="fas fa-file-pdf text-danger me-2"></i>
                        ${filename}
                    </div>
                    <div class="chapter-size">
                        <i class="fas fa-info-circle me-1"></i>
                        第 ${index + 1} 个章节
                    </div>
                </div>
                <div class="chapter-actions">
                    <button class="btn btn-outline-primary btn-sm" onclick="downloadSingle('${taskId}', '${filename}')">
                        <i class="fas fa-download me-1"></i>下载
                    </button>
                </div>
            `;
            
            chapterList.appendChild(listItem);
        });
        
        // 添加总结信息
        const summaryItem = document.createElement('div');
        summaryItem.className = 'list-group-item list-group-item-info text-center';
        summaryItem.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            共分割出 <strong>${files.length}</strong> 个章节文件
        `;
        chapterList.appendChild(summaryItem);
    }

    // 全局函数：下载单个文件
    window.downloadSingle = function(taskId, filename) {
        window.location.href = `/download/${taskId}/${encodeURIComponent(filename)}`;
    };

    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // 插入到container的顶部
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // 3秒后自动消失
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }

    // 文件拖拽上传
    const fileInput = document.getElementById('pdfFile');
    const uploadCard = document.querySelector('.card');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadCard.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadCard.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadCard.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        uploadCard.style.backgroundColor = '#e3f2fd';
        uploadCard.style.borderColor = '#2196f3';
    }

    function unhighlight(e) {
        uploadCard.style.backgroundColor = '';
        uploadCard.style.borderColor = '';
    }

    uploadCard.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            const file = files[0];
            if (file.type === 'application/pdf') {
                fileInput.files = files;
                showAlert('文件已选择: ' + file.name, 'success');
            } else {
                showAlert('请选择PDF文件', 'error');
            }
        }
    }
});