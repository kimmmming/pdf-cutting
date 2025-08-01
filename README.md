# PDF章节分割工具

一个用于将PDF文档按章节自动分割为更小PDF文件的Python工具。

## 功能特性

- 🔍 智能检测中英文章节标题
- 📄 支持多种章节标题格式（第一章、Chapter 1、1.等）
- 🛡️ 完善的错误处理和资源管理
- 📁 自动创建输出目录和文件名清理
- ⚙️ 支持自定义章节匹配模式
- 💻 命令行界面，易于使用
- 🔄 当未找到章节时自动按页数均匀分割

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法
```bash
python pdf_chapter_splitter.py document.pdf
```

### 指定输出目录
```bash
python pdf_chapter_splitter.py document.pdf -o output_folder
```

### 预览章节（不实际分割）
```bash
python pdf_chapter_splitter.py --dry-run document.pdf
```

### 添加自定义章节模式
```bash
python pdf_chapter_splitter.py document.pdf --pattern "^附录.*"
```

### 详细输出
```bash
python pdf_chapter_splitter.py document.pdf --verbose
```

## 支持的章节格式

- 中文：第一章、第1章、第1节
- 英文：Chapter 1、Chapter One
- 数字：1.、2.、3.
- 自定义模式（通过--pattern参数）

## 输出文件命名

- 格式：`第01章_章节标题.pdf`
- 自动清理无效字符
- 避免文件名冲突

## 命令行参数

- `pdf_path`: PDF文件路径（必需）
- `-o, --output`: 输出目录（可选）
- `-p, --pages`: 均匀分割时每部分的页数（默认10页）
- `--pattern`: 添加自定义章节匹配模式（可重复使用）
- `--dry-run`: 预览模式，不实际分割文件
- `--verbose`: 详细输出模式

## 示例

```bash
# 基本分割
python pdf_chapter_splitter.py book.pdf

# 自定义输出目录和页数
python pdf_chapter_splitter.py book.pdf -o chapters -p 15

# 添加多个自定义模式
python pdf_chapter_splitter.py book.pdf --pattern "^序言" --pattern "^目录"
```