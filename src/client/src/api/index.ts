import axios, { AxiosResponse } from 'axios';
import { ElMessage } from 'element-plus';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// 创建 axios 实例
const axiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 响应拦截器
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => {
    const data = response.data;
    // 如果响应格式是 {code, status, message, data}
    if (data.code !== undefined) {
      // 特殊处理：metadata not found 是正常的业务状态，不应该显示错误提示
      if (data.code !== 0 && !(data.code === 3 && data.message === 'metadata not found')) {
        ElMessage.error(data.message || '请求失败');
        return Promise.reject(new Error(data.message || '请求失败'));
      }
      return data;
    }
    // 如果响应格式是直接返回数据
    return data;
  },
  (error: any) => {
    if (error.response) {
      const status = error.response.status;
      const message = error.response.data?.message || error.response.data?.detail || '请求失败';
      if (status === 404) {
        ElMessage.error('接口不存在');
      } else if (status === 500) {
        ElMessage.error('服务器错误: ' + message);
      } else {
        ElMessage.error(message);
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      const errorCode = error.code;
      let userMessage = '无法连接到服务器';
      
      if (errorCode === 'ECONNREFUSED') {
        userMessage = '连接被拒绝。请确保服务器已启动（运行 python run_server.py）';
      } else if (errorCode === 'ETIMEDOUT' || errorCode === 'ECONNABORTED') {
        userMessage = '连接超时。请检查网络或服务器状态';
      } else if (errorCode === 'ENOTFOUND') {
        userMessage = '无法解析服务器地址。请检查 VITE_API_BASE 配置';
      } else {
        userMessage = `无法连接到服务器 (${errorCode || '未知错误'})。请确保服务器运行在 ${API_BASE}`;
      }
      
      ElMessage.error(userMessage);
      console.error('Request error:', {
        code: errorCode,
        message: error.message,
        config: error.config?.url,
      });
    } else {
      ElMessage.error('请求错误: ' + (error.message || '未知错误'));
      console.error('Request setup error:', error);
    }
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
  // 健康检查
  healthCheck: (): Promise<ApiResponse<{ status: string }>> =>
    axiosInstance.get('/health'),

  // 工具管理
  getToolList: (): Promise<ApiResponse<any[]>> =>
    axiosInstance.get('/tool/tool_list'),

  getTool: (toolName: string): Promise<ApiResponse<any>> =>
    axiosInstance.get(`/tool/${toolName}`),

  addTool: (toolName: string, config: any): Promise<ApiResponse<any>> =>
    axiosInstance.post(`/tool/${toolName}/add`, config),

  editTool: (toolName: string, config: any): Promise<ApiResponse<any>> =>
    axiosInstance.post(`/tool/${toolName}/edit`, config),

  getDefaultTools: (): Promise<ApiResponse<any>> =>
    axiosInstance.get('/tool/defaults'),

  getToolTemplates: (): Promise<ApiResponse<any>> =>
    axiosInstance.get('/tool/templates'),

  // 项目管理
  getProjects: (): Promise<ApiResponse<any>> =>
    axiosInstance.get('/project/projects'),

  getCurrentProject: (): Promise<ApiResponse<any>> =>
    axiosInstance.get('/project/projects/current'),

  createProject: (payload: {
    name: string;
    display_name?: string;
    description?: string;
  }): Promise<ApiResponse<any>> =>
    axiosInstance.post('/project/projects', payload),

  switchProject: (payload: { name: string }): Promise<ApiResponse<any>> =>
    axiosInstance.post('/project/projects/switch', payload),

  deleteProject: (name: string): Promise<ApiResponse<any>> =>
    axiosInstance.delete(`/project/projects/${name}`),

  // 文件管理
  uploadFile: (
    project: string,
    date: string,
    file: File,
    metadata: {
      source: string;
      tags: string[];
      notes?: string;
    }
  ): Promise<ApiResponse<FileInfo>> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', metadata.source);
    formData.append('tags', metadata.tags.join(','));
    if (metadata.notes) {
      formData.append('notes', metadata.notes);
    }
    return axiosInstance.post(
      `/project/${project}/data/${date}/upload_files`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  },

  updateFile: (
    project: string,
    date: string,
    file: File,
    metadata: {
      source: string;
      tags: string[];
      notes?: string;
    }
  ): Promise<ApiResponse<FileInfo>> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', metadata.source);
    formData.append('tags', metadata.tags.join(','));
    if (metadata.notes) {
      formData.append('notes', metadata.notes);
    }
    return axiosInstance.post(
      `/project/${project}/data/${date}/update_files`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  },

  getMetadata: (project: string, date: string): Promise<ApiResponse<any>> =>
    axiosInstance.get(`/project/${project}/data/${date}/metadata`),

  getRecordDates: (project: string): Promise<ApiResponse<string[]>> =>
    axiosInstance.get(`/project/${project}/data/dates`),

  previewFile: (
    project: string,
    date: string,
    filename: string
  ): Promise<Blob> =>
    axiosInstance
      .get(
      `/project/${project}/data/${date}/preview`,
      {
        params: { filename },
        responseType: 'blob',
      }
      )
      .then((res) => res.data as Blob),

  // 工作流管理
  getWorkflowTemplate: (project: string): Promise<ApiResponse<any>> =>
    axiosInstance.get(`/project/${project}/workflow_template`),

  getWorkflowList: (project: string): Promise<ApiResponse<WorkflowInfo[]>> =>
    axiosInstance.get(`/project/${project}/workflow_list`),

  createWorkflowFromTemplate: (
    project: string,
    data: {
      date: string;
      name: string;
      overrides?: any;
    }
  ): Promise<ApiResponse<{ wf_id: string }>> =>
    axiosInstance.post(`/project/${project}/create_workflow_from_template`, data),

  uploadWorkflow: (
    project: string,
    data: {
      date: string;
      wf_id: string;
      config: any;
    }
  ): Promise<ApiResponse<{ wf_id: string }>> =>
    axiosInstance.post(`/project/${project}/upload_workflow`, data),

  startWorkflow: (
    project: string,
    data: {
      wf_id: string;
      date: string;
      files?: string[];
      custom_prompt?: string;
    }
  ): Promise<ApiResponse<{ wf_id: string; date: string }>> =>
    axiosInstance.post(`/project/${project}/start_workflow`, data),

  getWorkflowStatus: (
    project: string,
    wfId: string
  ): Promise<ApiResponse<WorkflowInfo>> =>
    axiosInstance.get(`/project/${project}/workflow_status/${wfId}`),

  getWorkflowDetail: (
    project: string,
    wfId: string
  ): Promise<ApiResponse<{ status: any; output: any }>> =>
    axiosInstance.get(`/project/${project}/workflow_detail/${wfId}`),

  // LLM 配置
  getLlmConfig: (): Promise<ApiResponse<{ base_url: string | null; has_api_key: boolean; default_model?: string | null }>> =>
    axiosInstance.get('/llm/config'),

  updateLlmConfig: (payload: { base_url: string; api_key?: string; default_model?: string }): Promise<ApiResponse<any>> =>
    axiosInstance.post('/llm/config', payload),

  getLlmModels: (): Promise<ApiResponse<Array<{ id: string; owned_by?: string; object?: string }>>> =>
    axiosInstance.get('/llm/models'),

  getLlmStatus: (): Promise<ApiResponse<{ langchain_available: boolean; openai_configured: boolean; available_models: number; models: string[]; default_model: string }>> =>
    axiosInstance.get('/llm/status'),

  reinitializeLlmModels: (): Promise<ApiResponse<{ models: string[]; count: number }>> =>
    axiosInstance.post('/llm/reinitialize'),
};
