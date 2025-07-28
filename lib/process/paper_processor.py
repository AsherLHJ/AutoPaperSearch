import os
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import data
from . import search_paper
from ..log import utils
from ..config import config_loader as config
from ..result_summary_tools import result_summary_tools
import json
from language import language

def process_paper_batch(paper_indices, rq, keywords, requirements, api_key, thread_id, result_file_path, log_file_path, yon_log_file_path, total_papers):
    """
    处理一批论文的函数，由单个线程执行
    """
    relevant_count = 0
    batch_tokens = 0
    
    for idx, paper_index in enumerate(paper_indices):
        if paper_index in data.paper_data:
            # 记录单篇论文处理开始时间
            single_start_time = time.time()
            
            paper = data.paper_data[paper_index]
            title = paper['title']
            abstract = paper['abstract']
            entry = paper['entry']
            
            try:
                # 调用searchpaper中的方法检查相关性，传入对应的API密钥和requirements
                relevance, tokens, reason, prompt_tokens, completion_tokens, cache_hit, cache_miss = search_paper.check_paper_relevance(
                    rq, keywords, requirements, title, abstract, api_key)
                
                # 累加token使用量
                batch_tokens += tokens
                with data.token_lock:
                    data.token_used += tokens
                    data.prompt_tokens_used += prompt_tokens
                    data.completion_tokens_used += completion_tokens
                    data.prompt_cache_hit_tokens_used += cache_hit
                    data.prompt_cache_miss_tokens_used += cache_miss
                
                # 计算单篇论文处理时间
                single_elapsed_time = time.time() - single_start_time
                
                # 更新进度信息
                utils.update_progress(single_elapsed_time)
                
                # 记录到Y/N日志文件（无论结果是Y还是N）
                with data.file_write_lock:
                    with open(yon_log_file_path, 'a', encoding='utf-8') as yon_log_file:
                        yon_log_file.write('{\n')
                        yon_log_file.write(f'    "title": "{title}",\n')
                        yon_log_file.write(f'    "result": "{relevance.strip().upper()}",\n')
                        yon_log_file.write(f'    "reason": "{reason}"\n')
                        yon_log_file.write('}\n\n')
                
                # 如果相关，则添加到结果文件中
                if relevance.strip().upper() == 'Y':
                    relevant_count += 1
                    
                    # 使用线程锁保护文件写入
                    with data.file_write_lock:
                        # 将entry写入结果文件（追加模式）
                        with open(result_file_path, 'a', encoding='utf-8') as result_file:
                            result_file.write(entry + "\n\n")
                        
                        # 同时写入日志文件（JSON格式）
                        with open(log_file_path, 'a', encoding='utf-8') as log_file:
                            log_file.write('{\n')
                            log_file.write(f'    "title": "{title}",\n')
                            log_file.write(f'    "reason": "{reason}"\n')
                            log_file.write('}\n')
                    
            except Exception as e:
                # 静默处理错误，只在完整日志中记录
                with data.file_write_lock:
                    if config.save_full_log and data.full_log_file:
                        data.full_log_file.write(f"[Thread-{thread_id}] 处理论文 {paper_index} 时出错: {str(e)}\n")
                        data.full_log_file.flush()
    
    return relevant_count, batch_tokens

def process_papers(rq, keywords, requirements, n, selected_folders=None, year_range_info=None):
    """
    处理paper_data中的文章，将相关的文章保存到结果文件中
    """
    # 重置进度跟踪变量
    utils.reset_progress_tracking()
    
    # 获取语言文本
    lang = language.get_text(config.LANGUAGE)
    
    # 确保Result文件夹存在
    result_folder = config.RESULT_FOLDER
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)
    
    # 确保Log文件夹存在
    log_folder = config.LOG_FOLDER
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
        utils.print_and_log(f"{lang['log_folder_created'].format(path=log_folder)}")
    
    # 生成带时间戳的结果文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    query_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data.result_file_name = f"Result_{timestamp}"
    result_file_path = os.path.join(result_folder, f"{data.result_file_name}.bib")
    
    # 创建日志文件路径（移到Log文件夹）
    log_file_path = os.path.join(log_folder, f"Log_{data.result_file_name}.txt")
    
    # 创建Y/N判断结果日志文件路径
    yon_log_file_path = os.path.join(log_folder, f"Log_YoN_{timestamp}.txt")
    
    # 准备查询信息
    folder_info = ", ".join(selected_folders) if selected_folders else "All folders"
    year_info = year_range_info if year_range_info else "All years"
    
    # 如果启用完整日志，创建完整日志文件
    if config.save_full_log:
        full_log_file_path = os.path.join(log_folder, f"Log_ALL_{timestamp}.txt")
        data.full_log_file = open(full_log_file_path, 'w', encoding='utf-8')
        # 在完整日志文件开头写入详细的查询信息
        data.full_log_file.write(f"// Query Time: {query_time}\n")
        data.full_log_file.write(f"// Selected Folders: {folder_info}\n")
        data.full_log_file.write(f"// Year Range: {year_info}\n")
        data.full_log_file.write(f"// Research Question: {rq}\n")
        data.full_log_file.write(f"// Keywords: {keywords}\n")
        if requirements:
            data.full_log_file.write(f"// Requirements: {requirements}\n")
        data.full_log_file.write("\n")
        utils.print_and_log(f"{lang['full_log_created'].format(path=full_log_file_path)}")
    
    # 在结果文件开头写入详细的查询信息
    with open(result_file_path, 'w', encoding='utf-8') as result_file:
        result_file.write(f"% Query Time: {query_time}\n")
        result_file.write(f"% Selected Folders: {folder_info}\n")
        result_file.write(f"% Year Range: {year_info}\n")
        result_file.write(f"% Research Question: {rq}\n")
        result_file.write(f"% Keywords: {keywords}\n")
        if requirements:
            result_file.write(f"% Requirements: {requirements}\n")
        result_file.write(f"\n% Search Topic {{{rq}}}\n\n")
    
    # 在日志文件开头写入详细的查询信息
    with open(log_file_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"// Query Time: {query_time}\n")
        log_file.write(f"// Selected Folders: {folder_info}\n")
        log_file.write(f"// Year Range: {year_info}\n")
        log_file.write(f"// Research Question: {rq}\n")
        log_file.write(f"// Keywords: {keywords}\n")
        if requirements:
            log_file.write(f"// Requirements: {requirements}\n")
        log_file.write("\n")
    
    # 在Y/N日志文件开头写入详细的查询信息
    with open(yon_log_file_path, 'w', encoding='utf-8') as yon_log_file:
        yon_log_file.write(f"// Query Time: {query_time}\n")
        yon_log_file.write(f"// Selected Folders: {folder_info}\n")
        yon_log_file.write(f"// Year Range: {year_info}\n")
        yon_log_file.write(f"// Research Question: {rq}\n")
        yon_log_file.write(f"// Keywords: {keywords}\n")
        if requirements:
            yon_log_file.write(f"// Requirements: {requirements}\n")
    
    # 获取研究方向
    research_direction = rq
    
    # 处理前N篇文章（或者所有文章）
    paper_count = len(data.paper_data)
    if n == -1:
        max_papers = paper_count
    else:
        max_papers = min(n, paper_count)
    
    data.total_papers_to_process = max_papers
    
    utils.print_and_log(f"\n{lang['start_processing_papers'].format(count=max_papers)}")
    utils.print_and_log(f"{lang['total_papers'].format(count=paper_count)}")
    
    # 获取用于处理的API密钥（排除最后两个用于分析的）
    processing_apis = result_summary_tools.get_processing_apis()
    utils.print_and_log(f"{lang['max_parallel_config'].format(count=len(processing_apis))}")
    utils.print_and_log(f"预留 {len(config.API_KEYS) - len(processing_apis)} 个API密钥用于结果分析")

    # 将论文索引分配给不同的线程
    paper_indices = list(range(1, max_papers + 1))
    num_threads = min(len(processing_apis), max_papers)  # 关键代码：线程数取处理API密钥数和论文数的较小值
    batch_size = max_papers // num_threads
    remainder = max_papers % num_threads
    
    # 分配论文给各个线程
    batches = []
    start_idx = 0
    for i in range(num_threads):
        # 前remainder个线程多分配一篇论文
        current_batch_size = batch_size + (1 if i < remainder else 0)
        batch = paper_indices[start_idx:start_idx + current_batch_size]
        batches.append(batch)
        start_idx += current_batch_size
    
    # 计算平均每个线程分配的论文数
    avg_papers_per_thread = max_papers / num_threads
    utils.print_and_log(f"{lang['actual_threads_used'].format(threads=num_threads, avg=avg_papers_per_thread)}")
    
    # 启动进度监控线程
    data.progress_stop_event.clear()
    progress_thread = threading.Thread(target=utils.progress_monitor, daemon=True)
    progress_thread.start()
    
    # 使用线程池并行处理
    total_relevant_count = 0
    
    # 设置活跃线程数
    data.active_threads = num_threads  # 记录实际使用的线程数
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:  # 使用动态计算的线程数
        # 提交所有任务
        future_to_thread = {}
        for i, batch in enumerate(batches):
            if batch:  # 确保批次不为空
                future = executor.submit(
                    process_paper_batch,
                    batch,
                    research_direction,
                    keywords,
                    requirements,  # 添加requirements参数
                    processing_apis[i],  # 为每个线程分配不同的处理API密钥（排除分析用的）
                    i + 1,
                    result_file_path,
                    log_file_path,
                    yon_log_file_path,  # 添加Y/N日志文件路径
                    max_papers
                )
                future_to_thread[future] = i + 1
        
        # 等待所有任务完成
        for future in as_completed(future_to_thread):
            thread_id = future_to_thread[future]
            try:
                relevant_count, batch_tokens = future.result()
                total_relevant_count += relevant_count
            except Exception as e:
                with data.file_write_lock:
                    if config.save_full_log and data.full_log_file:
                        data.full_log_file.write(f"\n线程{thread_id}发生错误: {str(e)}\n")
                        data.full_log_file.flush()
    
    # 停止进度监控线程
    data.progress_stop_event.set()
    progress_thread.join(timeout=2)
    
    # 计算总耗时
    total_elapsed_time = time.time() - data.start_time
    
    # 格式化总耗时
    hours = int(total_elapsed_time // 3600)
    minutes = int((total_elapsed_time % 3600) // 60)
    seconds = int(total_elapsed_time % 60)
    
    # 计算平均单篇文章耗时（考虑并发处理）
    # 实际平均速度 = 总文章数 / 总耗时
    actual_papers_per_second = max_papers / total_elapsed_time if total_elapsed_time > 0 else 0
    # 实际单篇耗时 = 1 / 实际平均速度
    average_time_per_paper = 1 / actual_papers_per_second if actual_papers_per_second > 0 else 0
    
    # 计算最终价格
    from ..price import price
    final_price = price.calculate_token_price(
        data.prompt_tokens_used,
        data.completion_tokens_used,
        data.prompt_cache_hit_tokens_used,
        data.prompt_cache_miss_tokens_used
    )
    
    utils.print_and_log(f"\n{lang['processing_complete_summary'].format(count=total_relevant_count)}")
    utils.print_and_log(lang['time_statistics'])
    utils.print_and_log(lang['total_time'].format(hours=hours, minutes=minutes, seconds=seconds))
    utils.print_and_log(lang['avg_time_per_paper'].format(time=average_time_per_paper, threads=num_threads))
    utils.print_and_log(lang['processing_speed'].format(speed=actual_papers_per_second))
    utils.print_and_log(lang['token_statistics'])
    utils.print_and_log(lang['input_tokens'].format(total=data.prompt_tokens_used, hit=data.prompt_cache_hit_tokens_used, miss=data.prompt_cache_miss_tokens_used))
    utils.print_and_log(lang['output_tokens'].format(count=data.completion_tokens_used))
    utils.print_and_log(lang['total_tokens'].format(count=data.token_used))
    utils.print_and_log(lang['price_statistics'])
    utils.print_and_log(lang['total_cost'].format(price=price.format_price(final_price)))
    utils.print_and_log(lang['result_files'])
    utils.print_and_log(lang['relevant_papers_saved'].format(path=result_file_path))
    utils.print_and_log(lang['log_saved'].format(path=log_file_path))
    utils.print_and_log(lang['all_results_saved'].format(path=yon_log_file_path))
    
    # 关闭完整日志文件
    if data.full_log_file:
        data.full_log_file.close()
