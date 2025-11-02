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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { VideoPlay } from '@element-plus/icons-vue';
import { useProjectStore } from '../stores/project';
import { api } from '../api';
import dayjs from 'dayjs';

const projectStore = useProjectStore();
const selectedDate = ref(dayjs().format('YYYY-MM-DD'));
const workflows = ref<any[]>([]);
const showStartDialog = ref(false);
const starting = ref(false);
const workflowForm = ref({
  name: 'daily_summary',
  customPrompt: '',
});

const currentProject = computed(() => projectStore.currentProject);

const loadWorkflows = async () => {
  // TODO: 从服务器获取工作流列表
  // 目前工作流列表可能需要从元数据中获取或新增 API
  workflows.value = [];
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

const viewDetails = (workflow: any) => {
  ElMessage.info('查看详情功能开发中...');
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

onMounted(() => {
  loadWorkflows();
});
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
