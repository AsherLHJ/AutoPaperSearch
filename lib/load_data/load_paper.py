import os
import re
from ..process import data
from ..log import utils
from ..config import config_loader as config

def extract_year_from_filename(filename):
    """
    从文件名中提取年份
    例如：CHI2016.bib -> 2016, IEEEVR2023.bib -> 2023
    如果没有找到年份，返回None
    """
    # 使用正则表达式匹配4位数字的年份
    year_match = re.search(r'(19|20)\d{2}', filename)
    if year_match:
        return int(year_match.group())
    return None

def is_file_in_year_range(filename):
    """
    检查文件是否在指定的年份范围内
    """
    # 如果设置为包含所有年份，则接受所有文件
    if config.INCLUDE_ALL_YEARS:
        return True
    
    # 提取文件名中的年份
    year = extract_year_from_filename(filename)
    
    # 如果没有年份信息，根据INCLUDE_ALL_YEARS设置决定
    if year is None:
        return False
    
    # 检查年份是否在范围内
    return config.YEAR_RANGE_START <= year <= config.YEAR_RANGE_END

def get_subfolders():
    """
    获取Data文件夹下的所有子文件夹名称
    """
    from ..config import config_loader as config
    data_folder = config.DATA_FOLDER
    
    if not os.path.exists(data_folder) or not os.path.isdir(data_folder):
        return []
        
    try:
        subfolders = [f for f in os.listdir(data_folder) if os.path.isdir(os.path.join(data_folder, f))]
        return subfolders
    except OSError as e:
        from language import language
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang['data_folder_read_error'].format(error=e))
        return []

def read_bib_files(selected_folders=None):
    """
    遍历Data文件夹及其子文件夹中的bib文件，提取每篇论文的信息并存入Data.py的paper_data字典中
    """
    # 使用config_loader中定义的DATA_FOLDER路径
    from ..config import config_loader as config
    from language import language
    data_folder = config.DATA_FOLDER
    lang = language.get_text(config.LANGUAGE)
    
    # 检查Data文件夹是否存在
    if not os.path.exists(data_folder):
        utils.print_and_log(lang['data_folder_not_exist'].format(path=data_folder))
        utils.print_and_log(lang['creating_data_folder'])
        os.makedirs(data_folder)
        return
    
    # 初始化论文计数器，用作字典索引
    paper_index = 1
    
    # 统计信息
    total_folders = 0
    total_files = 0
    
    # 确定要遍历的文件夹
    folder_names_to_iterate = selected_folders
    if folder_names_to_iterate is None:
        folder_names_to_iterate = get_subfolders()

    # 遍历Data文件夹中的所有子文件夹
    for folder_name in folder_names_to_iterate:
        folder_path = os.path.join(data_folder, folder_name)
        
        # 跳过非文件夹项
        if not os.path.isdir(folder_path):
            continue
            
        total_folders += 1
        utils.print_and_log(f"\n{lang['processing_folder'].format(folder=folder_name)}")
        
        # 在每个子文件夹中查找.bib文件
        folder_file_count = 0
        skipped_files = 0
        for filename in os.listdir(folder_path):
            if filename.endswith('.bib'):
                # 检查文件是否在年份范围内
                if not is_file_in_year_range(filename):
                    year = extract_year_from_filename(filename)
                    if year is not None:
                        utils.print_and_log(f"  {lang['skip_file_year'].format(filename=filename, year=year)}")
                    else:
                        utils.print_and_log(f"  {lang['skip_file_no_year'].format(filename=filename)}")
                    skipped_files += 1
                    continue
                
                file_path = os.path.join(folder_path, filename)
                total_files += 1
                folder_file_count += 1
                year = extract_year_from_filename(filename)
                year_info = lang['year_info'].format(year=year) if year else lang['no_year_info']
                utils.print_and_log(f"  {lang['processing_file'].format(filename=filename, year_info=year_info)}")
                
                # 读取bib文件内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                except Exception as e:
                    utils.print_and_log(lang['read_file_warning'].format(filename=filename, error=str(e)))
                    continue
                
                # 使用正则表达式匹配每个论文条目
                # bib文件中的每个条目通常以@开头，以}结尾
                paper_entries = re.findall(r'@\w+\{[^@]*?\}(?=\s*(?:@|$))', content, re.DOTALL)
                utils.print_and_log(f"    {lang['found_papers'].format(count=len(paper_entries))}")
                            
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
                    
                    # 将论文信息存入data.paper_data字典
                    data.paper_data[paper_index] = {
                        'title': title,
                        'abstract': abstract,
                        'entry': entry,
                        'source_folder': folder_name,  # 记录来源文件夹
                        'source_file': filename  # 记录来源文件
                    }
                    
                    paper_index += 1
        
        if folder_file_count > 0:
            utils.print_and_log(f"  {lang['read_files_from_folder'].format(folder=folder_name, count=folder_file_count)}")
        else:
            utils.print_and_log(f"  {lang['warning_no_bib_files'].format(folder=folder_name)}")
    
    # 输出统计信息
    utils.print_and_log(f"\n{lang['read_complete']}")
    utils.print_and_log(f"{lang['total_folders_processed'].format(count=total_folders)}")
    utils.print_and_log(f"{lang['total_files_read'].format(count=total_files)}")
    utils.print_and_log(f"{lang['total_papers_extracted'].format(count=len(data.paper_data))}")