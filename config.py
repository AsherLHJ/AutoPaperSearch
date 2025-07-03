# 控制是否保存完整命令行输出的变量
save_full_log = True

# 控制是否在提示词中包含要求和关键词
include_requirements_in_prompt = True  # 是否在提示词中包含要求
include_keywords_in_prompt = False      # 是否在提示词中包含关键词

# 研究问题
ResearchQuestion = "Explore the caption / subtitle design"

# 要求（对论文筛选的额外要求）
Requirements = """
1. Should conduct user study.
2. Should display subtitle / caption.
"""
# 示例：Requirements = "必须包含用户研究或实验评估"

# 关键词（英文逗号分隔）
Keywords = ""

# 系统提示词 - 用于判断论文相关性
system_prompt = """你是一个学术论文相关性判断专家。你需要判断论文是否与用户的研究问题要找的答案相关。

判断标准（按照数字顺序依次判断）：
1. 如果你判断摘要的内容与用户的研究问题的相关性很高，则相关。不进入下一步判断。否则进入下一步判断。
2. 如果用户给出的#要求#为空，则跳过该步骤。如果你判断摘要的内容符合用户的要求，则相关。不进入下一步判断。否则进入下一步判断。
3. 如果用户给出的#关键词#为空，则跳过该步骤。如果你判断摘要的内容与用户的研究问题的可能答案相关性很不高，但你判断正文极有可能包含关键词，且猜测正文与用户的研究问题相关性很高，则相关。否则不相关。

重要说明：
- 关键词不区分大小写
- 注意同义词、缩写词的匹配

你必须以JSON格式输出判断结果。

输出格式示例（相关）：
{
    "relevant": "Y",
    "reason": "论文探讨了VST技术在混合现实应用中的使用"
}

输出格式示例（不相关）：
{
    "relevant": "N", 
    "reason": "论文仅涉及OST技术，未提及VST或视频透视技术"
}

注意：relevant字段只能是"Y"或"N"，reason字段必须是一句简短精炼的理由。
"""

# DeepSeek API 价格配置（单位：元/百万tokens）
# deepseek-chat 标准时段价格（北京时间 08:30-00:30）
deepseek_chat_standard_prices = {
    'input_cache_hit': 0.5,     # 输入（缓存命中）
    'input_cache_miss': 2.0,    # 输入（缓存未命中）
    'output': 8.0               # 输出
}

# deepseek-chat 优惠时段价格（北京时间 00:30-08:30）
deepseek_chat_discount_prices = {
    'input_cache_hit': 0.25,    # 输入（缓存命中）
    'input_cache_miss': 1.0,    # 输入（缓存未命中）
    'output': 4.0               # 输出
}

# deepseek-reasoner 标准时段价格（北京时间 08:30-00:30）
deepseek_reasoner_standard_prices = {
    'input_cache_hit': 1.0,     # 输入（缓存命中）
    'input_cache_miss': 4.0,    # 输入（缓存未命中）
    'output': 16.0              # 输出
}

# deepseek-reasoner 优惠时段价格（北京时间 00:30-08:30）
deepseek_reasoner_discount_prices = {
    'input_cache_hit': 0.25,    # 输入（缓存命中）
    'input_cache_miss': 1.0,    # 输入（缓存未命中）
    'output': 4.0               # 输出
}

# DeepSeek API 模型名称
model_name = 'deepseek-chat'

# DeepSeek API base URL
api_base_url = "https://api.deepseek.com"

# API密钥列表（将从APIKey文件夹中的txt文件自动加载）
API_KEYS = []
# 原始密钥已移除，请将密钥保存在APIKey文件夹中的txt文件里
# 格式：每行一个密钥，例如：
# sk-e1f2d3556e1f2d3556e1f2d3556e1f2d
# sk-e1f2d3556e1f2d3556e1f2d3556e1f2d