import os
from ..config import config_loader as config
from ..log import utils
from language import language

def load_api_keys_from_files():
    """
    从APIKey目录下读取所有txt文件中的API密钥，并更新config.API_KEYS
    每个txt文件中的API keys格式为每行一个key
    """
    # 使用config中定义的APIKEY_FOLDER路径
    api_key_folder = config.APIKEY_FOLDER
    
    # 清空现有的API_KEYS列表
    config.API_KEYS.clear()
    
    # 检查APIKey文件夹是否存在
    if not os.path.exists(api_key_folder):
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang['apikey_folder_not_exist'].format(path=api_key_folder))
        utils.print_and_log(lang['creating_apikey_folder'])
        os.makedirs(api_key_folder)
        return
    
    # 统计读取的key数量
    total_keys_loaded = 0
    
    # 遍历APIKey文件夹中的所有txt文件
    txt_files = [f for f in os.listdir(api_key_folder) if f.endswith('.txt')]
    
    if not txt_files:
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang['no_txt_files_found'].format(path=api_key_folder))
        return
    
    for filename in txt_files:
        file_path = os.path.join(api_key_folder, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # 读取文件中的每一行
                for line in file:
                    # 去除空白字符
                    key = line.strip()
                    # 只添加非空的key
                    if key and key.startswith('sk-'):
                        config.API_KEYS.append(key)
                        total_keys_loaded += 1
        except Exception as e:
            lang = language.get_text(config.LANGUAGE)
            utils.print_and_log(lang['read_file_error'].format(filename=filename, error=str(e)))
    
    # 打印加载结果
    lang = language.get_text(config.LANGUAGE)
    utils.print_and_log(lang['api_keys_loaded'].format(files=len(txt_files), keys=total_keys_loaded))
    
    # 如果没有加载到任何key，给出警告
    if total_keys_loaded == 0:
        utils.print_and_log(lang['no_valid_api_keys'])
        utils.print_and_log(lang['api_key_format_hint'])

def print_loaded_keys():
    """
    打印当前加载的API密钥数量（不显示具体内容）
    """
    lang = language.get_text(config.LANGUAGE)
    if config.API_KEYS:
        utils.print_and_log(lang['current_api_keys_loaded'].format(count=len(config.API_KEYS)))
    else:
        utils.print_and_log(lang['no_api_keys_loaded'])
