# SearchPaper - 学术论文相关性筛选工具

## 功能简介

SearchPaper 是一个基于 AI 的学术论文筛选工具，能够自动判断论文是否与您的研究主题相关。它使用 DeepSeek API 对论文标题和摘要进行智能分析，帮助研究人员快速筛选出相关文献。

### 主要特性
- 🚀 多线程并行处理，充分利用多个 API Key 提高处理速度
- 🤖 使用 DeepSeek AI 模型进行智能相关性判断
- 📊 实时进度监控，显示处理进度、时间预估和费用估算
- 💰 智能价格计算，支持优惠时段和标准时段的自动切换
- 📝 详细的日志记录，包括筛选原因和完整处理日志
- 🔧 灵活的配置系统，所有参数都可以通过配置文件调整

## 快速开始

### 1. 安装依赖

在新电脑上首次使用时，运行一键安装脚本：

```bash
python install_requirements.py
```

这将自动安装所需的 Python 库并创建必要的文件夹。

### 2. 配置 API 密钥

在 `APIKey` 文件夹中创建一个或多个 `.txt` 文件，每行添加一个 DeepSeek API 密钥：

```
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
sk-yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

### 3. 准备论文数据

将要处理的 `.bib` 格式文献文件放入 `Data` 文件夹中。程序会自动读取所有 `.bib` 文件。

### 4. 配置研究主题

编辑 `config.py` 文件，设置您的研究问题和关键词：

```python
# 研究问题
ResearchQuestion = "您的研究主题描述"

# 关键词（英文逗号分隔）
Keywords = "关键词1, 关键词2, 关键词3"
```

### 5. 运行程序

```bash
python Main.py
```

## 文件夹结构

```
SearchPaper/
├── APIKey/          # 存放API密钥文件
├── Data/            # 存放待处理的.bib文件
├── Result/          # 筛选出的相关论文
├── Log/             # 处理日志
├── lib/             # 核心功能模块
├── Main.py          # 主程序入口
├── config.py        # 配置文件
├── install_requirements.py  # 一键安装脚本
└── README.md        # 本文档
```

## 配置说明

### config.py 主要配置项

1. **研究主题设置**
   - `ResearchQuestion`: 研究问题的详细描述
   - `Keywords`: 相关关键词，用英文逗号分隔

2. **API 设置**
   - `model_name`: 使用的模型名称（默认：deepseek-chat）
   - `api_base_url`: API 服务地址

3. **日志设置**
   - `save_full_log`: 是否保存完整的命令行输出（默认：True）

4. **判断标准**
   - `system_prompt`: AI 判断相关性的具体规则（可自定义）

## 输出结果

### 1. 相关论文文件
- 位置：`Result/Result_YYYYMMDD_HHMM.bib`
- 内容：所有判定为相关的论文条目

### 2. 筛选日志
- 位置：`Log/Log_Result_YYYYMMDD_HHMM.txt`
- 内容：每篇相关论文的标题和判定理由

### 3. 完整日志（可选）
- 位置：`Log/Log_ALL_YYYYMMDD_HHMM.txt`
- 内容：程序运行的所有输出信息

## 进度监控

程序运行时会每秒更新一次进度信息，包括：
- 当前处理进度和已处理论文数
- 时间统计：已运行时长、预计剩余时间、预计完成时间
- Token 使用情况：输入/输出 Token 数量统计
- 价格估算：单篇成本、已消耗成本、预计总成本

## 价格说明

程序支持 DeepSeek API 的分时段计费：
- **优惠时段**（00:30-08:30）：价格更低
- **标准时段**（08:30-00:30）：正常价格

程序会自动识别当前时段并计算相应费用。

## 常见问题

### Q: 如何提高处理速度？
A: 增加更多的 API Key。程序会自动根据 Key 数量创建并行线程。

### Q: 如何修改相关性判断标准？
A: 编辑 `config.py` 中的 `system_prompt`，可以自定义判断规则。

### Q: 程序中断后如何继续？
A: 目前不支持断点续传，需要重新运行。建议分批处理大量论文。

### Q: 如何查看详细的错误信息？
A: 确保 `config.py` 中的 `save_full_log = True`，然后查看 Log 文件夹中的完整日志。

## 注意事项

1. 请妥善保管 API 密钥，不要上传到公开仓库
2. 处理大量论文时请注意 API 调用限制和费用
3. 建议在优惠时段（00:30-08:30）处理大批量论文以节省成本
4. 首次运行前请确保所有文件夹都已创建

## 技术支持

如有问题或建议，请查看代码注释或联系开发者。
