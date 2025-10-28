# 实现AutoResearchLogMaker Server

## 技术栈

- FastAPI: Web框架和RESTful API
- LangChain + LangGraph: LLM工作流编排
- PyMuPDF + PaddleOCR: PDF解析和OCR
- SQLite: 项目和workflow状态存储
- JSON/YAML: 用户可读的数据文件

## 项目结构

```
src/server/
├── main.py                    # FastAPI应用入口
├── config.py                  # 配置管理
├── database.py                # SQLite数据库连接和模型
├── models.py                  # Pydantic数据模型
├── DataManager/
│   ├── __init__.py
│   ├── FileManager.py         # 文件上传、更新、版本控制
│   ├── MetadataManager.py     # record_meta.json 管理
│   └── ToolConfigManager.py   # tool配置管理
├── ProjectManager/
│   ├── __init__.py
│   ├── ProjectManager.py      # 项目创建和管理
│   └── SettingsManager.py     # settings.yaml 管理
├── ToolManager/
│   ├── __init__.py
│   ├── ToolRegistry.py        # tool注册和发现
│   ├── PDFParser.py           # PDF解析工具
│   └── ImageReader.py         # 图片OCR工具
├── WorkflowManager/
│   ├── __init__.py
│   ├── WorkflowEngine.py      # LangGraph工作流引擎
│   └── WorkflowStorage.py     # workflow存储和状态管理
├── LLMManager/
│   ├── __init__.py
│   ├── LLMService.py          # LangChain集成
│   └── PromptManager.py       # prompt模板管理
└── routers/
    ├── __init__.py
    ├── tool_router.py         # /tool 端点
    ├── project_router.py      # /project/{project} 端点
    └── data_router.py         # /project/{project}/data 端点
```

## 实现步骤

### 1. 依赖和基础配置

- 更新 `pyproject.toml` 添加所有依赖
- 创建 `src/server/config.py` 管理配置路径
- 创建 `src/server/database.py` 设置SQLite连接
- 创建 `src/server/models.py` 定义Pydantic模型

### 2. 数据管理模块 (DataManager)

- `ToolConfigManager.py`: 读取/写入/更新tool配置JSON
- `MetadataManager.py`: 管理record_meta.json，包含文件历史版本控制
- `FileManager.py`: 文件上传、CRC32计算、路径管理、版本控制

### 3. 项目管理模块 (ProjectManager)

- `ProjectManager.py`: 项目创建、目录结构初始化、项目列表
- `SettingsManager.py`: settings.yaml读写和验证

### 4. 工具管理模块 (ToolManager)

- `ToolRegistry.py`: 扫描和注册default/user tools
- `PDFParser.py`: PyMuPDF解析PDF文本和结构
- `ImageReader.py`: PaddleOCR识别图片文字

### 5. Workflow管理模块 (WorkflowManager)

- `WorkflowStorage.py`: workflow JSON文件存储和SQLite状态跟踪
- `WorkflowEngine.py`: LangGraph构建workflow执行图，异步执行

### 6. LLM管理模块 (LLMManager)

- `PromptManager.py`: 加载和格式化prompt模板
- `LLMService.py`: LangChain集成，调用LLM生成总结

### 7. API路由 (routers)

- `tool_router.py`: 
  - GET /tool_list
  - GET /{user_tool}
  - POST /{user_tool}/add
  - POST /{user_tool}/edit
- `project_router.py`:
  - GET /workflow_list
  - POST /upload_workflow
  - POST /start_workflow
  - GET /workflow_status/{id}
- `data_router.py`:
  - POST /{date}/upload_files
  - POST /{date}/update_files
  - GET /{date}/metadata

### 8. FastAPI主应用 (main.py)

- 创建FastAPI应用实例
- 注册所有路由
- 配置CORS和中间件
- 设置启动/关闭事件处理

### 9. 模板文件填充

- 填充 `lib/server/static/default_tool_config.json`
- 填充 `lib/server/static/settings_template.yaml`
- 填充 `lib/server/static/usertool_config_template.json`

### 10. 数据库Schema

- 创建projects表：项目基本信息
- 创建workflows表：workflow执行记录和状态
- 创建files表（可选）：快速索引文件
- 自动初始化数据库

## 核心功能说明

### 文件版本控制

- 新文件上传使用CRC32生成file_id
- 更新文件时保留旧记录并标记retired_at
- metadata中维护完整的files历史数组

### Workflow执行

- LangGraph构建状态图：文件解析 → 向量检索 → LLM总结
- 异步执行，SQLite记录状态(pending/running/success/failed)
- 完成后生成output JSON并更新metadata

### 双存储策略

- SQLite：快速查询项目列表、workflow状态、文件索引
- JSON/YAML：用户可直接查看的完整数据记录
- 操作时同步更新两者，保证一致性

# 动态工作流 + Excel读取 + MCP Client 接入

## 目标
- 工作流由 `workflow_{timestamp}.json` 动态定义（来自 `default_workflow.json` 模板），可自定义节点和有向边。
- 新增 `ExcelReader` 工具，支持 .xlsx/.xls/.csv，输出每个 sheet 的结构化 JSON（含单元格类型与合并单元格）。
- 后端作为 MCP Client：用户通过 tools 接口新增 MCP 类工具（保存到 usrtools），工作流执行时按配置调用外部 MCP Tools 并注入到 LLM 工作流。

## 关键改动
- 模板与存储：
  - 新增静态模板 `lib/server/static/default_workflow.json`（包含 nodes、edges、inputs/outputs、工具映射示例）。
  - 扩展 `WorkflowStorage`：上传/创建/读取 `workflow_{timestamp}.json`，校验 schema。

- API 路由：
  - `POST /project/{project}/create_workflow_from_template`：从模板生成 `workflow_{ts}.json`（参数：name、nodes/edges 覆盖、llm_model、prompt_template）。
  - 保持 `POST /project/{project}/upload_workflow` 接受完整 JSON 并保存；新增校验返回错误详情。
  - `GET /project/{project}/workflow_template`：返回默认模板，便于前端编辑。

- WorkflowEngine 动态化：
  - 改造为：执行前从 `workflow_{ts}.json` 解析 nodes/edges 构建 LangGraph。
  - 节点类型：`tool`（引用 ToolRegistry 名称）、`llm`（调用 LLMService）、`branch`（条件路由，支持基于结果字段判断）、`merge`、`end`。
  - 统一节点IO约定：节点接收/返回 dict，允许从前序节点取 key 作为输入映射。

- 工具层：
  - 新增 `ToolManager/ExcelReader.py`（openpyxl + pandas + csv），输出：
    - sheets: [{name, rows, cols, cells[{r,c,value,type}], merged_ranges[]}]
    - summary: {sheet_count, row_counts, header_detected}
  - `ToolRegistry` 注册 `excel_reader`，并从 default_tool_config 支持启用。

- MCP Client：
  - 新增 `ToolManager/MCPClient.py`：
    - 读取 usertool 中 type=`mcp` 的配置（server_url、auth、tools 列表、超时）。
    - 暴露统一 `MCPTool`（继承 BaseTool），调用远端 MCP Server 的指定 tool，透传输入/输出。
  - `ToolConfigManager` 校验支持 `mcp` 类型；`ToolRegistry` 动态加载 `MCPTool`。

- 校验与Schema：
  - `default_workflow.json` 与 `workflow_{ts}.json` 的 Pydantic Schema（在 `models.py` 新增 `WorkflowGraphConfig`）。
  - 在上传/创建 API 中做 schema 校验并返回错误行/字段。

## 文件改动要点
- 新增：`src/server/ToolManager/ExcelReader.py`、`src/server/ToolManager/MCPClient.py`
- 修改：`src/server/ToolManager/ToolRegistry.py`（注册 excel_reader、加载 mcp 工具）
- 修改：`src/server/WorkflowManager/WorkflowEngine.py`（改为按 JSON 构建图）
- 修改：`src/server/WorkflowManager/Workflow