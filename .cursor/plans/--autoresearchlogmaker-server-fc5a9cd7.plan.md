<!-- fc5a9cd7-8339-4498-864a-f236a162fca7 462ff9b7-6d14-4a19-8b27-d69946e10b1d -->
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

### To-dos

- [x] 更新依赖配置和基础模块(pyproject.toml, config.py, database.py, models.py)
- [x] 实现DataManager模块(FileManager, MetadataManager, ToolConfigManager)
- [x] 实现ProjectManager模块(ProjectManager, SettingsManager)
- [x] 实现ToolManager模块(ToolRegistry, PDFParser, ImageReader)
- [x] 实现WorkflowManager模块(WorkflowStorage, WorkflowEngine)
- [x] 实现LLMManager模块(PromptManager, LLMService)
- [x] 实现所有API路由(tool_router, project_router, data_router)
- [x] 实现FastAPI主应用并整合所有模块
- [x] 填充静态模板文件(default_tool_config.json, settings_template.yaml, usertool_config_template.json)