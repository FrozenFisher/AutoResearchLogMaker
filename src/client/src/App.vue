<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <h1 class="app-title">AutoResearchLogMaker</h1>
        <el-space>
          <el-text v-if="currentProject" type="info">
            当前项目: {{ currentProject }}
          </el-text>
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
    <el-container>
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
        </el-menu>
      </el-aside>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useProjectStore } from './stores/project';
import { useServerCheck } from './composables/useServerCheck';
import { ElMessage } from 'element-plus';
import { FolderOpened, Connection, Setting, Document } from '@element-plus/icons-vue';

const route = useRoute();
const projectStore = useProjectStore();
const { isConnected, checkConnection, autoCheck } = useServerCheck();

const activeMenu = computed(() => route.path);
const currentProject = computed(() => projectStore.currentProject);
const healthChecking = ref(false);

const checkHealth = async () => {
  healthChecking.value = true;
  await checkConnection(true);
  healthChecking.value = false;
};

// 应用启动时自动检查连接
onMounted(() => {
  autoCheck();
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
