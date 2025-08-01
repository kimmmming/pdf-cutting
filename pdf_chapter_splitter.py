import PyPDF2
import re
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import argparse
import logging
from contextlib import contextmanager


class PDFChapterSplitter:
    def __init__(self, pdf_path: str, output_dir: str = None):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir) if output_dir else self.pdf_path.parent / f"{self.pdf_path.stem}_chapters"
        self._pdf_file = None
        self.reader = None
        self.chapter_patterns = [
            r'^第[一二三四五六七八九十\d]+章',  # 中文章节标题
            r'^Chapter\s+\d+',  # 英文章节标题
            r'^\d+\.\s+\S+',  # 数字章节 (1. 2. 3.) - 需要后面有内容
            r'^第\d+节',  # 中文节标题
            r'^第[一二三四五六七八九十\d]+部分',  # 中文部分标题
            r'^Section\s+\d+',  # 英文节标题
        ]
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def _pdf_context(self):
        """上下文管理器，确保PDF文件正确关闭"""
        try:
            self._pdf_file = open(self.pdf_path, 'rb')
            self.reader = PyPDF2.PdfReader(self._pdf_file)
            yield self.reader
        except FileNotFoundError:
            self.logger.error(f"PDF文件不存在: {self.pdf_path}")
            raise
        except PyPDF2.errors.PdfReadError as e:
            self.logger.error(f"PDF文件损坏或格式错误: {e}")
            raise
        except PermissionError:
            self.logger.error(f"没有权限访问文件: {self.pdf_path}")
            raise
        except Exception as e:
            self.logger.error(f"加载PDF文件失败: {e}")
            raise
        finally:
            if self._pdf_file:
                self._pdf_file.close()
                self._pdf_file = None
                self.reader = None
    
    def validate_pdf(self) -> bool:
        """验证PDF文件是否有效"""
        try:
            if not self.pdf_path.exists():
                self.logger.error(f"PDF文件不存在: {self.pdf_path}")
                return False
                
            if not self.pdf_path.is_file():
                self.logger.error(f"路径不是文件: {self.pdf_path}")
                return False
                
            if self.pdf_path.stat().st_size == 0:
                self.logger.error("PDF文件为空")
                return False
                
            with self._pdf_context() as reader:
                if len(reader.pages) == 0:
                    self.logger.error("PDF文件没有页面")
                    return False
                    
                # 尝试读取第一页以验证文件完整性
                try:
                    reader.pages[0].extract_text()
                except Exception as e:
                    self.logger.warning(f"第一页文本提取可能有问题: {e}")
                    
            return True
            
        except Exception as e:
            self.logger.error(f"PDF验证失败: {e}")
            return False
    
    def extract_text_from_page(self, reader, page_num: int) -> str:
        """从指定页面提取文本"""
        try:
            if page_num >= len(reader.pages):
                self.logger.warning(f"页面索引超出范围: {page_num}")
                return ""
                
            page = reader.pages[page_num]
            text = page.extract_text()
            
            # 处理可能的编码问题
            if text:
                # 清理文本中的异常字符
                text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
                # 统一换行符
                text = re.sub(r'\r\n|\r', '\n', text)
            
            return text or ""
            
        except Exception as e:
            self.logger.warning(f"提取第{page_num + 1}页文本失败: {e}")
            return ""
    
    def find_chapter_breaks(self) -> List[Tuple[int, str]]:
        """查找章节分割点"""
        chapter_breaks = []
        
        try:
            with self._pdf_context() as reader:
                total_pages = len(reader.pages)
                self.logger.info(f"开始扫描 {total_pages} 页以查找章节...")
                
                for page_num in range(total_pages):
                    text = self.extract_text_from_page(reader, page_num)
                    if not text.strip():
                        continue
                        
                    lines = text.split('\n')
                    
                    # 检查页面前10行和可能的标题位置
                    lines_to_check = lines[:10]
                    
                    # 如果页面很长，也检查中间部分可能的标题
                    if len(lines) > 20:
                        mid_start = len(lines) // 2 - 2
                        mid_end = len(lines) // 2 + 3
                        lines_to_check.extend(lines[mid_start:mid_end])
                    
                    for line_idx, line in enumerate(lines_to_check):
                        line = line.strip()
                        if not line or len(line) < 2:
                            continue
                        
                        # 跳过过长的行（可能是正文）
                        if len(line) > 100:
                            continue
                            
                        for pattern in self.chapter_patterns:
                            if re.match(pattern, line, re.IGNORECASE):
                                # 避免重复检测同一页的章节
                                if chapter_breaks and chapter_breaks[-1][0] == page_num:
                                    break
                                    
                                chapter_title = line[:60].strip()  # 增加标题长度限制
                                chapter_breaks.append((page_num, chapter_title))
                                self.logger.info(f"发现章节: 第{page_num + 1}页 - {chapter_title}")
                                break
                        else:
                            continue
                        break  # 找到章节后跳出行循环
                
                # 去重并排序
                chapter_breaks = list(dict.fromkeys(chapter_breaks))  # 去重保持顺序
                chapter_breaks.sort(key=lambda x: x[0])  # 按页码排序
                
                self.logger.info(f"总共找到 {len(chapter_breaks)} 个章节")
                
        except Exception as e:
            self.logger.error(f"查找章节时出错: {e}")
            return []
        
        return chapter_breaks
    
    def create_output_directory(self) -> bool:
        """创建输出目录"""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"输出目录已创建: {self.output_dir}")
            return True
        except PermissionError:
            self.logger.error(f"没有权限创建目录: {self.output_dir}")
            return False
        except Exception as e:
            self.logger.error(f"创建输出目录失败: {e}")
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除无效字符"""
        if not filename:
            return "未命名章节"
            
        # Windows和Unix系统的无效字符
        invalid_chars = r'<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 移除控制字符
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        # 移除前后空格和点号（Windows不允许以点结尾）
        filename = filename.strip('. ')
        
        # 处理保留名称（Windows）
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
        if filename.upper() in reserved_names:
            filename = f"_{filename}"
        
        # 限制文件名长度（考虑文件扩展名）
        max_length = 200  # 为扩展名和路径留出空间
        if len(filename) > max_length:
            filename = filename[:max_length]
        
        return filename or "未命名章节"
    
    def split_pdf_by_chapters(self) -> bool:
        """按章节分割PDF"""
        # 验证PDF文件
        if not self.validate_pdf():
            return False
        
        # 创建输出目录
        if not self.create_output_directory():
            return False
        
        # 查找章节分割点
        chapter_breaks = self.find_chapter_breaks()
        
        if not chapter_breaks:
            self.logger.warning("未找到章节标记，尝试按页数均匀分割...")
            return self.split_pdf_evenly()
        
        # 验证章节分割点的合理性
        if len(chapter_breaks) == 1:
            self.logger.warning("只找到一个章节，可能检测有误，尝试按页数分割...")
            return self.split_pdf_evenly()
        
        success = True
        try:
            with self._pdf_context() as reader:
                total_pages = len(reader.pages)
                
                for i, (start_page, title) in enumerate(chapter_breaks):
                    # 计算结束页面
                    if i + 1 < len(chapter_breaks):
                        end_page = chapter_breaks[i + 1][0] - 1
                    else:
                        end_page = total_pages - 1
                    
                    # 确保页面范围有效
                    if start_page > end_page or start_page >= total_pages:
                        self.logger.warning(f"章节 {i+1} 页面范围无效: {start_page}-{end_page}")
                        continue
                    
                    if not self.extract_pages_to_pdf(reader, start_page, end_page, title, i + 1):
                        success = False
                        
                if success:
                    self.logger.info(f"PDF按章节分割完成！输出目录: {self.output_dir}")
                else:
                    self.logger.warning("部分章节分割失败，请检查输出目录")
                    
        except Exception as e:
            self.logger.error(f"分割过程中出错: {e}")
            return False
        
        return success
    
    def extract_pages_to_pdf(self, reader, start_page: int, end_page: int, title: str, chapter_num: int) -> bool:
        """提取指定页面范围到新的PDF文件"""
        try:
            writer = PyPDF2.PdfWriter()
            pages_added = 0
            
            for page_num in range(start_page, end_page + 1):
                if page_num < len(reader.pages):
                    try:
                        page = reader.pages[page_num]
                        writer.add_page(page)
                        pages_added += 1
                    except Exception as e:
                        self.logger.warning(f"添加第{page_num + 1}页时出错: {e}")
                        continue
            
            if pages_added == 0:
                self.logger.error(f"章节 {chapter_num} 没有成功添加任何页面")
                return False
            
            clean_title = self.sanitize_filename(title)
            filename = f"第{chapter_num:02d}章_{clean_title}.pdf"
            output_path = self.output_dir / filename
            
            # 确保文件名不会重复
            counter = 1
            original_path = output_path
            while output_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                output_path = original_path.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            # 验证输出文件
            if not output_path.exists() or output_path.stat().st_size == 0:
                self.logger.error(f"输出文件创建失败或为空: {output_path}")
                return False
            
            self.logger.info(f"已创建: {output_path.name} (第{start_page + 1}-{end_page + 1}页, {pages_added}页)")
            return True
            
        except Exception as e:
            self.logger.error(f"创建章节PDF失败: {e}")
            return False
    
    def split_pdf_evenly(self, pages_per_section: int = 10) -> bool:
        """按页数均匀分割PDF"""
        if pages_per_section <= 0:
            pages_per_section = 10
            
        try:
            with self._pdf_context() as reader:
                total_pages = len(reader.pages)
                section_num = 1
                success = True
                
                self.logger.info(f"开始按 {pages_per_section} 页/节均匀分割 PDF...")
                
                for start_page in range(0, total_pages, pages_per_section):
                    end_page = min(start_page + pages_per_section - 1, total_pages - 1)
                    
                    writer = PyPDF2.PdfWriter()
                    pages_added = 0
                    
                    for page_num in range(start_page, end_page + 1):
                        try:
                            writer.add_page(reader.pages[page_num])
                            pages_added += 1
                        except Exception as e:
                            self.logger.warning(f"添加第{page_num + 1}页时出错: {e}")
                            continue
                    
                    if pages_added == 0:
                        self.logger.warning(f"第{section_num}部分没有成功添加任何页面")
                        success = False
                        continue
                    
                    filename = f"第{section_num:02d}部分_第{start_page + 1}-{end_page + 1}页.pdf"
                    output_path = self.output_dir / filename
                    
                    # 处理文件名冲突
                    counter = 1
                    original_path = output_path
                    while output_path.exists():
                        stem = original_path.stem
                        suffix = original_path.suffix
                        output_path = original_path.parent / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
                    
                    # 验证输出文件
                    if not output_path.exists() or output_path.stat().st_size == 0:
                        self.logger.error(f"输出文件创建失败或为空: {output_path}")
                        success = False
                        continue
                    
                    self.logger.info(f"已创建: {output_path.name} ({pages_added}页)")
                    section_num += 1
                
                if success:
                    self.logger.info(f"PDF均匀分割完成！输出目录: {self.output_dir}")
                else:
                    self.logger.warning("部分分割失败，请检查输出目录")
                
                return success
            
        except Exception as e:
            self.logger.error(f"均匀分割PDF失败: {e}")
            return False
    
    def add_custom_pattern(self, pattern: str) -> bool:
        """添加自定义章节匹配模式"""
        if not pattern or not pattern.strip():
            self.logger.warning("空的匹配模式，已忽略")
            return False
            
        try:
            # 验证正则表达式是否有效
            re.compile(pattern)
            self.chapter_patterns.append(pattern.strip())
            self.logger.info(f"已添加自定义模式: {pattern}")
            return True
        except re.error as e:
            self.logger.error(f"无效的正则表达式模式 '{pattern}': {e}")
            return False
    
    def get_pdf_info(self) -> dict:
        """获取PDF基本信息"""
        try:
            with self._pdf_context() as reader:
                info = {
                    'total_pages': len(reader.pages),
                    'title': None,
                    'author': None,
                    'subject': None,
                    'creator': None
                }
                
                if reader.metadata:
                    info.update({
                        'title': reader.metadata.get('/Title'),
                        'author': reader.metadata.get('/Author'),
                        'subject': reader.metadata.get('/Subject'),
                        'creator': reader.metadata.get('/Creator')
                    })
                
                return info
        except Exception as e:
            self.logger.error(f"获取PDF信息失败: {e}")
            return {'total_pages': 0}


def main():
    parser = argparse.ArgumentParser(
        description='PDF章节分割工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python pdf_chapter_splitter.py document.pdf                    # 基本用法
  python pdf_chapter_splitter.py document.pdf -o output_folder   # 指定输出目录
  python pdf_chapter_splitter.py document.pdf -p 15             # 设置每节页数
  python pdf_chapter_splitter.py document.pdf --pattern "^附录.*"  # 添加自定义匹配模式
        """
    )
    
    parser.add_argument('pdf_path', help='PDF文件路径')
    parser.add_argument('-o', '--output', help='输出目录（默认为PDF文件名_chapters）', default=None)
    parser.add_argument('-p', '--pages', type=int, help='未找到章节时每节的页数（默认10页）', default=10)
    parser.add_argument('--pattern', help='添加自定义章节匹配模式（正则表达式）', action='append')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细输出')
    parser.add_argument('--dry-run', action='store_true', help='仅显示会找到的章节，不实际分割')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 验证输入参数
    if args.pages <= 0:
        print("错误: 页数必须大于0")
        sys.exit(1)
    
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"错误: 文件 '{pdf_path}' 不存在")
        sys.exit(1)
    
    if not pdf_path.is_file():
        print(f"错误: '{pdf_path}' 不是文件")
        sys.exit(1)
    
    try:
        splitter = PDFChapterSplitter(str(pdf_path), args.output)
        
        # 添加自定义模式
        if args.pattern:
            valid_patterns = 0
            for pattern in args.pattern:
                if splitter.add_custom_pattern(pattern):
                    valid_patterns += 1
            
            if valid_patterns == 0:
                print("警告: 没有有效的自定义模式被添加")
        
        # 如果是演练模式，只显示章节检测结果
        if args.dry_run:
            if not splitter.validate_pdf():
                print("PDF文件验证失败")
                sys.exit(1)
            
            chapter_breaks = splitter.find_chapter_breaks()
            if chapter_breaks:
                print(f"\n找到 {len(chapter_breaks)} 个章节:")
                for i, (page, title) in enumerate(chapter_breaks, 1):
                    print(f"  {i}. 第{page + 1}页: {title}")
            else:
                print("未找到章节标记")
            return
        
        # 执行分割
        success = splitter.split_pdf_by_chapters()
        
        if not success:
            print("章节分割失败，尝试按页数均匀分割...")
            success = splitter.split_pdf_evenly(args.pages)
        
        if success:
            print(f"分割完成！输出目录: {splitter.output_dir}")
        else:
            print("分割失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"程序运行出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()