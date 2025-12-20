<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <h1 class="app-title">AutoResearchLogMaker</h1>
        <el-space>
          <el-select
            v-model="projectSelect"
            placeholder="选择项目"
            size="small"
            style="min-width: 180px"
            @change="onProjectChange"
            :loading="projectLoading"
          >
            <el-option
              v-for="item in projectOptions"
              :key="item.name"
              :label="item.display_name || item.name"
              :value="item.name"
            />
          </el-select>
          <el-button
            size="small"
            @click="openCreateProjectDialog"
          >
            新建项目
          </el-button>
          <el-button
            size="small"
            type="danger"
            :disabled="!projectSelect || projectOptions.length === 0"
            @click="openDeleteProjectDialog"
          >
            删除项目
          </el-button>
          <el-button 
            @click="checkHealth" 
            :loading="healthChecking" 
            :type="isConnected ? 'success' : 'danger'"
            size="small"
          >
            {{ isConnected ? '✓ 已连接' : '✗ 未连接' }}
          </el-button>
        </el-space>
      </div>
    </el-header>
    <el-container class="app-body">
      <el-aside width="200px" class="app-sidebar">
        <el-menu
          :default-active="activeMenu"
          router
          class="sidebar-menu"
        >
          <el-menu-item index="/files">
            <el-icon><FolderOpened /></el-icon>
            <span>文件管理</span>
          </el-menu-item>
          <el-menu-item index="/workflow">
            <el-icon><Connection /></el-icon>
            <span>工作流</span>
          </el-menu-item>
          <el-menu-item index="/tools">
            <el-icon><Setting /></el-icon>
            <span>工具配置</span>
          </el-menu-item>
          <el-menu-item index="/results">
            <el-icon><Document /></el-icon>
            <span>结果查看</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-container class="app-main-container">
        <el-main class="app-main">
          <router-view />
        </el-main>
        <el-aside width="260px" class="timeline-aside">
          <TimelinePanel />
        </el-aside>
      </el-container>
    </el-container>

    <!-- 新建项目对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建项目"
      width="480px"
    >
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="项目标识" required>
          <el-input
            v-model="createForm.name"
            placeholder="仅限字母、数字、下划线和中划线"
          />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input
            v-model="createForm.displayName"
            placeholder="列表中展示的名称（可选）"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="简单说明项目用途（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="creatingProject"
          @click="handleCreateProject"
        >
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 删除项目确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="删除项目"
      width="420px"
    >
      <div style="margin-bottom: 16px;">
        <el-alert
          type="warning"
          :closable="false"
          show-icon
        >
          <template #title>
            <div>
              <p style="margin: 0 0 8px 0;">确定要删除项目 <strong>{{ deleteProjectName }}</strong> 吗？</p>
              <p style="margin: 0; font-size: 12px; color: #909399;">此操作将永久删除项目及其所有数据，包括文件、工作流和输出结果，且无法恢复。</p>
            </div>
          </template>
        </el-alert>
      </div>
      <el-form>
        <el-form-item label="确认输入项目名">
          <el-input
            v-model="deleteConfirmName"
            placeholder="请输入项目标识以确认删除"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button
          type="danger"
          :loading="deletingProject"
          :disabled="deleteConfirmName !== deleteProjectName"
          @click="handleDeleteProject"
        >
          确认删除
        </el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useProjectStore } from './stores/project';
import { useServerCheck } from './composables/useServerCheck';
import { ElMessage } from 'element-plus';
import { FolderOpened, Connection, Setting, Document } from '@element-plus/icons-vue';
import TimelinePanel from './components/TimelinePanel.vue';

const route = useRoute();
const projectStore = useProjectStore();
const { isConnected, checkConnection, autoCheck } = useServerCheck();

const activeMenu = computed(() => route.path);
const currentProject = computed(() => projectStore.currentProject);
const projectOptions = computed(() => projectStore.projects);
const projectLoading = computed(() => projectStore.loading);
const projectSelect = ref<string>();
const createDialogVisible = ref(false);
const creatingProject = ref(false);
const createForm = ref({
  name: '',
  displayName: '',
  description: '',
});
const deleteDialogVisible = ref(false);
const deletingProject = ref(false);
const deleteProjectName = ref<string>('');
const deleteConfirmName = ref<string>('');
const healthChecking = ref(false);

const checkHealth = async () => {
  healthChecking.value = true;
  await checkConnection(true);
  healthChecking.value = false;
};

const onProjectChange = async (value: string) => {
  await projectStore.switchProject(value);
};

const openDeleteProjectDialog = () => {
  if (!projectSelect.value) return;
  deleteProjectName.value = projectSelect.value;
  deleteConfirmName.value = '';
  deleteDialogVisible.value = true;
};

const handleDeleteProject = async () => {
  if (!deleteProjectName.value || deleteConfirmName.value !== deleteProjectName.value) {
    return;
  }
  deletingProject.value = true;
  try {
    const result = await projectStore.deleteProject(deleteProjectName.value);
    if (result.code === 0) {
      ElMessage.success('项目删除成功');
      deleteDialogVisible.value = false;
      // 项目列表会自动更新，当前项目也会自动切换
      if (projectStore.projects.length > 0) {
        projectSelect.value = projectStore.currentProject;
      } else {
        projectSelect.value = undefined;
      }
    }
  } catch (e) {
    // deleteProject 内部已通过 axios 拦截器提示错误
  } finally {
    deletingProject.value = false;
  }
};

const openCreateProjectDialog = () => {
  createForm.value = {
    name: '',
    displayName: '',
    description: '',
  };
  createDialogVisible.value = true;
};

const handleCreateProject = async () => {
  if (!createForm.value.name) {
    ElMessage.warning('请输入项目标识');
    return;
  }
  const namePattern = /^[a-zA-Z0-9_-]+$/;
  if (!namePattern.test(createForm.value.name)) {
    ElMessage.error('项目标识只能包含字母、数字、下划线和连字符');
    return;
  }

  creatingProject.value = true;
  try {
    const result = await projectStore.createProject({
      name: createForm.value.name,
      display_name: createForm.value.displayName || createForm.value.name,
      description: createForm.value.description || undefined,
    });
    if (result.code === 0) {
      ElMessage.success('项目创建成功');
      createDialogVisible.value = false;
      projectSelect.value = result.data.name;
    }
  } catch (e) {
    // createProject 内部已通过 axios 拦截器提示错误
  } finally {
    creatingProject.value = false;
  }
};

// 同步 projectSelect 与 currentProject
watch(
  () => projectStore.currentProject,
  (val) => {
    if (val !== projectSelect.value) {
      projectSelect.value = val;
    }
  },
  { immediate: true }
);

// 应用启动时自动检查连接
onMounted(async () => {
  autoCheck();
  await projectStore.loadProjects();
  // 确保 projectSelect 与 currentProject 同步
  if (projectStore.currentProject) {
    projectSelect.value = projectStore.currentProject;
  }
});
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.app-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-title {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.app-sidebar {
  background-color: #f5f5f5;
  border-right: 1px solid #e4e7ed;
}

.sidebar-menu {
  border-right: none;
}

.app-main {
  background-color: #ffffff;
  padding: 20px;
}
</style>
