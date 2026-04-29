# GitHub Trending Pusher / GitHub热点推送

桌面端自动化工具，从GitHub获取star增长较快且具有学习价值的开源项目，通过智能规则匹配与LLM综合评估，精选TOP N项目并生成结构化总结报告。

## 功能特性

| 功能 | 说明 |
|------|------|
| GitHub热门项目抓取 | 从GitHub Trending页面和Search API获取star增长较快的热门开源项目 |
| 智能规则匹配 | 支持按关键词、主题标签、编程语言自定义推送规则 |
| 综合评估筛选 | 结合规则匹配度、Star阈值、增长速度、LLM学习价值四维度评分，选取TOP N项目 |
| LLM总结生成 | 通过大语言模型生成结构化总结报告（含仓库链接、介绍、学习价值、应用举例） |
| GUI管理界面 | 美观的图形界面，含仪表盘、规则管理、历史记录、系统设置四个页面 |
| 定时任务调度 | 支持每日定时自动执行推送任务 |
| 开机自启动 | 支持Windows开机自动启动 |

## 技术栈

- **语言**：Python 3.10+
- **GUI框架**：CustomTkinter 5.2+
- **GitHub API**：PyGitHub 2.1+
- **HTTP请求**：httpx 0.25+
- **HTML解析**：BeautifulSoup4 4.12+
- **LLM集成**：OpenAI兼容协议（火山方舟 GLM-4.7）
- **定时任务**：APScheduler 3.10+
- **数据存储**：SQLite
- **日志**：loguru 0.7+

## 项目结构

```
├── Code/                          # 源代码
│   ├── config/                    # 配置管理
│   │   ├── default_config.json    # 默认配置模板
│   │   └── settings.py            # 配置管理器（单例模式）
│   ├── core/                      # 核心业务
│   │   ├── github_fetcher.py      # GitHub数据抓取器
│   │   ├── llm_summarizer.py      # LLM总结生成器
│   │   ├── repo_evaluator.py      # 仓库综合评估器
│   │   ├── rule_matcher.py        # 规则匹配器
│   │   └── scheduler.py           # 任务调度器
│   ├── database/                  # 数据库层
│   │   ├── connection.py          # SQLite连接管理
│   │   ├── crud.py                # CRUD操作
│   │   └── migrations.py          # 数据库迁移
│   ├── gui/                       # GUI界面
│   │   ├── app.py                 # 主应用窗口
│   │   ├── components/            # 通用组件
│   │   └── pages/                 # 页面（仪表盘/规则/历史/设置）
│   ├── models/                    # 数据模型
│   ├── service/                   # 服务层
│   ├── utils/                     # 工具函数
│   ├── main.py                    # 程序入口
│   ├── requirements.txt           # 依赖清单
│   └── pyproject.toml             # 项目配置
├── Docs/                          # 开发文档
│   ├── 项目设计文档.md
│   ├── 项目开发文档.md
│   ├── 1.基础设施搭建.md
│   ├── 2.核心业务开发.md
│   ├── 3.服务层开发.md
│   ├── 4.GUI界面开发.md
│   └── 5.集成联调与优化.md
└── README.md
```

## 快速开始

### 环境要求

- Python 3.10 及以上
- Windows 10/11

### 安装依赖

```bash
cd Code
pip install -r requirements.txt
```

### 配置

1. 复制默认配置模板（首次启动会自动生成 `app_config.json`）
2. 在GUI设置页面中配置：
   - **GitHub Token**：GitHub Personal Access Token（仅需 `public_repo` 权限）
   - **代理厂家**：选择LLM API代理厂家（支持OpenAI、火山方舟、DeepSeek、智谱AI、月之暗面、硅基流动、阿里云百炼或自定义）
   - **API Key**：对应代理厂家的API Key
   - **模型**：点击"获取模型"自动获取可用模型列表，或手动输入自定义模型名称

或通过环境变量配置：

```bash
set GITHUB_TOKEN=your_github_token
set VOLCENGINE_API_KEY=your_api_key
```

### 运行

```bash
cd Code
python main.py
```

### 打包

```bash
cd Code
python build.py
```

## 安全说明

- API Key **禁止硬编码**在源代码中，通过配置文件或环境变量传入
- `app_config.json`（用户配置）已加入 `.gitignore`，不会推送到仓库
- GitHub Token 仅申请最小权限（`public_repo`），不执行任何写操作
- 所有HTTP请求使用HTTPS

## 许可证

[MIT License](LICENSE)
