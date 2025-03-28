# AI Seed Collector

## 项目简介
AI Seed Collector 是一个智能化的网站内容采集工具，它利用AI技术自动分析和提取网站中对投资者有价值的信息。该工具能够自动识别网站结构，解析栏目内容，并智能判断页面信息的投资价值。

## 核心功能

### 1. 站点解析（siteParser）
- 自动爬取网站结构
- 智能识别和收集栏目URL
- 支持多层级页面遍历

### 2. 栏目解析（columnParser）
- 使用LLM（大语言模型）分析页面内容
- 智能判断页面是否包含投资价值信息
- 自动提取页面中的关键标题和链接

### 3. 选择器生成（selectorParser）
- 自动生成精确的CSS选择器
- 支持XPath路径查找
- 智能处理动态页面内容

## 技术架构

### 主要组件
- **siteParser**: 负责网站结构解析和URL收集
- **columnParser**: 处理页面内容分析和LLM交互
- **selectorParser**: 生成页面元素选择器

### 核心依赖
- BeautifulSoup4：HTML解析
- Requests：网络请求处理
- lxml：XML/HTML处理
- Playwright：动态页面渲染

## 使用方法

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行采集：
```bash
python main.py [网站URL]
```

## 特色优势

1. **智能分析**：利用AI技术智能识别投资相关信息
2. **自动化处理**：全自动的页面解析和内容提取
3. **精确定位**：准确生成页面元素选择器
4. **可扩展性**：模块化设计，易于扩展新功能

## 应用场景

- 投资信息监控
- 公司公告采集
- 行业新闻跟踪
- 舆情监测分析
- 招投标信息收集