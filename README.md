# 本地企业数据分析与制度问答 Agent

一个面向企业内部场景的本地 Agent 项目。用户可以用自然语言提问，系统根据问题类型选择数据分析或制度知识库能力，并返回带真实数据依据或文档来源的中文答案。

## 项目能力

- 使用 Ollama 在本机运行 DeepSeek/Qwen 等大模型。
- 使用 Dify Chatflow 编排分类、条件分支、RAG、HTTP 工具和最终回答。
- 使用 Pandas 分析真实 Online Retail 交易数据。
- 使用 SQLite 保存结构化订单数据，支持按国家、日期和 TopN 查询。
- 使用 FastAPI 将本地数据分析能力封装为 HTTP 服务。
- 使用 Chroma 和 Embedding 模型构建公司制度知识库。
- 支持 TXT、DOCX、PDF 文档检索，并在资料不足时拒答。
- 支持多轮会话上下文、工具调用记录、数据覆盖范围提示和 Web App 发布。
- 使用 Docker Compose 在本地部署 Dify。

## 系统架构

```text
用户浏览器
    ↓
Dify Web App / Chatflow
    ↓
问题分类器
    ├─ 公司制度问题 → RAG 知识库 → LLM → 直接回复
    ├─ 销售分析问题 → FastAPI → Pandas / SQLite → LLM → 直接回复
    └─ 不支持问题 → 兜底回复
    ↓
本地 Ollama 模型
```

当前数据分析链路：

```text
自然语言问题
→ 意图识别
→ 参数提取
→ 受控 SQL 查询
→ 统一结果
→ 本地 LLM 生成中文回答
```

## 技术栈

- Python、Pandas、SQLite
- FastAPI、Uvicorn
- LangGraph
- Dify、Docker Compose
- Ollama、DeepSeek R1 Distill Qwen 7B、Qwen
- Chroma、Embedding 模型
- Streamlit、OpenPyXL

## 目录说明

```text
my-data-analysis-agent/
├─ streamlit_app.py                 # Streamlit 数据分析页面
├─ langgraph_first_demo.py          # LangGraph 本地 Agent 入口
├─ agent_service.py                 # Agent 服务层
├─ local_llm.py                     # Ollama 调用封装
├─ retail_tools.py                  # Pandas 数据分析工具
├─ retail_analysis.py               # 零售数据分析逻辑
├─ api.py                            # 原有 Agent FastAPI 服务
├─ sql_api.py                        # SQLite SQL 查询 API
├─ rag_demo/                         # RAG 文档解析、索引、检索和评估
├─ Dockerfile                        # Agent 服务镜像配置
├─ docker-compose.yml                # 本地服务编排配置
├─ requirements.txt                  # Python 依赖
├─ datasets/                         # 本地数据集，不提交真实数据
├─ models/                           # 本地模型，不提交模型文件
└─ retail.db                         # 本地 SQLite 数据库，不提交数据库文件
```

## 环境要求

- Windows 10/11
- Python 3.12
- Docker Desktop
- Ollama
- 已下载并配置所需本地模型

建议确认：

```powershell
python --version
docker --version
ollama list
```

## 每日启动

完整启动顺序：

```powershell
# 1. 启动 FastAPI 数据分析服务
cd E:\my-data-analysis-agent
python -m uvicorn api:app --host 0.0.0.0 --port 8000

# 2. 另开 PowerShell，启动 Dify
cd E:\代码\dify\docker
docker compose up -d
```

然后访问：

```text
Dify：http://localhost:8080
FastAPI 文档：http://127.0.0.1:8000/docs
```

Ollama 默认服务地址为：

```text
http://127.0.0.1:11434
```

更完整的启动、检查和停止说明见：

```text
Dify与数据分析Agent每日启动方式.txt
```

## 创建 SQLite 数据库

将真实 Online Retail Excel 数据清洗后导入 SQLite，生成 `retail.db` 和 `retail_orders` 表。数据库文件被 `.gitignore` 排除，不上传到 GitHub。

示例数据路径：

```text
datasets/02_真实零售交易大数据/Online_Retail.xlsx
```

数据库中的主要字段：

```text
InvoiceNo、StockCode、Description、Quantity、InvoiceDate、UnitPrice、CustomerID、Country、SalesAmount
```

## SQL 查询接口

启动：

```powershell
cd E:\my-data-analysis-agent
python -m uvicorn sql_api:app --host 0.0.0.0 --port 8001
```

接口：

```text
GET /health
GET /sql/country-sales
```

支持的查询参数：

```text
country     国家，可选，例如 Germany
start_date  起始日期，可选，例如 2011-12-01
end_date    结束日期边界，可选，例如 2012-01-01
top_n       返回数量，默认 10，范围 1-100
```

示例：

```powershell
Invoke-RestMethod "http://127.0.0.1:8001/sql/country-sales?start_date=2011-12-01&end_date=2012-01-01&top_n=5"
```

接口使用参数化 SQL，并返回 `data_coverage` 字段。当前数据实际覆盖到 `2011-12-09`，因此查询 2011 年 12 月时必须提示结果不是完整月份数据。

## Dify 工作流

### 制度问答

```text
用户输入 → 问题分类器 → 知识库检索 → LLM → 直接回复
```

知识库示例文档：

- 公司销售管理制度.txt
- 员工报销管理办法.docx
- 产品售后服务规范.pdf

### 数据分析

当前已验证的能力包括：

- 国家销售额排行
- 月度销售趋势与环比
- 客户复购分析
- 指定国家、日期和 TopN 的 SQL 销售查询

SQL 条件查询分支：

```text
问题分类器
→ LLM 5：提取 country、start_date、end_date、top_n
→ HTTP 请求 4：调用 sql_api.py
→ LLM 6：整理 JSON 结果
→ 直接回复 6
```

Dify 容器访问 Windows 宿主机服务时使用：

```text
http://host.docker.internal:8000
http://host.docker.internal:8001
http://host.docker.internal:11434
```

## 测试用例

| 问题 | 预期能力 |
|---|---|
| 哪个国家卖得最好？ | 全周期国家销售分析 |
| 2011 年 12 月销售额最高的 5 个国家是哪些？ | SQL 日期 + TopN 查询，并提示数据覆盖范围 |
| 客户复购率是多少？ | 客户复购分析 |
| 订单折扣超过 10% 需要谁审批？ | RAG 检索公司销售管理制度 |
| 一线城市住宿最多报销多少？ | RAG 检索报销管理办法 |
| 公司年假有多少天？ | 资料不足时明确拒答 |
| 帮我分析天气情况 | 不支持问题走兜底回复 |

排查时按这个顺序查看 Dify 日志：

```text
问题分类器 → 实际分支 → 参数提取 → HTTP 状态码 → 工具返回值 → LLM 输入 → 最终回复
```

## 工程设计原则

1. LLM 负责理解自然语言和组织表达，不直接编造业务数字。
2. Pandas、SQL 或数据库负责真实查询和指标计算。
3. RAG 负责从非结构化文档中检索依据，SQL 负责从结构化数据中取数。
4. 工具使用统一输入输出，便于日志、校验和前端复用。
5. SQL 使用参数化查询，后续扩展应采用指标注册表和白名单校验。
6. 查询范围和数据实际覆盖范围分开处理，避免把部分月份当成完整月份。
7. 模型、数据库、向量索引和密钥属于本地或敏感资源，不提交到 GitHub。

## 后续企业化方向

Demo 阶段可以保留多个独立工具，便于验证 Agent 基础闭环。规模扩大后，建议将数据分析能力收敛为一个统一接口：

```text
POST /analytics/query
```

统一请求包含：

```text
metric：指标，例如销售额、复购率
dimension：维度，例如国家、月份、客户
filters：筛选条件，例如国家和日期
sort / limit：排序和返回数量
```

后端再通过指标注册表映射到受控 SQL 或 Python 分析函数。Dify 只调用统一入口，不需要每新增一个指标就增加一套工作流节点。


## 当前限制

- 当前 SQL 接口是受控查询示例，不是任意 SQL 生成器。
- Online Retail 原始数据只覆盖到 2011-12-09。
- 本项目默认使用本地模型，模型响应速度取决于显卡、内存和 Ollama 配置。
- Dify 的工作流配置和知识库数据需要在本地环境中单独维护。
