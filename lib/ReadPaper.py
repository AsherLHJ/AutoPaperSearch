import os
import re
from . import Data  # 更新导入路径
from . import utils

def read_bib_files():
    """
    遍历Data文件夹及其子文件夹中的bib文件，提取每篇论文的信息并存入Data.py的paper_data字典中
    """
    # 设置Data文件夹路径 - 需要回到上一级目录
    data_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Data')
    
    # 检查Data文件夹是否存在
    if not os.path.exists(data_folder):
        utils.print_and_log(f"错误：Data文件夹不存在: {data_folder}")
        return
    
    # 初始化论文计数器，用作字典索引
    paper_index = 1
    
    # 统计信息
    total_folders = 0
    total_files = 0
    
    # 遍历Data文件夹中的所有子文件夹
    for folder_name in os.listdir(data_folder):
        folder_path = os.path.join(data_folder, folder_name)
        
        # 跳过非文件夹项
        if not os.path.isdir(folder_path):
            continue
            
        total_folders += 1
        utils.print_and_log(f"\n处理文件夹: {folder_name}")
        
        # 在每个子文件夹中查找.bib文件
        folder_file_count = 0
        for filename in os.listdir(folder_path):
            if filename.endswith('.bib'):
                file_path = os.path.join(folder_path, filename)
                total_files += 1
                folder_file_count += 1
                utils.print_and_log(f"  处理文件: {filename}")
                
                # 读取bib文件内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                except Exception as e:
                    utils.print_and_log(f"  警告：读取文件 {filename} 失败: {str(e)}")
                    continue
                
                # 使用正则表达式匹配每个论文条目
                # bib文件中的每个条目通常以@开头，以}结尾
                paper_entries = re.findall(r'@\w+\{[^@]*?\}(?=\s*(?:@|$))', content, re.DOTALL)
                            
                # 处理每篇论文的基本信息并存入Data.paper_data字典
                for entry in paper_entries:
                    # 提取标题
                    # 使用更严格的正则表达式，确保title是独立的标签
                    # (?:^|\n) 表示行首或换行符
                    # \s* 表示可能的空白字符
                    # title 是精确匹配的标签名
                    # \s*=\s* 表示等号前后可能的空白字符
                    title_match = re.search(r'(?:^|\n)\s*title\s*=\s*\{([^\}]*)\}', entry, re.MULTILINE)
                    title = title_match.group(1) if title_match else "标题未知"
                    
                    # 提取摘要
                    abstract_match = re.search(r'abstract\s*=\s*\{([^\}]*)\}', entry)
                    abstract = abstract_match.group(1) if abstract_match else "摘要未知"
                    
                    # 将论文信息存入Data.paper_data字典
                    Data.paper_data[paper_index] = {
                        'title': title,
                        'abstract': abstract,
                        'entry': entry,
                        'source_folder': folder_name,  # 记录来源文件夹
                        'source_file': filename  # 记录来源文件
                    }
                    
                    paper_index += 1
        
        if folder_file_count > 0:
            utils.print_and_log(f"  从 {folder_name} 文件夹中读取了 {folder_file_count} 个.bib文件")
        else:
            utils.print_and_log(f"  警告：{folder_name} 文件夹中没有找到.bib文件")
    
    # 输出统计信息
    utils.print_and_log(f"\n读取完成！")
    utils.print_and_log(f"共处理 {total_folders} 个文件夹")
    utils.print_and_log(f"共读取 {total_files} 个.bib文件")
    utils.print_and_log(f"共提取 {len(Data.paper_data)} 篇论文")