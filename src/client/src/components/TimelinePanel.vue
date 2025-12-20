<template>
  <div class="timeline-panel">
    <div class="timeline-header">
      <span class="timeline-title">时间线</span>
      <span class="timeline-project" v-if="currentProject">[{{ currentProject }}]</span>
    </div>
    <div v-if="loading" class="timeline-loading">
      <el-skeleton :rows="5" animated />
    </div>
    <div v-else-if="treeData.length === 0" class="timeline-empty">
      <el-empty description="暂无记录" :image-size="60" />
    </div>
    <div v-else class="timeline-tree">
      <el-tree
        :data="treeData"
        :props="treeProps"
        node-key="id"
        highlight-current
        :default-expand-all="false"
        @node-click="onNodeClick"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch, provide } from 'vue';
import { useRouter } from 'vue-router';
import { useProjectStore } from '../stores/project';
import { api, type WorkflowInfo } from '../api';

interface TimelineNode {
  id: string;
  label: string;
  type: 'date' | 'category-files' | 'category-workflows' | 'file' | 'workflow';
  date?: string;
  file?: any;
  workflow?: WorkflowInfo;
  children?: TimelineNode[];
}

const router = useRouter();
const projectStore = useProjectStore();

const currentProject = computed(() => projectStore.currentProject);

const dates = ref<string[]>([]);
const filesByDate = ref<Record<string, any[]>>({});
const workflowsByDate = ref<Record<string, WorkflowInfo[]>>({});
const loading = ref(false);

const treeProps = {
  children: 'children',
  label: 'label',
};

const treeData = computed<TimelineNode[]>(() => {
  const dateSet = new Set<string>();
  dates.value.forEach((d) => dateSet.add(d));
  Object.keys(workflowsByDate.value).forEach((d) => dateSet.add(d));

  const allDates = Array.from(dateSet).sort().reverse();

  return allDates.map((d) => {
    const fileChildren =
      (filesByDate.value[d] || []).map((f, index) => ({
        id: `${d}-file-${index}`,
        label: f.filename,
        type: 'file' as const,
        date: d,
        file: f,
      })) || [];

    const workflowChildren =
      (workflowsByDate.value[d] || []).map((w, index) => ({
        id: `${d}-wf-${index}`,
        label: w.name || w.wf_id,
        type: 'workflow' as const,
        date: d,
        workflow: w,
      })) || [];

    const children: TimelineNode[] = [];
    children.push({
      id: `${d}-files`,
      label: '文件',
      type: 'category-files',
      date: d,
      children: fileChildren,
    });
    children.push({
      id: `${d}-workflows`,
      label: '工作流',
      type: 'category-workflows',
      date: d,
      children: workflowChildren,
    });

    return {
      id: d,
      label: d,
      type: 'date',
      date: d,
      children,
    } as TimelineNode;
  });
});

const loadDates = async () => {
  if (!currentProject.value) return;
  try {
    const result = await api.getRecordDates(currentProject.value);
    if (result.code === 0 && Array.isArray(result.data)) {
      dates.value = result.data;
    } else {
      dates.value = [];
    }
  } catch (error) {
    console.error('Timeline load dates error:', error);
    dates.value = [];
  }
};

const loadWorkflows = async () => {
  if (!currentProject.value) return;
  try {
    const result = await api.getWorkflowList(currentProject.value);
    if (result.code === 0 && Array.isArray(result.data)) {
      const map: Record<string, WorkflowInfo[]> = {};
      for (const w of result.data as any as WorkflowInfo[]) {
        const t =
          (w.started_at as string | undefined) ||
          (w.finished_at as string | undefined) ||
          (w as any).created_at;
        const dateStr =
          typeof t === 'string' && t.length >= 10
            ? t.slice(0, 10)
            : '未知日期';
        if (!map[dateStr]) {
          map[dateStr] = [];
        }
        map[dateStr].push(w);
      }
      workflowsByDate.value = map;
    } else {
      workflowsByDate.value = {};
    }
  } catch (error) {
    console.error('Timeline load workflows error:', error);
    workflowsByDate.value = {};
  }
};

const loadFilesForDate = async (date: string) => {
  if (!currentProject.value || !date) return;
  try {
    const result = await api.getMetadata(currentProject.value, date);
    if (result.code === 0) {
      filesByDate.value[date] = result.data?.files || [];
    } else {
      filesByDate.value[date] = [];
    }
  } catch (error: any) {
    if (error?.response?.data?.code === 3) {
      filesByDate.value[date] = [];
    } else {
      console.error('Timeline load files error:', error);
      filesByDate.value[date] = [];
    }
  }
};

const refreshTimeline = async () => {
  loading.value = true;
  try {
    filesByDate.value = {};
    workflowsByDate.value = {};
    dates.value = [];
    await Promise.all([loadDates(), loadWorkflows()]);
  } finally {
    loading.value = false;
  }
};

const onNodeClick = async (node: TimelineNode) => {
  if (!node) return;

  if (node.type === 'file' && node.file && node.date) {
    await router.push({
      path: '/files',
      query: { date: node.date, file: node.file.file_id },
    });
    return;
  }

  if (node.type === 'workflow' && node.workflow && node.date) {
    await router.push({
      path: '/workflow',
      query: { wf_id: node.workflow.wf_id, date: node.date },
    });
    return;
  }

  if (node.type === 'date' && node.date) {
    if (!filesByDate.value[node.date]) {
      await loadFilesForDate(node.date);
    }
    // 默认跳转到文件页面，定位到该日期
    await router.push({ path: '/files', query: { date: node.date } });
  }
};

watch(
  () => currentProject.value,
  async (val, oldVal) => {
    if (val && val !== oldVal) {
      await refreshTimeline();
    }
  },
  { immediate: true }
);

onMounted(async () => {
  if (currentProject.value) {
    await refreshTimeline();
  }
});

// 暴露刷新方法供其他组件调用
provide('refreshTimeline', refreshTimeline);
</script>

<style scoped>
.timeline-panel {
  height: 100%;
  padding: 8px 0 8px 8px;
  box-sizing: border-box;
  border-left: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px 8px;
}

.timeline-title {
  font-size: 14px;
  font-weight: 500;
}

.timeline-project {
  font-size: 12px;
  color: #909399;
}

.timeline-loading,
.timeline-empty {
  padding: 8px;
}

.timeline-tree {
  flex: 1;
  overflow: auto;
  padding-right: 4px;
}
</style>


