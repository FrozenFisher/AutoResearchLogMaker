<template>
  <div class="workflow-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>工作流管理</span>
          <el-space>
            <el-date-picker
              v-model="selectedDate"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
            />
            <el-button type="success" @click="openCreateDialog">
              <el-icon><Plus /></el-icon>
              新建工作流
            </el-button>
            <el-button type="primary" @click="startWorkflow">
              <el-icon><VideoPlay /></el-icon>
              启动工作流
            </el-button>
          </el-space>
        </div>
      </template>

      <div v-if="workflows.length === 0" class="empty-container">
        <el-empty description="暂无工作流记录" />
      </div>

      <el-table v-else :data="workflows" style="width: 100%">
        <el-table-column prop="wf_id" label="工作流ID" width="200" />
        <el-table-column prop="name" label="名称" width="200" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="{ row }">
            {{ row.started_at ? formatTime(row.started_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="finished_at" label="结束时间" width="180">
          <template #default="{ row }">
            {{ row.finished_at ? formatTime(row.finished_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetails(row)">
              查看详情
            </el-button>
            <el-button
              v-if="row.status === 'running'"
              link
              type="warning"
              size="small"
              @click="refreshStatus(row)"
            >
              刷新状态
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建工作流对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建工作流" width="700px">
      <el-tabs v-model="createTab" type="border-card">
        <el-tab-pane label="从模板创建" name="template">
          <el-form :model="createForm" label-width="120px" style="margin-top: 20px">
            <el-form-item label="工作流名称" required>
              <el-input v-model="createForm.name" placeholder="输入工作流名称" />
            </el-form-item>
            <el-form-item label="提示词模板">
              <el-input v-model="createForm.promptTemplate" placeholder="默认使用 default" />
            </el-form-item>
            <el-form-item label="LLM模型">
              <el-input v-model="createForm.llmModel" placeholder="默认使用配置的默认模型" />
            </el-form-item>
            <el-form-item label="说明">
              <el-alert
                type="info"
                :closable="false"
                show-icon
              >
                <template #title>
                  <div style="font-size: 12px;">
                    将从默认模板创建工作流，创建后可以编辑配置或直接启动。
                  </div>
                </template>
              </el-alert>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="上传自定义配置" name="upload">
          <el-form :model="uploadForm" label-width="120px" style="margin-top: 20px">
            <el-form-item label="工作流ID" required>
              <el-input v-model="uploadForm.wfId" placeholder="如: wf_20251217_120000" />
              <div style="font-size: 12px; color: #909399; margin-top: 4px;">
                工作流的唯一标识符
              </div>
            </el-form-item>
            <el-form-item label="工作流配置" required>
              <el-input
                v-model="uploadForm.configJson"
                type="textarea"
                :rows="12"
                placeholder='请输入工作流配置 JSON，例如：&#10;{&#10;  "name": "my_workflow",&#10;  "nodes": [...],&#10;  "edges": [...]&#10;}'
              />
              <div style="font-size: 12px; color: #909399; margin-top: 4px;">
                请确保 JSON 格式正确
              </div>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmCreateWorkflow"
          :loading="creating"
        >
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 启动工作流对话框 -->
    <el-dialog v-model="showStartDialog" title="启动工作流" width="500px">
      <el-form :model="workflowForm" label-width="100px">
        <el-form-item label="工作流名称">
          <el-input v-model="workflowForm.name" placeholder="输入工作流名称" />
        </el-form-item>
        <el-form-item label="自定义提示词">
          <el-input
            v-model="workflowForm.customPrompt"
            type="textarea"
            :rows="3"
            placeholder="可选，覆盖默认提示词"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showStartDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmStartWorkflow" :loading="starting">
          启动
        </el-button>
      </template>
    </el-dialog>

    <!-- 工作流详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="工作流详情"
      width="700px"
    >
      <div v-if="detailLoading" style="padding: 20px;">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="!detailData" style="padding: 20px;">
        <el-empty description="暂无详情数据" />
      </div>
      <div v-else style="max-height: 500px; overflow: auto;">
        <el-descriptions title="基础信息" :column="2" size="small" border>
          <el-descriptions-item label="工作流ID">
            {{ detailData.status?.wf_id || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="名称">
            {{ detailData.status?.name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(detailData.status?.status || '')">
              {{ getStatusText(detailData.status?.status || '') }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="模型">
            {{ detailData.status?.llm_model || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ detailData.status?.started_at || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="结束时间">
            {{ detailData.status?.finished_at || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <div style="margin-top: 16px;">
          <h4>错误信息</h4>
          <div style="font-size: 13px; color: #f56c6c;" v-if="detailData.status?.error_message">
            {{ detailData.status.error_message }}
          </div>
          <div v-else style="font-size: 13px; color: #909399;">
            无错误信息
          </div>
        </div>

        <div style="margin-top: 16px;">
          <h4>摘要 / 输出</h4>
          <div v-if="detailData.output?.summary" style="margin-bottom: 12px;">
            <el-alert type="success" :closable="false" show-icon>
              <template #title>
                <div style="white-space: pre-wrap; font-size: 13px;">
                  {{ detailData.output.summary }}
                </div>
              </template>
            </el-alert>
          </div>
          <div v-if="detailData.output?.context" style="margin-bottom: 12px;">
            <h5 style="font-size: 13px; color: #909399; margin: 8px 0;">中间步骤输出</h5>
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item
                v-for="(val, key) in detailData.output.context"
                :key="key"
                :label="key"
              >
                <pre
                  style="white-space: pre-wrap; font-size: 12px; margin: 0; max-height: 160px; overflow: auto;"
                >{{ typeof val === 'string' ? val : JSON.stringify(val, null, 2) }}</pre>
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <div>
            <h5 style="font-size: 13px; color: #909399; margin-bottom: 4px;">原始输出 JSON</h5>
            <pre
              style="background: #f5f7fa; padding: 12px; border-radius: 4px; font-size: 12px; max-height: 260px; overflow: auto;"
            >{{ JSON.stringify(detailData.output || {}, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, inject } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { VideoPlay, Plus } from '@element-plus/icons-vue';
import { useProjectStore } from '../stores/project';
import { api, type WorkflowInfo } from '../api';
import dayjs from 'dayjs';

const route = useRoute();
const projectStore = useProjectStore();
const selectedDate = ref(dayjs().format('YYYY-MM-DD'));
const workflows = ref<WorkflowInfo[]>([]);
const showCreateDialog = ref(false);
const showStartDialog = ref(false);
const creating = ref(false);
const starting = ref(false);
const createTab = ref<'template' | 'upload'>('template');
const createForm = ref({
  name: 'daily_summary',
  promptTemplate: '',
  llmModel: '',
});
const uploadForm = ref({
  wfId: '',
  configJson: '',
});
const workflowForm = ref({
  name: 'daily_summary',
  customPrompt: '',
});

const detailDialogVisible = ref(false);
const detailLoading = ref(false);
const detailData = ref<{ status: any; output: any } | null>(null);

const currentProject = computed(() => projectStore.currentProject);

// 注入时间线刷新方法
const refreshTimeline = inject<() => Promise<void>>('refreshTimeline');

const loadWorkflows = async () => {
  try {
    const result = await api.getWorkflowList(currentProject.value);
    if (result.code === 0) {
      workflows.value = result.data || [];
    } else {
      workflows.value = [];
    }
  } catch (error) {
    console.error('Load workflows error:', error);
    workflows.value = [];
  }
};

const openCreateDialog = () => {
  if (!selectedDate.value) {
    ElMessage.warning('请先选择日期');
    return;
  }
  // 重置表单
  createForm.value = {
    name: 'daily_summary',
    promptTemplate: '',
    llmModel: '',
  };
  uploadForm.value = {
    wfId: '',
    configJson: '',
  };
  createTab.value = 'template';
  showCreateDialog.value = true;
};

const confirmCreateWorkflow = async () => {
  if (!selectedDate.value) {
    ElMessage.warning('请先选择日期');
    return;
  }

  creating.value = true;
  try {
    if (createTab.value === 'template') {
      // 从模板创建
      if (!createForm.value.name) {
        ElMessage.warning('请输入工作流名称');
        return;
      }

      const overrides: any = {};
      if (createForm.value.promptTemplate) {
        overrides.prompt_template = createForm.value.promptTemplate;
      }
      if (createForm.value.llmModel) {
        overrides.llm_model = createForm.value.llmModel;
      }

      const result = await api.createWorkflowFromTemplate(currentProject.value, {
        date: selectedDate.value,
        name: createForm.value.name,
        overrides: Object.keys(overrides).length > 0 ? overrides : undefined,
      });

      if (result.code !== 0) {
        throw new Error(result.message || '创建工作流失败');
      }

      ElMessage.success('工作流创建成功');
      showCreateDialog.value = false;

      // 刷新列表和时间线
      await loadWorkflows();
      if (refreshTimeline) {
        await refreshTimeline();
      }
    } else {
      // 上传自定义配置
      if (!uploadForm.value.wfId) {
        ElMessage.warning('请输入工作流ID');
        return;
      }
      if (!uploadForm.value.configJson) {
        ElMessage.warning('请输入工作流配置');
        return;
      }

      let config: any;
      try {
        config = JSON.parse(uploadForm.value.configJson);
      } catch (e) {
        ElMessage.error('JSON 格式错误，请检查配置');
        return;
      }

      const result = await api.uploadWorkflow(currentProject.value, {
        date: selectedDate.value,
        wf_id: uploadForm.value.wfId,
        config: config,
      });

      if (result.code !== 0) {
        throw new Error(result.message || '上传工作流失败');
      }

      ElMessage.success('工作流创建成功');
      showCreateDialog.value = false;

      // 刷新列表和时间线
      await loadWorkflows();
      if (refreshTimeline) {
        await refreshTimeline();
      }
    }
  } catch (error: any) {
    ElMessage.error(error.message || '创建工作流失败');
    console.error('Create workflow error:', error);
  } finally {
    creating.value = false;
  }
};

const startWorkflow = () => {
  if (!selectedDate.value) {
    ElMessage.warning('请先选择日期');
    return;
  }
  showStartDialog.value = true;
};

const confirmStartWorkflow = async () => {
  if (!selectedDate.value) {
    ElMessage.warning('请先选择日期');
    return;
  }

  starting.value = true;
  try {
    // 1. 从模板创建工作流
    const createResult = await api.createWorkflowFromTemplate(currentProject.value, {
      date: selectedDate.value,
      name: workflowForm.value.name,
    });

    if (createResult.code !== 0) {
      throw new Error(createResult.message || '创建工作流失败');
    }

    const wfId = createResult.data.wf_id;

    // 2. 启动工作流
    const startResult = await api.startWorkflow(currentProject.value, {
      wf_id: wfId,
      date: selectedDate.value,
      custom_prompt: workflowForm.value.customPrompt || undefined,
    });

    if (startResult.code !== 0) {
      throw new Error(startResult.message || '启动工作流失败');
    }

    ElMessage.success('工作流启动成功');
    showStartDialog.value = false;
    workflowForm.value.name = 'daily_summary';
    workflowForm.value.customPrompt = '';

    // 刷新工作流列表和时间线
    await loadWorkflows();
    if (refreshTimeline) {
      await refreshTimeline();
    }

    // 3. 开始轮询状态
    pollWorkflowStatus(wfId);
  } catch (error: any) {
    ElMessage.error(error.message || '启动工作流失败');
    console.error('Start workflow error:', error);
  } finally {
    starting.value = false;
  }
};

const pollWorkflowStatus = async (wfId: string) => {
  const maxAttempts = 60; // 最多轮询 60 次
  let attempts = 0;

  const poll = async () => {
    if (attempts >= maxAttempts) {
      ElMessage.warning('工作流状态查询超时');
      return;
    }

    attempts++;

    try {
      const result = await api.getWorkflowStatus(currentProject.value, wfId);
      if (result.code === 0) {
        const workflow = result.data;
        updateWorkflowInList(workflow);

        if (workflow.status === 'running') {
          // 继续轮询
          setTimeout(poll, 2000); // 每 2 秒轮询一次
        } else if (workflow.status === 'success') {
          ElMessage.success('工作流执行完成');
        } else if (workflow.status === 'failed') {
          ElMessage.error('工作流执行失败');
        }
      }
    } catch (error) {
      console.error('Poll workflow status error:', error);
    }
  };

  poll();
};

const updateWorkflowInList = (workflow: any) => {
  const index = workflows.value.findIndex((w) => w.wf_id === workflow.wf_id);
  if (index >= 0) {
    workflows.value[index] = workflow;
  } else {
    workflows.value.unshift(workflow);
  }
};

const refreshStatus = async (workflow: any) => {
  try {
    const result = await api.getWorkflowStatus(currentProject.value, workflow.wf_id);
    if (result.code === 0) {
      updateWorkflowInList(result.data);
      if (result.data.status === 'running') {
        pollWorkflowStatus(workflow.wf_id);
      }
    }
  } catch (error) {
    ElMessage.error('刷新状态失败');
    console.error('Refresh status error:', error);
  }
};

const viewDetails = async (workflow: any) => {
  if (!workflow || !workflow.wf_id) return;
  detailDialogVisible.value = true;
  detailLoading.value = true;
  detailData.value = null;
  try {
    const result = await api.getWorkflowDetail(currentProject.value, workflow.wf_id);
    if (result.code === 0) {
      detailData.value = result.data || null;
    }
  } catch (error) {
    ElMessage.error('加载工作流详情失败');
    console.error('Load workflow detail error:', error);
  } finally {
    detailLoading.value = false;
  }
};

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
  };
  return map[status] || 'info';
};

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败',
  };
  return map[status] || status;
};

const formatTime = (time: string): string => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss');
};

onMounted(async () => {
  await loadWorkflows();
  const qWf = route.query.wf_id;
  if (typeof qWf === 'string') {
    try {
      const result = await api.getWorkflowStatus(currentProject.value, qWf);
      if (result.code === 0) {
        updateWorkflowInList(result.data);
      }
    } catch (error) {
      console.error('Load workflow from query error:', error);
    }
  }
});

watch(
  () => route.query.wf_id,
  async (val) => {
    if (typeof val === 'string') {
      try {
        const result = await api.getWorkflowStatus(currentProject.value, val);
        if (result.code === 0) {
          updateWorkflowInList(result.data);
        }
      } catch (error) {
        console.error('Watch wf_id error:', error);
      }
    }
  }
);

watch(
  () => currentProject.value,
  async () => {
    // 切换/新建项目后，重新加载该项目的工作流列表
    await loadWorkflows();
  }
);
</script>

<style scoped>
.workflow-page {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-container {
  padding: 40px 0;
}
</style>
