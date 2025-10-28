# AutoResearchLogMaker Client 实现计划

## 概述

本文档面向接力开发的大模型，说明如何实现 AutoResearchLogMaker 的客户端（Client）。

**背景**：Server 端已全部实现完毕，包括：
- FastAPI 后端服务（`src/server/`）
- 数据管理（文件/元数据/工具配置）
- 项目管理（项目/设置）
- 工具系统（PDF/图片OCR/Excel/文本处理/MCP外部工具）
- 工作流引擎（支持动态 JSON 图定义、LangGraph 执行）
- LLM 集成（LangChain + 提示模板）

**目标**：实现一个用户友好的客户端，提供图形化界面或 CLI 工具，让用户能够：
1. 创建和管理研究项目
2. 按日期上传/管理文件（PDF/图片/Excel/截图/剪贴板）
3. 配置和启动工作流（自动解析文件并生成研究总结）
4. 查看工作流执行状态和输出结果
5. 配置工具和提示模板

---

## Server API 接口总览

客户端需要调用以下已实现的 RESTful API：

### 1. 健康检查
- `GET /health` - 检查服务是否运行

### 2. 工具管理 (`/tool`)
- `GET /tool/tool_list` - 获取所有工具列表（default + user）
- `GET /tool/{user_tool}` - 获取指定用户工具配置
- `POST /tool/{user_tool}/add` - 添加新用户工具
- `POST /tool/{user_tool}/edit` - 编辑用户工具

### 3. 项目工作流 (`/project/{project}`)
- `GET /project/{project}/workflow_template` - 获取默认工作流模板
- `POST /project/{project}/create_workflow_from_template` - 从模板创建工作流
  - Body: `{ "date": "YYYY-MM-DD", "name": "workflow_name", "overrides": {...} }`
- `POST /project/{project}/upload_workflow` - 上传完整工作流配置
  - Body: `{ "date": "YYYY-MM-DD", "wf_id": "wf_xxx", "config": {...} }`
- `POST /project/{project}/start_workflow` - 启动工作流执行
  - Body: `{ "wf_id": "wf_xxx", "date": "YYYY-MM-DD", "files": [...], "custom_prompt": "..." }`
- `GET /project/{project}/workflow_status/{wf_id}` - 查询工作流状态

### 4. 数据管理 (`/project/{project}/data`)
- `POST /project/{project}/data/{date}/upload_files` - 上传文件
  - Form: `file`, `source`, `tags`, `notes`
- `POST /project/{project}/data/{date}/update_files` - 更新已存在文件
  - Form: `file`, `source`, `tags`, `notes`
- `GET /project/{project}/data/{date}/metadata` - 获取日期的元数据

---

## Client 架构设计

### 技术栈建议

**方案A：桌面应用（已选定）**
- **框架**：Electron + Vue 3 + TypeScript
- **优势**：原生体验、支持截图/剪贴板、跨平台、Vue生态丰富
- **技术栈**：
  - **前端框架**：Vue 3 + Composition API + TypeScript
  - **UI组件库**：Element Plus 或 Ant Design Vue
  - **状态管理**：Pinia
  - **路由**：Vue Router
  - **HTTP客户端**：axios
  - **文件上传**：FormData + 拖拽上传
  - **剪贴板/截图**：`electron-clipboard` / `screenshot-desktop`
  - **构建工具**：Vite + Electron Builder
  - **代码规范**：ESLint + Prettier

**方案B：Web 应用**
- **框架**：React + TypeScript + Ant Design / Vue 3 + Element Plus
- **优势**：快速开发、易于部署
- **限制**：截图/剪贴板功能受浏览器限制

**方案C：CLI 工具**
- **框架**：Python `click` / `typer` 或 Node.js `commander`
- **优势**：脚本化、自动化流程
- **适用场景**：批量处理、CI/CD 集成

---

## 功能模块设计

### 1. 项目管理模块

**功能**：
- 创建新项目（输入项目名、描述、默认 Prompt）
- 列出所有项目
- 切换当前项目
- 项目设置（编辑 `settings.yaml`：default_prompt、required_tools）

**实现要点**：
- 项目创建需调用 Server 的项目初始化逻辑（可能需要新增 API 或直接操作文件系统）
- 使用 `lib/{project_name}/` 存储项目数据
- 设置页面需读取/写入 `settings_template.yaml`

**建议 API 扩展**（如果 Server 未提供）：
- `POST /project/create` - 创建项目
- `GET /project/list` - 列出项目
- `GET /project/{project}/settings` - 获取项目设置
- `PUT /project/{project}/settings` - 更新项目设置

---

### 2. 文件管理模块

**功能**：
- 按日期组织文件（日期选择器）
- 上传文件：
  - 本地文件选择（PDF/图片/Excel/文本）
  - 截图上传（调用系统截图工具或内置）
  - 剪贴板粘贴（图片/文本）
- 文件列表展示（文件名、大小、标签、上传时间）
- 文件预览（PDF/图片缩略图）
- 文件更新/替换（显示版本历史）
- 标签管理（添加/删除标签，按标签筛选）

**实现要点**：
- 使用 `FormData` 上传文件到 `POST /project/{project}/data/{date}/upload_files`
- 截图功能：
  - **Electron**：使用 `electron-screenshot` 或系统快捷键触发
  - **Web**：使用浏览器 Clipboard API（`navigator.clipboard.read()`）
- 剪贴板粘贴：
  - 监听 `paste` 事件，提取图片/文本并上传
- 文件列表：调用 `GET /project/{project}/data/{date}/metadata` 获取 `files[]` 数组

**UI 参考**：
- 左侧：日期选择器 + 项目切换
- 中间：文件列表（表格或卡片视图）
- 右侧：文件详情/预览

---

### 3. 工作流管理模块

**功能**：
- 工作流模板选择/编辑（可视化编辑器）
- 从模板创建工作流（填写名称、覆盖参数）
- 上传自定义工作流 JSON
- 启动工作流（选择日期、文件、自定义 Prompt）
- 查看工作流执行状态（pending/running/success/failed）
- 查看工作流输出结果（总结文本、元数据）
- 工作流历史记录（按项目/日期筛选）

**实现要点**：
- **工作流图编辑器**（可选高级功能）：
  - 使用 `react-flow` 或 `vue-flow` 可视化编辑节点/边
  - 节点类型：`start`, `tool`, `llm`, `branch`, `merge`, `end`
  - 支持拖拽、连线、参数配置
- **快速启动**：
  - 调用 `POST /project/{project}/create_workflow_from_template`
  - 然后调用 `POST /project/{project}/start_workflow`
- **状态轮询**：
  - 定时调用 `GET /project/{project}/workflow_status/{wf_id}` 更新状态
  - 使用 WebSocket（需 Server 支持）或长轮询

**UI 参考**：
- 顶部：工作流操作栏（新建/导入/启动）
- 中间：工作流列表（类似 GitHub Actions）
- 底部：执行日志/输出结果

---

### 4. 工具配置模块

**功能**：
- 查看所有可用工具（default + user）
- 添加用户自定义工具（填写配置表单）
- 编辑用户工具配置
- 启用/禁用工具
- MCP 工具配置（外部 MCP Server URL、认证、工具列表）

**实现要点**：
- 调用 `GET /tool/tool_list` 获取工具列表
- 添加工具：调用 `POST /tool/{user_tool}/add`，需传递：
  ```json
  {
    "name": "my_custom_tool",
    "description": "...",
    "type": "custom|mcp|pdf_parser|...",
    "config": { ... },
    "enabled": true
  }
  ```
- MCP 工具示例配置：
  ```json
  {
    "name": "external_summarizer",
    "type": "mcp",
    "config": {
      "server_url": "https://mcp.example.com",
      "auth": { "bearer": "TOKEN" },
      "remote_tool": "summarize",
      "timeout": 60
    }
  }
  ```

**UI 参考**：
- 工具列表（表格）
- 工具详情/编辑对话框

---

### 5. 输出结果查看模块

**功能**：
- 查看某日期的自动总结
- 查看工作流输出 JSON
- 导出结果（Markdown/PDF）
- 用户备注编辑

**实现要点**：
- 调用 `GET /project/{project}/data/{date}/metadata` 获取 `summary.auto_summary` 路径
- 读取 `lib/server/usrdata/{project}/data/{date}/outputs/output_{timestamp}.json`
- 显示总结文本、处理的文件列表、LLM 元数据

**UI 参考**：
- 左侧：日期选择器
- 中间：总结内容（Markdown 渲染）
- 右侧：元数据（文件列表、工作流信息）

---

## 数据流示例

### 典型使用流程：每日研究日志

1. **用户打开客户端**
   - 选择项目：`my_research_project`
   - 选择日期：`2025-10-28`

2. **上传文件**
   - 用户拖拽 3 个 PDF 文件到界面
   - Client 调用 `POST /project/my_research_project/data/2025-10-28/upload_files`（3次）
   - Server 返回文件路径，自动更新 `record_meta.json`

3. **启动工作流**
   - 用户点击"生成今日总结"按钮
   - Client 调用 `POST /project/my_research_project/create_workflow_from_template`
     - Body: `{ "date": "2025-10-28", "name": "daily_summary" }`
   - Server 返回 `wf_id: "wf_20251028_153045"`
   - Client 调用 `POST /project/my_research_project/start_workflow`
     - Body: `{ "wf_id": "wf_20251028_153045", "date": "2025-10-28" }`
   - Server 在后台执行工作流

4. **查看进度**
   - Client 每 2 秒轮询 `GET /project/my_research_project/workflow_status/wf_20251028_153045`
   - 状态变化：`pending` → `running` → `success`

5. **查看结果**
   - Client 调用 `GET /project/my_research_project/data/2025-10-28/metadata`
   - 解析 `summary.auto_summary` 路径，展示总结内容
   - 用户可添加 `user_notes`

---

## 技术实现细节

### HTTP 客户端封装

```typescript
// src/api/index.ts (Vue 3 + TypeScript)
import axios, { AxiosResponse } from 'axios';
import { ElMessage } from 'element-plus';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// 响应拦截器
axios.interceptors.response.use(
  (response: AxiosResponse) => {
    if (response.data.code !== 0) {
      ElMessage.error(response.data.message || '请求失败');
      throw new Error(response.data.message);
    }
    return response.data;
  },
  (error) => {
    ElMessage.error('网络错误');
    return Promise.reject(error);
  }
);

export interface ApiResponse<T = any> {
  code: number;
  status: string;
  message: string;
  data: T;
}

export interface FileInfo {
  file_id: string;
  filename: string;
  stored_path: string;
  size_bytes: number;
  uploaded_at: string;
  source: string;
  tags: string[];
  notes?: string;
}

export interface WorkflowInfo {
  wf_id: string;
  name: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  started_at?: string;
  finished_at?: string;
}

export const api = {
  // 工具管理
  getToolList: (): Promise<ApiResponse<any[]>> => 
    axios.get(`${API_BASE}/tool/tool_list`),
  
  getTool: (toolName: string): Promise<ApiResponse<any>> => 
    axios.get(`${API_BASE}/tool/${toolName}`),
  
  addTool: (toolName: string, config: any): Promise<ApiResponse<any>> => 
    axios.post(`${API_BASE}/tool/${toolName}/add`, config),
  
  editTool: (toolName: string, config: any): Promise<ApiResponse<any>> => 
    axios.post(`${API_BASE}/tool/${toolName}/edit`, config),
  
  // 文件管理
  uploadFile: (project: string, date: string, file: File, metadata: {
    source: string;
    tags: string[];
    notes?: string;
  }): Promise<ApiResponse<FileInfo>> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', metadata.source);
    formData.append('tags', metadata.tags.join(','));
    formData.append('notes', metadata.notes || '');
    return axios.post(`${API_BASE}/project/${project}/data/${date}/upload_files`, formData);
  },
  
  updateFile: (project: string, date: string, file: File, metadata: {
    source: string;
    tags: string[];
    notes?: string;
  }): Promise<ApiResponse<FileInfo>> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', metadata.source);
    formData.append('tags', metadata.tags.join(','));
    formData.append('notes', metadata.notes || '');
    return axios.post(`${API_BASE}/project/${project}/data/${date}/update_files`, formData);
  },
  
  getMetadata: (project: string, date: string): Promise<ApiResponse<any>> => 
    axios.get(`${API_BASE}/project/${project}/data/${date}/metadata`),
  
  // 工作流管理
  getWorkflowTemplate: (project: string): Promise<ApiResponse<any>> => 
    axios.get(`${API_BASE}/project/${project}/workflow_template`),
  
  createWorkflowFromTemplate: (project: string, data: {
    date: string;
    name: string;
    overrides?: any;
  }): Promise<ApiResponse<{ wf_id: string }>> => 
    axios.post(`${API_BASE}/project/${project}/create_workflow_from_template`, data),
  
  uploadWorkflow: (project: string, data: {
    date: string;
    wf_id: string;
    config: any;
  }): Promise<ApiResponse<{ wf_id: string }>> => 
    axios.post(`${API_BASE}/project/${project}/upload_workflow`, data),
  
  startWorkflow: (project: string, data: {
    wf_id: string;
    date: string;
    files?: string[];
    custom_prompt?: string;
  }): Promise<ApiResponse<{ wf_id: string; date: string }>> => 
    axios.post(`${API_BASE}/project/${project}/start_workflow`, data),
  
  getWorkflowStatus: (project: string, wfId: string): Promise<ApiResponse<WorkflowInfo>> => 
    axios.get(`${API_BASE}/project/${project}/workflow_status/${wfId}`),
  
  // 健康检查
  healthCheck: (): Promise<ApiResponse<{ status: string }>> => 
    axios.get(`${API_BASE}/health`),
};
```

### 截图功能实现（Electron + Vue）

```typescript
// src/main/screenshot.ts (主进程)
import { desktopCapturer, ipcMain } from 'electron';

ipcMain.handle('capture-screenshot', async () => {
  try {
    const sources = await desktopCapturer.getSources({ 
      types: ['screen'],
      thumbnailSize: { width: 1920, height: 1080 }
    });
    
    if (sources.length === 0) {
      throw new Error('No screen sources available');
    }
    
    const mainSource = sources[0];
    const imageBuffer = mainSource.thumbnail.toPNG();
    
    return {
      success: true,
      data: imageBuffer.toString('base64'),
      mimeType: 'image/png'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
});

// src/renderer/composables/useScreenshot.ts (渲染进程)
import { ref } from 'vue';
import { ElMessage } from 'element-plus';

export function useScreenshot() {
  const isCapturing = ref(false);
  
  const captureScreenshot = async (): Promise<File | null> => {
    if (isCapturing.value) return null;
    
    isCapturing.value = true;
    try {
      const result = await window.electronAPI.captureScreenshot();
      
      if (!result.success) {
        ElMessage.error(`截图失败: ${result.error}`);
        return null;
      }
      
      // 将 base64 转换为 File 对象
      const byteCharacters = atob(result.data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      
      const file = new File([byteArray], `screenshot_${Date.now()}.png`, {
        type: result.mimeType
      });
      
      ElMessage.success('截图成功');
      return file;
    } catch (error) {
      ElMessage.error('截图失败');
      console.error('Screenshot error:', error);
      return null;
    } finally {
      isCapturing.value = false;
    }
  };
  
  return {
    isCapturing,
    captureScreenshot
  };
}
```

### 剪贴板监听（Vue 3）

```typescript
// src/composables/useClipboard.ts
import { ref, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';

export function useClipboard() {
  const isListening = ref(false);
  
  const handlePaste = async (event: ClipboardEvent) => {
    const items = event.clipboardData?.items;
    if (!items) return;
    
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      
      if (item.type.startsWith('image/')) {
        event.preventDefault();
        const file = item.getAsFile();
        if (file) {
          // 触发文件上传事件
          const customEvent = new CustomEvent('clipboard-file', { 
            detail: { file, source: 'clipboard' } 
          });
          window.dispatchEvent(customEvent);
          ElMessage.success('检测到剪贴板图片');
        }
        break;
      }
    }
  };
  
  const startListening = () => {
    if (isListening.value) return;
    document.addEventListener('paste', handlePaste);
    isListening.value = true;
  };
  
  const stopListening = () => {
    if (!isListening.value) return;
    document.removeEventListener('paste', handlePaste);
    isListening.value = false;
  };
  
  onMounted(() => {
    startListening();
  });
  
  onUnmounted(() => {
    stopListening();
  });
  
  return {
    isListening,
    startListening,
    stopListening
  };
}
```

### Vue 3 组件示例

```vue
<!-- src/components/FileUpload.vue -->
<template>
  <div class="file-upload">
    <el-upload
      ref="uploadRef"
      v-model:file-list="fileList"
      :auto-upload="false"
      :on-change="handleFileChange"
      :on-remove="handleFileRemove"
      :before-upload="beforeUpload"
      drag
      multiple
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持 PDF、图片、Excel 文件，单个文件不超过 50MB
        </div>
      </template>
    </el-upload>
    
    <div class="upload-actions">
      <el-button @click="takeScreenshot" :loading="isCapturing">
        <el-icon><camera /></el-icon>
        截图上传
      </el-button>
      <el-button @click="uploadFiles" type="primary" :loading="uploading">
        上传文件
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElMessage, ElUpload, type UploadFile } from 'element-plus';
import { UploadFilled, Camera } from '@element-plus/icons-vue';
import { useScreenshot } from '@/composables/useScreenshot';
import { useClipboard } from '@/composables/useClipboard';
import { api } from '@/api';

const props = defineProps<{
  project: string;
  date: string;
}>();

const emit = defineEmits<{
  uploaded: [files: any[]];
}>();

const uploadRef = ref<InstanceType<typeof ElUpload>>();
const fileList = ref<UploadFile[]>([]);
const uploading = ref(false);
const { isCapturing, captureScreenshot } = useScreenshot();
useClipboard();

const handleFileChange = (file: UploadFile) => {
  console.log('File changed:', file);
};

const handleFileRemove = (file: UploadFile) => {
  console.log('File removed:', file);
};

const beforeUpload = (file: File) => {
  const isValidType = ['application/pdf', 'image/', 'application/vnd.openxmlformats-officedocument'].some(
    type => file.type.includes(type)
  );
  
  if (!isValidType) {
    ElMessage.error('不支持的文件类型');
    return false;
  }
  
  const isLt50M = file.size / 1024 / 1024 < 50;
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB');
    return false;
  }
  
  return true;
};

const takeScreenshot = async () => {
  const file = await captureScreenshot();
  if (file) {
    const uploadFile: UploadFile = {
      name: file.name,
      size: file.size,
      raw: file,
      status: 'ready'
    };
    fileList.value.push(uploadFile);
  }
};

const uploadFiles = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件');
    return;
  }
  
  uploading.value = true;
  const uploadedFiles: any[] = [];
  
  try {
    for (const file of fileList.value) {
      if (file.raw) {
        const result = await api.uploadFile(props.project, props.date, file.raw, {
          source: 'manual_upload',
          tags: [],
          notes: ''
        });
        uploadedFiles.push(result.data);
      }
    }
    
    ElMessage.success(`成功上传 ${uploadedFiles.length} 个文件`);
    emit('uploaded', uploadedFiles);
    fileList.value = [];
    uploadRef.value?.clearFiles();
  } catch (error) {
    ElMessage.error('上传失败');
    console.error('Upload error:', error);
  } finally {
    uploading.value = false;
  }
};

// 监听剪贴板文件事件
window.addEventListener('clipboard-file', (event: any) => {
  const { file, source } = event.detail;
  const uploadFile: UploadFile = {
    name: file.name,
    size: file.size,
    raw: file,
    status: 'ready'
  };
  fileList.value.push(uploadFile);
  ElMessage.info('已添加剪贴板文件到上传列表');
});
</script>

<style scoped>
.file-upload {
  padding: 20px;
}

.upload-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}
</style>
```

---

## UI/UX 设计建议

### 主界面布局

```
┌─────────────────────────────────────────────────────────┐
│  [Logo] AutoResearchLogMaker         [项目: 我的研究]   │
├───────────┬─────────────────────────────────────────────┤
│           │                                             │
│  [项目]   │  顶部导航: [文件] [工作流] [工具] [设置]  │
│  项目A    │                                             │
│  项目B    │  ┌─────────────────────────────────────┐   │
│  + 新建   │  │  日期: 2025-10-28  [上传] [截图]   │   │
│           │  ├─────────────────────────────────────┤   │
│  [日期]   │  │  文件列表:                          │   │
│  2025-10-28 │  paper1.pdf  [PDF]  10MB  [预览]  │   │
│  2025-10-27 │  image.png   [图片] 2MB   [预览]  │   │
│  2025-10-26 │  data.xlsx   [Excel] 500KB [预览] │   │
│  ...      │  │                                     │   │
│           │  └─────────────────────────────────────┘   │
│           │                                             │
│  [操作]   │  ┌─────────────────────────────────────┐   │
│  生成总结  │  │  工作流状态: running...             │   │
│  查看结果  │  │  [进度条] 50%                       │   │
│           │  └─────────────────────────────────────┘   │
└───────────┴─────────────────────────────────────────────┘
```

### 工作流编辑器（高级功能）

```
┌─────────────────────────────────────────────────────────┐
│  工作流编辑器: daily_summary                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   [start] ──→ [pdf_parser] ──→ [text_processor]       │
│                    ↓                     ↓              │
│              [image_reader]         [llm_summary]      │
│                    ↓                     ↓              │
│                    └──────→ [merge] ────→ [end]        │
│                                                         │
│  节点配置:                                              │
│  ┌─────────────────────────────────────────────┐       │
│  │ 节点: llm_summary                           │       │
│  │ 类型: llm                                   │       │
│  │ 模型: gpt-3.5-turbo                         │       │
│  │ 模板: default                               │       │
│  │ 输入映射: { "content": "text_processed" }   │       │
│  └─────────────────────────────────────────────┘       │
│                                                         │
│  [保存] [导出JSON] [预览]                              │
└─────────────────────────────────────────────────────────┘
```

---

## 开发路线图

### 阶段 1：MVP（最小可行产品）

**目标**：实现核心功能，验证流程可行性

1. **基础框架搭建**
   - 选择技术栈（推荐 Electron + React）
   - 配置开发环境、HTTP 客户端
   - 设计主界面布局

2. **文件上传功能**
   - 本地文件选择
   - 调用 `upload_files` API
   - 文件列表展示

3. **工作流快速启动**
   - 从模板创建工作流
   - 启动工作流
   - 查询状态（轮询）

4. **结果查看**
   - 展示总结内容
   - 查看元数据


---

### 阶段 2：增强功能

**目标**：提升用户体验，增加高级特性

1. **项目管理**
   - 项目创建/切换
   - 设置编辑

2. **截图/剪贴板**
   - 快捷键截图
   - 剪贴板粘贴上传

3. **工具配置**
   - 工具列表展示
   - 添加/编辑用户工具
   - MCP 工具配置

4. **文件预览**
   - PDF 缩略图
   - 图片预览
   - Excel 表格展示


---

### 阶段 3：高级功能

**目标**：完善产品，支持复杂场景

1. **工作流可视化编辑器**
   - 节点拖拽
   - 连线编辑
   - 参数配置

2. **批量操作**
   - 批量上传文件
   - 批量启动工作流

3. **导出功能**
   - 导出 Markdown
   - 导出 PDF 报告

4. **历史记录**
   - 文件版本管理
   - 工作流历史

5. **搜索与过滤**
   - 按标签搜索文件
   - 按日期范围筛选


---

## 依赖与环境

### 前端依赖（Electron + Vue 3）

```json
{
  "name": "autoresearchlogmaker-client",
  "version": "1.0.0",
  "main": "dist-electron/main.js",
  "scripts": {
    "dev": "vite",
    "build": "vite build && electron-builder",
    "build:renderer": "vite build",
    "build:main": "tsc -p electron/tsconfig.json",
    "electron:dev": "concurrently \"npm run dev\" \"wait-on http://localhost:5173 && electron .\"",
    "electron:build": "npm run build:renderer && npm run build:main && electron-builder",
    "dist": "npm run electron:build"
  },
  "dependencies": {
    "vue": "^3.3.x",
    "vue-router": "^4.2.x",
    "pinia": "^2.1.x",
    "axios": "^1.5.x",
    "element-plus": "^2.4.x",
    "@element-plus/icons-vue": "^2.1.x",
    "dayjs": "^1.11.x",
    "marked": "^9.1.x",
    "highlight.js": "^11.9.x"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.4.x",
    "vite": "^4.5.x",
    "typescript": "^5.2.x",
    "vue-tsc": "^1.8.x",
    "electron": "^27.x",
    "electron-builder": "^24.6.x",
    "concurrently": "^8.2.x",
    "wait-on": "^7.2.x",
    "@types/node": "^20.8.x",
    "eslint": "^8.52.x",
    "@typescript-eslint/eslint-plugin": "^6.9.x",
    "@typescript-eslint/parser": "^6.9.x",
    "prettier": "^3.0.x"
  }
}
```

### 项目结构

```
client/
├── electron/                 # Electron 主进程
│   ├── main.ts              # 主进程入口
│   ├── preload.ts           # 预加载脚本
│   ├── screenshot.ts        # 截图功能
│   └── tsconfig.json        # TypeScript 配置
├── src/                     # Vue 渲染进程
│   ├── api/                 # API 接口
│   │   └── index.ts
│   ├── components/          # Vue 组件
│   │   ├── FileUpload.vue
│   │   ├── WorkflowEditor.vue
│   │   └── ProjectManager.vue
│   ├── composables/         # Vue 3 Composables
│   │   ├── useScreenshot.ts
│   │   ├── useClipboard.ts
│   │   └── useWorkflow.ts
│   ├── stores/              # Pinia 状态管理
│   │   ├── project.ts
│   │   ├── file.ts
│   │   └── workflow.ts
│   ├── views/               # 页面组件
│   │   ├── Home.vue
│   │   ├── Project.vue
│   │   └── Settings.vue
│   ├── App.vue
│   ├── main.ts
│   └── router.ts
├── public/
├── package.json
├── vite.config.ts
├── tsconfig.json
└── electron-builder.json
```

### 启动命令

```bash
# 安装依赖
npm install

# 开发模式（同时启动 Vite 和 Electron）
npm run electron:dev

# 仅启动前端开发服务器
npm run dev

# 构建生产版本
npm run electron:build

# 打包为可执行文件
npm run dist
```

---

## 测试与部署

### 测试策略

1. **单元测试**：HTTP 客户端、工具函数
2. **集成测试**：完整流程（上传→工作流→结果）
3. **手动测试**：UI/UX 交互、边界情况

### 部署方式

- **桌面应用**：打包为可执行文件（`.exe` / `.dmg` / `.AppImage`）
- **Web 应用**：部署到静态服务器（Nginx / Vercel / Netlify）
- **CLI 工具**：发布到 npm / PyPI

---

## 常见问题与解决方案

### Q1: Server API 返回 CORS 错误
**A**: Server 已配置 CORS 中间件（`allow_origins=["*"]`），确保前端请求带正确 Header。

### Q2: 文件上传失败
**A**: 检查文件大小是否超过 `MAX_FILE_SIZE`（默认 50MB），检查 `FormData` 格式是否正确。

### Q3: 工作流一直处于 `running` 状态
**A**: 检查 Server 日志，可能是 LLM API Key 未配置或工具执行失败。

### Q4: 截图功能无法使用
**A**: 
- Electron: 确保有屏幕录制权限（macOS 需在系统设置中授权）
- Web: 浏览器限制，建议使用浏览器扩展或 Electron

---

## 总结

本计划提供了 AutoResearchLogMaker Client 的完整实现指南，涵盖：
- Server API 接口总览
- 功能模块设计（项目/文件/工作流/工具/输出）
- 技术实现细节（HTTP 客户端、截图、剪贴板）
- UI/UX 设计建议
- 开发路线图（3 阶段）

**建议优先级**：
1. 先实现 MVP（文件上传 + 工作流启动 + 结果查看）
2. 再增强用户体验（截图/剪贴板/项目管理）
3. 最后完善高级功能（可视化编辑器/批量操作）

**技术选型（已确定）**：
- **桌面应用**：Electron + Vue 3 + TypeScript + Element Plus
- **状态管理**：Pinia
- **构建工具**：Vite + Electron Builder
- **UI组件**：Element Plus（Vue 3 生态）

祝开发顺利！如有问题，请参考 Server 代码（`src/server/`）或查阅 API 文档。

