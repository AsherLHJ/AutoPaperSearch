from openai import OpenAI
import time
import json
import threading
from ..config import config_loader as config
from ..log import utils
from language import language
import os
import re

def get_available_analysis_apis():
    """
    获取可用于结果分析的API密钥
    确保预留最后两个API密钥用于结果分析
    """
    if len(config.API_KEYS) < 2:
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang.get("warning_insufficient_api_keys", "警告：API密钥数量不足，至少需要2个API密钥用于结果分析"))
        return []
    
    # 返回最后两个API密钥用于结果分析
    return config.API_KEYS[-2:]

def get_processing_apis():
    """
    获取用于论文处理的API密钥（去除最后两个用于分析的）
    """
    if len(config.API_KEYS) <= 2:
        return config.API_KEYS  # 如果只有2个或更少，全部用于处理
    
    # 返回除最后两个之外的所有API密钥
    return config.API_KEYS[:-2]

def generate_brief_summary():
    """
    生成简要总结
    使用deepseek-v3模型和第一个分析API密钥
    自动生成聚类关键词和分析结果
    """
    analysis_apis = get_available_analysis_apis()
    if not analysis_apis:
        lang = language.get_text(config.LANGUAGE)
        return {"error": lang.get("error_no_analysis_api_keys", "错误：没有可用的分析API密钥")}
    
    api_key = analysis_apis[0]  # 使用第一个分析API
    
    # 读取所有结果文件
    all_papers = read_all_result_papers()
    if not all_papers:
        lang = language.get_text(config.LANGUAGE)
        return {"error": lang.get("error_no_related_papers", "没有找到相关论文，无法生成总结")}
    
    # 根据配置语言设置确定回答语言和示例
    if config.LANGUAGE == 'en_US':
        language_instruction = "Please respond in English."
        task_instruction = "Please perform clustering analysis, categorize the papers and give less than 10 clusters and keywords, and provide statistical data analysis including counts and percentages for each category."
        example_output = """{
    "keywords": "Machine Translation, Human-Computer Interaction, Accessibility",
    "summary": "Translation Technology Papers Classification and Statistical Analysis
=== STATISTICAL OVERVIEW ===
Total Papers Analyzed: 8

=== CATEGORY BREAKDOWN ===
1. Mobile Translation Apps: 3 papers (37.5%)
   - Focus: User experience and special group needs
   - Key technologies: Real-time translation, speech processing
   
2. Subtitles & Accessibility: 2 papers (25.0%)
   - Focus: Inclusive design and accessibility
   - Key technologies: Eye tracking, adaptive display
   
3. Language Learning Tools: 1 paper (12.5%)
   - Focus: Educational applications
   - Key technologies: Multimedia integration
   
4. Cross-language Interaction: 2 papers (25.0%)
   - Focus: Communication barriers
   - Key technologies: Context-aware systems

=== KEY FINDINGS ===
1. Mobile translation apps (37.5%) represent the largest research area
2. Equal emphasis on accessibility and cross-language interaction (25% each)
3. Technology trends evolving from basic translation to context-aware experiences
4. Strong focus on marginalized groups (immigrants, refugees)

=== DATA SUMMARY ===
- Most active research area: Mobile Translation (37.5%)
- Emerging trend: Accessibility-focused design (25.0%)
- Research gap: Limited educational applications (12.5%)
..."
}"""
    else:  # zh_CN or default
        language_instruction = "请用中文回答。"
        task_instruction = "请对论文进行聚类分析、归纳分类并给出关键词(小于10组)，并提供详细的数据统计分析，包括每个类别的数量和百分比统计。"
        example_output = """{
    "keywords": "Machine Translation, Human-Computer Interaction, Accessibility",
    "summary": "翻译技术论文分类与统计分析报告
=== 统计概览 ===
论文总数：8篇

=== 分类统计 ===
1. 移动翻译应用：3篇 (37.5%)
   - 研究重点：用户体验和特殊群体需求
   - 关键技术：实时翻译、语音处理
   
2. 字幕与可访问性：2篇 (25.0%)
   - 研究重点：包容性设计和无障碍访问
   - 关键技术：眼动追踪、自适应显示
   
3. 语言学习工具：1篇 (12.5%)
   - 研究重点：教育应用
   - 关键技术：多媒体整合
   
4. 跨语言交互：2篇 (25.0%)
   - 研究重点：沟通障碍解决
   - 关键技术：情境感知系统

=== 关键发现 ===
1. 移动翻译应用(37.5%)是最大的研究领域
2. 可访问性和跨语言交互研究并重(各占25%)
3. 技术趋势从基础翻译向情境感知体验发展
4. 重点关注边缘化群体(移民、难民)的需求

=== 数据汇总 ===
- 最活跃研究领域：移动翻译 (37.5%)
- 新兴趋势：可访问性设计 (25.0%)
- 研究空白：教育应用有限 (12.5%)
..."
}"""
    
    # 构建提示词
    if config.LANGUAGE == 'en_US':
        system_prompt = f"""
The user will provide paper information. {task_instruction} {language_instruction}

IMPORTANT: You must respond ENTIRELY in English. Do not mix languages.

CRITICAL REQUIREMENTS:
1. Must categorize ALL papers into clear groups
2. Must provide exact counts and percentages for each category
3. Must include statistical overview with total paper count
4. Must analyze research trends and patterns
5. Output results in JSON format with detailed statistical summary

EXAMPLE INPUT: 
Paper 1. Title: Unmet Needs and Opportunities for Mobile Translation AI
   Abstract: Translation apps and devices are often presented in the context of providing assistance while travel...
Paper 2. Title: A View on the Viewer: Gaze-Adaptive Captions for Videos
   Abstract: Subtitles play a crucial role in cross-lingual distribution of multimedia content and help communica...
Paper 3. Title: Designing for Transient Use: A Human-in-the-loop Translation Platform for Refugees
   Abstract: Refugees undergoing resettlement in a new country post exile and migration face disruptive life chan...

EXAMPLE JSON OUTPUT:
{example_output}
"""
    else:  # zh_CN or default
        system_prompt = f"""
用户将提供论文信息。{task_instruction} {language_instruction}

重要：您必须完全用中文回答。不要混用语言。

关键要求：
1. 必须将所有论文归类到明确的组别中
2. 必须提供每个类别的确切数量和百分比
3. 必须包含论文总数的统计概览
4. 必须分析研究趋势和模式
5. 以JSON格式输出详细的统计摘要结果

示例输入: 
论文1. 标题: Unmet Needs and Opportunities for Mobile Translation AI
   摘要预览: Translation apps and devices are often presented in the context of providing assistance while travel...
论文2. 标题: A View on the Viewer: Gaze-Adaptive Captions for Videos
   摘要预览: Subtitles play a crucial role in cross-lingual distribution of multimedia content and help communica...
论文3. 标题: Designing for Transient Use: A Human-in-the-loop Translation Platform for Refugees
   摘要预览: Refugees undergoing resettlement in a new country post exile and migration face disruptive life chan...

示例JSON输出:
{example_output}
"""

    user_prompt = format_papers_for_analysis_prompt(all_papers)

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        messages = [{"role": "system", "content": system_prompt},
                   {"role": "user", "content": user_prompt}]
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            response_format={'type': 'json_object'},
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # 记录到日志
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang.get("brief_summary_generated", "简要总结生成完成，使用API: {api}..., 模型: deepseek-v3").format(api=api_key[:8]))
        
        return {
            "keywords": result.get("keywords", ""),
            "summary": result.get("summary", ""),
            "success": True
        }
        
    except Exception as e:
        lang = language.get_text(config.LANGUAGE)
        error_msg = lang.get("brief_summary_generation_error", "生成简要总结时发生错误: {error}").format(error=str(e))
        utils.print_and_log(error_msg)
        return {"error": error_msg, "success": False}

def generate_brief_summary_with_keywords(existing_keywords):
    """
    基于现有关键词生成简要总结
    使用deepseek-v3模型和第一个分析API密钥
    """
    analysis_apis = get_available_analysis_apis()
    if not analysis_apis:
        lang = language.get_text(config.LANGUAGE)
        return {"error": lang.get("error_no_analysis_api_keys", "错误：没有可用的分析API密钥")}
    
    api_key = analysis_apis[0]  # 使用第一个分析API
    
    # 读取所有结果文件
    all_papers = read_all_result_papers()
    if not all_papers:
        lang = language.get_text(config.LANGUAGE)
        return {"error": lang.get("error_no_related_papers", "没有找到相关论文，无法生成总结")}
    
    # 根据配置语言设置确定回答语言和示例
    if config.LANGUAGE == 'en_US':
        language_instruction = "Please respond in English."
        keywords_label = "Clustering keywords"
        instruction_text = "Please re-analyze and classify papers based on the provided clustering keywords. Provide detailed statistical analysis with counts and percentages."
        task_instruction = "Must perform detailed statistical analysis and categorization based on the provided keywords."
        example_output = """{
    "keywords": "Machine Translation, Human-Computer Interaction, Accessibility",
    "summary": "Re-classification and Statistical Analysis Based on Keywords
=== STATISTICAL OVERVIEW ===
Total Papers Analyzed: 8
Analysis Based on Keywords: Machine Translation, Human-Computer Interaction, Accessibility

=== KEYWORD-BASED CLASSIFICATION ===
1. Machine Translation Applications: 4 papers (50.0%)
   - Directly related to translation technology
   - Includes mobile apps, spatial translation, AI-assisted translation
   
2. Human-Computer Interaction Design: 2 papers (25.0%)
   - Focus on user interface and experience design
   - Includes adaptive captions, user agency in AI systems
   
3. Accessibility Research: 2 papers (25.0%)
   - Emphasis on inclusive design for diverse user groups
   - Includes refugee support, educational accessibility

=== COMPARATIVE ANALYSIS ===
- Keyword-focused distribution differs from general clustering
- Machine Translation now dominates (50% vs previous 37.5%)
- HCI and Accessibility equally important (25% each)
- Strong alignment with provided keyword themes

=== DATA INSIGHTS ===
- Most papers align with Machine Translation keyword (50%)
- Balanced focus on user-centered design aspects (50% total for HCI + Accessibility)
- Research emphasis matches keyword priorities
..."
}"""
    else:  # zh_CN or default
        language_instruction = "请用中文回答。"
        keywords_label = "聚类关键词"
        instruction_text = "请基于提供的聚类关键词重新进行论文分类分析。提供详细的统计分析，包括数量和百分比。"
        task_instruction = "必须基于提供的关键词进行详细的统计分析和归纳分类。"
        example_output = """{
    "keywords": "Machine Translation, Human-Computer Interaction, Accessibility",
    "summary": "基于关键词的重新分类统计分析报告
=== 统计概览 ===
论文总数：8篇
基于关键词分析：Machine Translation, Human-Computer Interaction, Accessibility

=== 基于关键词的分类统计 ===
1. 机器翻译应用：4篇 (50.0%)
   - 直接相关翻译技术研究
   - 包含移动应用、空间翻译、AI辅助翻译
   
2. 人机交互设计：2篇 (25.0%)
   - 专注用户界面和体验设计
   - 包含自适应字幕、AI系统中的用户主导性
   
3. 可访问性研究：2篇 (25.0%)
   - 强调面向多样化用户群体的包容性设计
   - 包含难民支持、教育可访问性

=== 对比分析 ===
- 基于关键词的分布与一般聚类不同
- 机器翻译现在占主导地位(50% vs 之前的37.5%)
- 人机交互和可访问性同等重要(各占25%)
- 与提供的关键词主题高度一致

=== 数据洞察 ===
- 大多数论文与机器翻译关键词匹配(50%)
- 用户中心设计方面重点平衡(人机交互+可访问性共50%)
- 研究重点与关键词优先级匹配
..."
}"""
    
    # 构建提示词
    if config.LANGUAGE == 'en_US':
        system_prompt = f"""
The user will provide paper information and clustering keywords. {task_instruction} {language_instruction}

IMPORTANT: You must respond ENTIRELY in English. Do not mix languages.

CRITICAL REQUIREMENTS:
1. Must categorize ALL papers based on the provided keywords
2. Must provide exact counts and percentages for each category  
3. Must include statistical overview with total paper count
4. Must compare with general clustering if applicable
5. Output results in JSON format with detailed statistical analysis

EXAMPLE INPUT: 
{keywords_label}: Machine Translation, Human-Computer Interaction, Accessibility

Paper 1. Title: Unmet Needs and Opportunities for Mobile Translation AI
   Abstract: Translation apps and devices are often presented in the context of providing assistance while travel...
Paper 2. Title: A View on the Viewer: Gaze-Adaptive Captions for Videos
   Abstract: Subtitles play a crucial role in cross-lingual distribution of multimedia content and help communica...
Paper 3. Title: Designing for Transient Use: A Human-in-the-loop Translation Platform for Refugees
   Abstract: Refugees undergoing resettlement in a new country post exile and migration face disruptive life chan...

EXAMPLE JSON OUTPUT:
{example_output}
"""
    else:  # zh_CN or default
        system_prompt = f"""
用户将提供论文信息和聚类关键词。{task_instruction} {language_instruction}

重要：您必须完全用中文回答。不要混用语言。

关键要求：
1. 必须基于提供的关键词对所有论文进行分类
2. 必须提供每个类别的确切数量和百分比
3. 必须包含论文总数的统计概览
4. 必须与一般聚类进行对比(如适用)
5. 以JSON格式输出详细的统计分析结果

示例输入: 
{keywords_label}：Machine Translation, Human-Computer Interaction, Accessibility

论文1. 标题: Unmet Needs and Opportunities for Mobile Translation AI
   摘要预览: Translation apps and devices are often presented in the context of providing assistance while travel...
论文2. 标题: A View on the Viewer: Gaze-Adaptive Captions for Videos
   摘要预览: Subtitles play a crucial role in cross-lingual distribution of multimedia content and help communica...
论文3. 标题: Designing for Transient Use: A Human-in-the-loop Translation Platform for Refugees
   摘要预览: Refugees undergoing resettlement in a new country post exile and migration face disruptive life chan...

示例JSON输出:
{example_output}
"""

    user_prompt = f"""{keywords_label}：{existing_keywords}

{format_papers_for_analysis_prompt(all_papers)}

{instruction_text}"""

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        messages = [{"role": "system", "content": system_prompt},
                   {"role": "user", "content": user_prompt}]
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            response_format={'type': 'json_object'},
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # 记录到日志
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang.get("keyword_based_summary_generated", "基于关键词的简要总结生成完成，使用API: {api}..., 模型: deepseek-v3").format(api=api_key[:8]))
        
        return {
            "keywords": existing_keywords,
            "summary": result.get("summary", ""),
            "success": True
        }
        
    except Exception as e:
        lang = language.get_text(config.LANGUAGE)
        error_msg = lang.get("keyword_based_summary_error", "基于关键词生成简要总结时发生错误: {error}").format(error=str(e))
        utils.print_and_log(error_msg)
        return {"error": error_msg, "success": False}

def generate_deep_summary(clustering_words):
    """
    生成深度总结
    使用deepseek-r1模型和第二个分析API密钥
    """
    analysis_apis = get_available_analysis_apis()
    if len(analysis_apis) < 2:
        lang = language.get_text(config.LANGUAGE)
        return {"error": lang.get("error_insufficient_api_keys_deep", "错误：需要至少2个API密钥用于深度分析"), "success": False}
    
    api_key = analysis_apis[1]  # 使用第二个分析API
    
    # 读取所有结果文件
    all_papers = read_all_result_papers()
    if not all_papers:
        lang = language.get_text(config.LANGUAGE)
        return {"error": lang.get("error_no_related_papers", "没有找到相关论文，无法生成总结"), "success": False}
    
    # 构建提示词
    system_prompt = """
The user will provide some paper information. Please 通过聚类分析，给出文章分类关键词，以及分类的统计结果， output them in JSON format with detailed analysis.

EXAMPLE INPUT: 
论文1. 标题: Unmet Needs and Opportunities for Mobile Translation AI
   摘要预览: Translation apps and devices are often presented in the context of providing assistance while travel...
   关键词: emerging markets, immigrants, machine translation, migrants, mobile, speech
论文2. 标题: A View on the Viewer: Gaze-Adaptive Captions for Videos
   摘要预览: Subtitles play a crucial role in cross-lingual distribution of multimedia content and help communica...
   关键词: eye tracking, gaze input, gaze-responsive display, multimedia, subtitles, video captions

EXAMPLE JSON OUTPUT:
{
    "keywords": "Machine Translation, Human-Computer Interaction, Accessibility",
    "detailed_analysis": {
        "categories": [
            {
                "name": "移动翻译技术",
                "count": 3,
                "percentage": 37.5,
                "papers": ["论文1", "论文3", "论文8"],
                "key_technologies": ["实时翻译", "语音处理", "跨语言交互"],
                "research_trends": "从基础翻译向情境感知和用户体验优化发展"
            },
            {
                "name": "多媒体字幕与可访问性",
                "count": 2,
                "percentage": 25.0,
                "papers": ["论文2", "论文9"],
                "key_technologies": ["眼动追踪", "自适应显示", "多语言字幕"],
                "research_trends": "注重用户个性化体验和包容性设计"
            }
        ],
        "research_gaps": [
            "缺乏对特定人群（如移民、难民）的深入研究",
            "技术与社会文化因素结合不够"
        ],
        "future_directions": [
            "开发更加情境感知的翻译系统",
            "加强多模态交互设计研究",
            "关注边缘化群体的技术需求"
        ],
        "methodology_analysis": {
            "experimental_design": "多采用用户研究和实验室实验相结合",
            "evaluation_metrics": "用户体验、翻译准确度、系统响应时间",
            "common_limitations": "样本规模限制、实验环境与真实使用场景差异"
        }
    },
    "summary": "详细的分类统计和深度分析结果..."
}
"""

    user_prompt = f"""聚类关键词：{clustering_words}

{format_papers_for_analysis_prompt(all_papers)}

请基于提供的聚类关键词进行深度分析。"""

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        messages = [{"role": "system", "content": system_prompt},
                   {"role": "user", "content": user_prompt}]
        
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=messages,
            response_format={'type': 'json_object'},
            temperature=0.5
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # 记录到日志
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang.get("deep_summary_generated", "深度总结生成完成，使用API: {api}..., 模型: deepseek-r1").format(api=api_key[:8]))
        
        return {
            "keywords": result.get("keywords", ""),
            "summary": result.get("summary", ""),
            "detailed_analysis": result.get("detailed_analysis", {}),
            "success": True
        }
        
    except Exception as e:
        lang = language.get_text(config.LANGUAGE)
        error_msg = lang.get("deep_summary_generation_error", "生成深度总结时发生错误: {error}").format(error=str(e))
        utils.print_and_log(error_msg)
        return {"error": error_msg, "success": False}

def read_all_result_papers():
    """
    读取Result文件夹中所有.bib文件的论文信息
    提取每篇论文的title、abstract、keywords
    """
    result_folder = config.RESULT_FOLDER
    if not os.path.exists(result_folder):
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang.get("result_folder_not_exist", "结果文件夹不存在: {folder}").format(folder=result_folder))
        return []
    
    all_papers = []
    bib_files = [f for f in os.listdir(result_folder) if f.endswith('.bib')]
    
    if not bib_files:
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang.get("no_bib_files_found", "结果文件夹中没有找到.bib文件"))
        return []
    
    lang = language.get_text(config.LANGUAGE)
    utils.print_and_log(lang.get("found_bib_files_parsing", "找到 {count} 个.bib文件，开始解析...").format(count=len(bib_files)))
    
    for bib_file in bib_files:
        file_path = os.path.join(result_folder, bib_file)
        papers = parse_bib_file(file_path)
        all_papers.extend(papers)
        utils.print_and_log(lang.get("parsed_papers_from_file", "从 {file} 解析到 {count} 篇论文").format(file=bib_file, count=len(papers)))
    
    utils.print_and_log(lang.get("total_papers_parsed", "总共解析到 {count} 篇论文").format(count=len(all_papers)))
    return all_papers

def parse_bib_file(file_path):
    """
    解析单个.bib文件，提取title、abstract、keywords
    """
    papers = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # 按@分割条目
        entries = re.split(r'\n@', content)
        
        for i, entry in enumerate(entries):
            if i == 0:
                # 跳过第一部分（通常是搜索主题）
                continue
            
            # 添加@符号（除了第一个）
            if not entry.startswith('@'):
                entry = '@' + entry
            
            paper = parse_single_entry(entry)
            if paper:
                papers.append(paper)
                
    except Exception as e:
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang.get("parse_file_error", "解析文件 {file} 时发生错误: {error}").format(file=file_path, error=str(e)))
        
    return papers

def parse_single_entry(entry):
    """
    解析单个bib条目
    """
    try:
        paper = {}
        
        # 提取title
        title_match = re.search(r'title\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', entry, re.DOTALL)
        if title_match:
            paper['title'] = title_match.group(1).strip()
        else:
            return None  # 没有title的条目跳过
        
        # 提取abstract
        lang = language.get_text(config.LANGUAGE)
        abstract_match = re.search(r'abstract\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', entry, re.DOTALL)
        if abstract_match:
            abstract = abstract_match.group(1).strip()
            # 截取前200个字符作为预览
            paper['abstract'] = abstract[:200] + "..." if len(abstract) > 200 else abstract
        else:
            paper['abstract'] = lang.get("no_abstract", "暂无摘要")
        
        # 提取keywords
        keywords_match = re.search(r'keywords\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', entry, re.DOTALL)
        if keywords_match:
            paper['keywords'] = keywords_match.group(1).strip()
        else:
            paper['keywords'] = lang.get("no_keywords", "暂无关键词")
        
        return paper
        
    except Exception as e:
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang.get("parse_entry_error", "解析单个条目时发生错误: {error}").format(error=str(e)))
        return None

def format_papers_for_analysis_prompt(papers):
    """
    格式化论文列表用于分析提示词
    """
    lang = language.get_text(config.LANGUAGE)
    no_keywords_text = lang.get("no_keywords", "暂无关键词")
    
    formatted = []
    for i, paper in enumerate(papers, 1):
        # 格式化论文标题
        formatted_paper = lang.get("paper_format", "论文{i}. 标题: {title}").format(i=i, title=paper['title'])
        # 添加摘要预览
        formatted_paper += f"\n   {lang.get('abstract_preview', '摘要预览: {abstract}').format(abstract=paper['abstract'])}"
        # 检查是否有关键词（排除"暂无关键词"和"No keywords available"）
        if paper['keywords'] not in ["暂无关键词", "No keywords available", no_keywords_text]:
            formatted_paper += f"\n   {lang.get('keywords_format', '关键词: {keywords}').format(keywords=paper['keywords'])}"
        formatted.append(formatted_paper)
    
    return "\n".join(formatted)

def get_latest_result_file():
    """
    获取最新的结果文件路径
    """
    result_folder = config.RESULT_FOLDER
    if not os.path.exists(result_folder):
        return None
    
    result_files = [f for f in os.listdir(result_folder) if f.startswith('Result_') and f.endswith('.bib')]
    if not result_files:
        return None
    
    # 按时间戳排序，返回最新的
    result_files.sort(reverse=True)
    return os.path.join(result_folder, result_files[0])

def get_latest_log_file():
    """
    获取最新的日志文件路径
    """
    log_folder = config.LOG_FOLDER
    if not os.path.exists(log_folder):
        return None
    
    log_files = [f for f in os.listdir(log_folder) if f.startswith('Log_Result_') and f.endswith('.txt')]
    if not log_files:
        return None
    
    # 按时间戳排序，返回最新的
    log_files.sort(reverse=True)
    return os.path.join(log_folder, log_files[0])

# UI调用的带线程管理的函数
def generate_brief_summary_async(callback, existing_keywords=None):
    """
    异步生成简要总结，带回调机制
    callback: 回调函数，接收结果字典作为参数
    existing_keywords: 可选的现有关键词
    """
    def run_analysis():
        try:
            # 检查是否有结果文件
            result_file_path = get_latest_result_file()
            if not result_file_path:
                lang = language.get_text(config.LANGUAGE)
                callback({"error": lang.get("error_no_result_files", "没有找到结果文件，请先运行论文处理"), "success": False})
                return
            
            # 根据是否有现有关键词选择不同的分析方法
            if existing_keywords and existing_keywords.strip():
                result = generate_brief_summary_with_keywords(existing_keywords.strip())
            else:
                result = generate_brief_summary()
            
            callback(result)
        except Exception as e:
            lang = language.get_text(config.LANGUAGE)
            error_msg = lang.get("brief_summary_generation_error", "生成简要总结时发生错误: {error}").format(error=str(e))
            utils.print_and_log(error_msg)
            callback({"error": error_msg, "success": False})
    
    # 在后台线程中运行
    thread = threading.Thread(target=run_analysis, daemon=True)
    thread.start()

def generate_deep_summary_async(clustering_words, callback):
    """
    异步生成深度总结，带回调机制
    clustering_words: 聚类关键词
    callback: 回调函数，接收结果字典作为参数
    """
    def run_analysis():
        try:
            # 检查是否有结果文件
            result_file_path = get_latest_result_file()
            if not result_file_path:
                lang = language.get_text(config.LANGUAGE)
                callback({"error": lang.get("error_no_result_files", "没有找到结果文件，请先运行论文处理"), "success": False})
                return
            
            # 检查关键词
            if not clustering_words or not clustering_words.strip():
                lang = language.get_text(config.LANGUAGE)
                callback({"error": lang.get("error_no_clustering_words", "请先生成简要总结或输入聚类分析关键词"), "success": False})
                return
            
            result = generate_deep_summary(clustering_words.strip())
            callback(result)
        except Exception as e:
            lang = language.get_text(config.LANGUAGE)
            error_msg = lang.get("deep_summary_generation_error", "生成深度总结时发生错误: {error}").format(error=str(e))
            utils.print_and_log(error_msg)
            callback({"error": error_msg, "success": False})
    
    # 在后台线程中运行
    thread = threading.Thread(target=run_analysis, daemon=True)
    thread.start()

def generate_deep_summary_stream(clustering_words, stream_callback, completion_callback):
    """
    流式生成深度总结
    clustering_words: 聚类关键词
    stream_callback: 流式回调函数，接收流式内容片段
    completion_callback: 完成回调函数，接收最终结果
    """
    analysis_apis = get_available_analysis_apis()
    if len(analysis_apis) < 2:
        lang = language.get_text(config.LANGUAGE)
        completion_callback({"error": lang.get("error_insufficient_api_keys_deep", "错误：需要至少2个API密钥用于深度分析"), "success": False})
        return
    
    api_key = analysis_apis[1]  # 使用第二个分析API
    
    # 读取所有结果文件
    all_papers = read_all_result_papers()
    if not all_papers:
        lang = language.get_text(config.LANGUAGE)
        completion_callback({"error": lang.get("error_no_related_papers", "没有找到相关论文，无法生成总结"), "success": False})
        return
    
    # 根据配置语言设置确定回答语言
    language_instruction = ""
    reasoning_prefix = ""
    if config.LANGUAGE == 'en_US':
        language_instruction = "Please respond in English."
        reasoning_prefix = "[Reasoning] "
        analysis_sections = """
1. Paper classification statistics
2. Research trend analysis
3. Technology development directions
4. Research gaps and opportunities
5. Methodology analysis
6. Future development recommendations"""
    else:  # zh_CN or default
        language_instruction = "请用中文回答。"
        reasoning_prefix = "[推理] "
        analysis_sections = """
1. 论文分类统计
2. 研究趋势分析
3. 技术发展方向
4. 研究空白与机会
5. 方法学分析
6. 未来发展建议"""
    
    # 构建提示词
    if config.LANGUAGE == 'en_US':
        system_prompt = f"""
The user will provide some paper information. Please perform clustering analysis and provide detailed classification results. {language_instruction}

IMPORTANT: You must respond ENTIRELY in English. Do not mix languages.

Please provide in-depth analysis including but not limited to:
{analysis_sections}

Please use natural language for detailed analysis, no need for strict JSON format.

EXAMPLE INPUT: 
Paper 1. Title: Unmet Needs and Opportunities for Mobile Translation AI
   Abstract: Translation apps and devices are often presented in the context of providing assistance while travel...
   Keywords: emerging markets, immigrants, machine translation, migrants, mobile, speech
Paper 2. Title: A View on the Viewer: Gaze-Adaptive Captions for Videos
   Abstract: Subtitles play a crucial role in cross-lingual distribution of multimedia content and help communica...
   Keywords: eye tracking, gaze input, gaze-responsive display, multimedia, subtitles, video captions

Please provide a detailed analysis report.
"""
    else:  # zh_CN or default
        system_prompt = f"""
用户将提供一些论文信息。请进行聚类分析并提供详细的分类结果。{language_instruction}

重要：您必须完全用中文回答。不要混用语言。

请提供深入分析，包括但不限于：
{analysis_sections}

请使用自然语言进行详细分析，无需严格的JSON格式。

示例输入: 
论文1. 标题: Unmet Needs and Opportunities for Mobile Translation AI
   摘要预览: Translation apps and devices are often presented in the context of providing assistance while travel...
   关键词: emerging markets, immigrants, machine translation, migrants, mobile, speech
论文2. 标题: A View on the Viewer: Gaze-Adaptive Captions for Videos
   摘要预览: Subtitles play a crucial role in cross-lingual distribution of multimedia content and help communica...
   关键词: eye tracking, gaze input, gaze-responsive display, multimedia, subtitles, video captions

请提供详细的分析报告。
"""

    # 根据语言设置构建用户提示词
    if config.LANGUAGE == 'en_US':
        user_prompt = f"""Clustering keywords: {clustering_words}

{format_papers_for_analysis_prompt(all_papers)}

Please provide in-depth analysis based on the provided clustering keywords."""
    else:  # zh_CN or default
        user_prompt = f"""聚类关键词：{clustering_words}

{format_papers_for_analysis_prompt(all_papers)}

请基于提供的聚类关键词进行深度分析。"""

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        messages = [{"role": "system", "content": system_prompt},
                   {"role": "user", "content": user_prompt}]
        
        # 流式调用
        stream = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=messages,
            max_tokens=64000,
            temperature=0.5,
            stream=True
        )
        
        reasoning_content = ""
        accumulated_content = ""
        
        for chunk in stream:
            # 处理推理过程内容
            if chunk.choices[0].delta.reasoning_content:
                reasoning_chunk = chunk.choices[0].delta.reasoning_content
                reasoning_content += reasoning_chunk
                # 发送推理过程给回调，添加特殊标识
                stream_callback(f"{reasoning_prefix}{reasoning_chunk}")
            # 处理最终回答内容
            elif chunk.choices[0].delta.content:
                content_chunk = chunk.choices[0].delta.content
                accumulated_content += content_chunk
                # 发送最终内容给回调
                stream_callback(content_chunk)
        
        # 直接返回原始内容，不进行JSON解析
        completion_callback({
            "keywords": clustering_words,
            "summary": accumulated_content,
            "success": True,
            "raw_content": accumulated_content,
            "reasoning_content": reasoning_content  # 添加推理过程
        })
        
        # 记录到日志
        lang = language.get_text(config.LANGUAGE)
        utils.print_and_log(lang.get("deep_summary_stream_generated", "深度总结流式生成完成，使用API: {api}..., 模型: deepseek-r1").format(api=api_key[:8]))
        
    except Exception as e:
        lang = language.get_text(config.LANGUAGE)
        error_msg = lang.get("deep_summary_stream_error", "生成深度总结时发生错误: {error}").format(error=str(e))
        utils.print_and_log(error_msg)
        completion_callback({"error": error_msg, "success": False})

def generate_deep_summary_stream_async(clustering_words, stream_callback, completion_callback):
    """
    异步流式生成深度总结，带回调机制
    clustering_words: 聚类关键词
    stream_callback: 流式回调函数，接收流式内容片段
    completion_callback: 完成回调函数，接收最终结果
    """
    def run_analysis():
        try:
            # 检查是否有结果文件
            result_file_path = get_latest_result_file()
            if not result_file_path:
                lang = language.get_text(config.LANGUAGE)
                completion_callback({"error": lang.get("error_no_result_files", "没有找到结果文件，请先运行论文处理"), "success": False})
                return
            
            # 检查关键词
            if not clustering_words or not clustering_words.strip():
                lang = language.get_text(config.LANGUAGE)
                completion_callback({"error": lang.get("error_no_clustering_words", "请先生成简要总结或输入聚类分析关键词"), "success": False})
                return
            
            generate_deep_summary_stream(clustering_words.strip(), stream_callback, completion_callback)
        except Exception as e:
            lang = language.get_text(config.LANGUAGE)
            error_msg = lang.get("deep_summary_generation_error", "生成深度总结时发生错误: {error}").format(error=str(e))
            utils.print_and_log(error_msg)
            completion_callback({"error": error_msg, "success": False})
    
    # 在后台线程中运行
    thread = threading.Thread(target=run_analysis, daemon=True)
    thread.start()
