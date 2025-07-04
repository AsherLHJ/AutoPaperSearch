import json
import os

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

# 全局变量，用于存储配置
save_full_log = True
include_requirements_in_prompt = True
include_keywords_in_prompt = False
DATA_FOLDER = ''
APIKEY_FOLDER = ''
RESULT_FOLDER = ''
LANGUAGE = 'zh_CN'
ResearchQuestion = ''
Requirements = ''
Keywords = ''
system_prompt = ''
deepseek_chat_standard_prices = {}
deepseek_chat_discount_prices = {}
deepseek_reasoner_standard_prices = {}
deepseek_reasoner_discount_prices = {}
model_name = ''
api_base_url = ''
API_KEYS = []

def load_config():
    """加载配置文件"""
    global save_full_log, include_requirements_in_prompt, include_keywords_in_prompt
    global DATA_FOLDER, APIKEY_FOLDER, RESULT_FOLDER, LANGUAGE
    global ResearchQuestion, Requirements, Keywords, system_prompt
    global deepseek_chat_standard_prices, deepseek_chat_discount_prices
    global deepseek_reasoner_standard_prices, deepseek_reasoner_discount_prices
    global model_name, api_base_url, API_KEYS
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 加载基本配置
        save_full_log = config.get('save_full_log', True)
        include_requirements_in_prompt = config.get('include_requirements_in_prompt', True)
        include_keywords_in_prompt = config.get('include_keywords_in_prompt', False)
        
        # 加载文件夹路径
        DATA_FOLDER = os.path.join(os.path.dirname(__file__), config.get('DATA_FOLDER', 'Data'))
        APIKEY_FOLDER = os.path.join(os.path.dirname(__file__), config.get('APIKEY_FOLDER', 'APIKey'))
        RESULT_FOLDER = os.path.join(os.path.dirname(__file__), config.get('RESULT_FOLDER', 'Result'))
        
        # 加载语言设置
        LANGUAGE = config.get('LANGUAGE', 'zh_CN')
        
        # 加载研究问题和关键词
        ResearchQuestion = config.get('ResearchQuestion', '')
        Requirements = config.get('Requirements', '')
        Keywords = config.get('Keywords', '')
        
        # 加载系统提示词
        system_prompt = config.get('system_prompt', '')
        
        # 加载价格配置
        deepseek_chat_standard_prices = config.get('deepseek_chat_standard_prices', {
            'input_cache_hit': 0.5,
            'input_cache_miss': 2.0,
            'output': 8.0
        })
        
        deepseek_chat_discount_prices = config.get('deepseek_chat_discount_prices', {
            'input_cache_hit': 0.25,
            'input_cache_miss': 1.0,
            'output': 4.0
        })
        
        deepseek_reasoner_standard_prices = config.get('deepseek_reasoner_standard_prices', {
            'input_cache_hit': 1.0,
            'input_cache_miss': 4.0,
            'output': 16.0
        })
        
        deepseek_reasoner_discount_prices = config.get('deepseek_reasoner_discount_prices', {
            'input_cache_hit': 0.25,
            'input_cache_miss': 1.0,
            'output': 4.0
        })
        
        # 加载API配置
        model_name = config.get('model_name', 'deepseek-chat')
        api_base_url = config.get('api_base_url', 'https://api.deepseek.com')
        API_KEYS = config.get('API_KEYS', [])
        
        print(f"配置文件加载成功: {CONFIG_FILE}")
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        print("使用默认配置")

def save_config():
    """保存配置到文件"""
    config = {
        'save_full_log': save_full_log,
        'include_requirements_in_prompt': include_requirements_in_prompt,
        'include_keywords_in_prompt': include_keywords_in_prompt,
        'DATA_FOLDER': os.path.basename(DATA_FOLDER),
        'APIKEY_FOLDER': os.path.basename(APIKEY_FOLDER),
        'RESULT_FOLDER': os.path.basename(RESULT_FOLDER),
        'LANGUAGE': LANGUAGE,
        'ResearchQuestion': ResearchQuestion,
        'Requirements': Requirements,
        'Keywords': Keywords,
        'system_prompt': system_prompt,
        'deepseek_chat_standard_prices': deepseek_chat_standard_prices,
        'deepseek_chat_discount_prices': deepseek_chat_discount_prices,
        'deepseek_reasoner_standard_prices': deepseek_reasoner_standard_prices,
        'deepseek_reasoner_discount_prices': deepseek_reasoner_discount_prices,
        'model_name': model_name,
        'api_base_url': api_base_url,
        'API_KEYS': API_KEYS
    }
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        print(f"配置已保存到: {CONFIG_FILE}")
    except Exception as e:
        print(f"保存配置文件失败: {e}")

# 初始加载配置
load_config()