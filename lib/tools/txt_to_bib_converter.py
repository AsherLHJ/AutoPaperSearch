#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知网文献txt格式转BibTeX格式转换工具

该工具支持将知网导出的txt格式文献文件转换为标准的BibTeX格式。
支持批量处理文件夹中的所有txt文件，并保持相同的目录结构。

作者: AutoPaperSearch
日期: 2024
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
import hashlib


class TxtToBibConverter:
    """知网txt文献格式转BibTeX格式转换器"""
    
    def __init__(self):
        self.entry_types = {
            '期刊': 'article',
            '会议': 'inproceedings',
            '学位论文': 'phdthesis',
            '图书': 'book',
            '报纸': 'article'
        }
    
    def parse_txt_file(self, file_path: str) -> List[Dict[str, str]]:
        """解析txt文件，提取文献信息
        
        Args:
            file_path: txt文件路径
            
        Returns:
            文献信息字典列表
        """
        papers = []
        current_paper = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按空行分割不同的文献条目
            entries = re.split(r'\n\s*\n', content.strip())
            
            for entry in entries:
                if not entry.strip():
                    continue
                    
                paper_info = self._parse_single_entry(entry)
                if paper_info:
                    papers.append(paper_info)
                    
        except Exception as e:
            print(f"解析文件 {file_path} 时出错: {e}")
            
        return papers
    
    def _parse_single_entry(self, entry: str) -> Optional[Dict[str, str]]:
        """解析单个文献条目
        
        Args:
            entry: 单个文献条目的文本
            
        Returns:
            文献信息字典
        """
        paper_info = {}
        lines = entry.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 解析各个字段
            if line.startswith('SrcDatabase-来源库:'):
                paper_info['source_db'] = line.split(':', 1)[1].strip()
            elif line.startswith('Title-题名:'):
                paper_info['title'] = line.split(':', 1)[1].strip()
            elif line.startswith('Author-作者:'):
                paper_info['author'] = line.split(':', 1)[1].strip()
            elif line.startswith('0rgan-单位:') or line.startswith('Organ-单位:'):
                paper_info['organization'] = line.split(':', 1)[1].strip()
            elif line.startswith('Source-文献来源:'):
                paper_info['journal'] = line.split(':', 1)[1].strip()
            elif line.startswith('Keyword-关键词:'):
                paper_info['keywords'] = line.split(':', 1)[1].strip()
            elif line.startswith('Summary-摘要:'):
                abstract = line.split(':', 1)[1].strip()
                # 移除可能的<正>标记
                abstract = re.sub(r'^<正>', '', abstract)
                paper_info['abstract'] = abstract
        
        return paper_info if paper_info else None
    
    def _generate_cite_key(self, paper_info: Dict[str, str]) -> str:
        """生成BibTeX引用键
        
        Args:
            paper_info: 文献信息字典
            
        Returns:
            引用键字符串
        """
        # 使用作者姓名和标题的哈希值生成唯一的引用键
        author = paper_info.get('author', 'unknown')
        title = paper_info.get('title', 'untitled')
        
        # 取第一个作者的姓名
        first_author = author.split(';')[0].split(',')[0].strip()
        
        # 生成简短的哈希值
        hash_input = f"{first_author}_{title}"
        hash_value = hashlib.md5(hash_input.encode('utf-8')).hexdigest()[:8]
        
        # 清理作者姓名，只保留字母和数字
        clean_author = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', first_author)
        if len(clean_author) > 10:
            clean_author = clean_author[:10]
        
        return f"{clean_author}_{hash_value}"
    
    def _format_authors(self, authors: str) -> str:
        """格式化作者字段
        
        Args:
            authors: 原始作者字符串
            
        Returns:
            BibTeX格式的作者字符串
        """
        # 分割多个作者
        author_list = [author.strip() for author in authors.split(';') if author.strip()]
        
        # 对于中文作者名，保持原样；对于英文作者名，可以考虑格式化
        formatted_authors = []
        for author in author_list:
            # 移除可能的单位信息（在作者名后面）
            author = re.sub(r'\s*\d+.*$', '', author)
            formatted_authors.append(author.strip())
        
        return ' and '.join(formatted_authors)
    
    def convert_to_bib(self, paper_info: Dict[str, str]) -> str:
        """将文献信息转换为BibTeX格式
        
        Args:
            paper_info: 文献信息字典
            
        Returns:
            BibTeX格式字符串
        """
        # 确定文献类型
        source_db = paper_info.get('source_db', '期刊')
        entry_type = self.entry_types.get(source_db, 'article')
        
        # 生成引用键
        cite_key = self._generate_cite_key(paper_info)
        
        # 构建BibTeX条目
        bib_entry = f"@{entry_type}{{{cite_key},\n"
        
        # 添加各个字段
        if 'title' in paper_info:
            bib_entry += f"  title = {{{paper_info['title']}}},\n"
        
        if 'author' in paper_info:
            formatted_authors = self._format_authors(paper_info['author'])
            bib_entry += f"  author = {{{formatted_authors}}},\n"
        
        if 'journal' in paper_info:
            bib_entry += f"  journal = {{{paper_info['journal']}}},\n"
        
        if 'keywords' in paper_info:
            bib_entry += f"  keywords = {{{paper_info['keywords']}}},\n"
        
        if 'abstract' in paper_info:
            # 清理摘要文本
            abstract = paper_info['abstract'].replace('{', '').replace('}', '')
            bib_entry += f"  abstract = {{{abstract}}},\n"
        
        if 'organization' in paper_info:
            bib_entry += f"  note = {{单位: {paper_info['organization']}}},\n"
        
        # 移除最后的逗号并添加结束括号
        bib_entry = bib_entry.rstrip(',\n') + '\n}\n'
        
        return bib_entry
    
    def convert_file(self, input_file: str, output_file: str) -> bool:
        """转换单个文件
        
        Args:
            input_file: 输入txt文件路径
            output_file: 输出bib文件路径
            
        Returns:
            转换是否成功
        """
        try:
            # 解析txt文件
            papers = self.parse_txt_file(input_file)
            
            if not papers:
                print(f"警告: 文件 {input_file} 中没有找到有效的文献信息")
                return False
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # 写入BibTeX文件
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, paper in enumerate(papers):
                    if i > 0:
                        f.write('\n')  # 在条目之间添加空行
                    bib_entry = self.convert_to_bib(paper)
                    f.write(bib_entry)
            
            print(f"成功转换: {input_file} -> {output_file} ({len(papers)} 条文献)")
            return True
            
        except Exception as e:
            print(f"转换文件 {input_file} 时出错: {e}")
            return False
    
    def convert_directory(self, source_dir: str, target_dir: str) -> None:
        """批量转换目录中的所有txt文件
        
        Args:
            source_dir: 源目录路径
            target_dir: 目标目录路径
        """
        source_path = Path(source_dir)
        target_path = Path(target_dir)
        
        if not source_path.exists():
            print(f"错误: 源目录 {source_dir} 不存在")
            return
        
        # 确保目标目录存在
        target_path.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        total_files = 0
        success_files = 0
        
        # 遍历源目录中的所有txt文件
        for txt_file in source_path.rglob('*.txt'):
            total_files += 1
            
            # 计算相对路径
            relative_path = txt_file.relative_to(source_path)
            
            # 构建输出文件路径（将.txt替换为.bib）
            output_file = target_path / relative_path.with_suffix('.bib')
            
            # 转换文件
            if self.convert_file(str(txt_file), str(output_file)):
                success_files += 1
        
        print(f"\n转换完成: {success_files}/{total_files} 个文件转换成功")


def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("使用方法: python txt_to_bib_converter.py <源目录> <目标目录>")
        print("示例: python txt_to_bib_converter.py C:/path/to/source C:/path/to/target")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    target_dir = sys.argv[2]
    
    converter = TxtToBibConverter()
    converter.convert_directory(source_dir, target_dir)


if __name__ == '__main__':
    main()