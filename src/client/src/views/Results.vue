<template>
  <div class="results-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>结果查看</span>
          <el-date-picker
            v-model="selectedDate"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="loadResults"
          />
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>

      <div v-else-if="!summary" class="empty-container">
        <el-empty description="该日期暂无总结结果" />
      </div>

      <div v-else class="results-content">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-card>
              <template #header>
                <span>研究总结</span>
              </template>
              <div
                class="summary-content"
                v-html="renderedSummary"
              ></div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <template #header>
                <span>元数据</span>
              </template>
              <div class="metadata-content">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="日期">
                    {{ selectedDate }}
                  </el-descriptions-item>
                  <el-descriptions-item label="处理文件数">
                    {{ metadata?.files?.length || 0 }}
                  </el-descriptions-item>
                  <el-descriptions-item label="工作流ID">
                    {{ metadata?.workflow_id || '-' }}
                  </el-descriptions-item>
                </el-descriptions>

                <el-divider />

                <div v-if="metadata?.files && metadata.files.length > 0">
                  <h4>处理的文件：</h4>
                  <el-tag
                    v-for="file in metadata.files"
                    :key="file.file_id"
                    style="margin: 4px"
                  >
                    {{ file.filename }}
                  </el-tag>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { useProjectStore } from '../stores/project';
import { api } from '../api';
import dayjs from 'dayjs';
import { marked } from 'marked';

const projectStore = useProjectStore();
const selectedDate = ref(dayjs().format('YYYY-MM-DD'));
const loading = ref(false);
const summary = ref<string>('');
const metadata = ref<any>(null);

const currentProject = computed(() => projectStore.currentProject);

const renderedSummary = computed(() => {
  if (!summary.value) return '';
  try {
    return marked(summary.value);
  } catch (error) {
    return summary.value;
  }
});

const loadResults = async () => {
  if (!selectedDate.value) {
    return;
  }

  loading.value = true;
  try {
    const result = await api.getMetadata(currentProject.value, selectedDate.value);
    if (result.code === 0) {
      metadata.value = result.data;

      // 尝试读取总结内容
      // TODO: 根据实际的元数据结构读取 summary.auto_summary 路径
      if (result.data?.summary?.auto_summary) {
        // 这里需要从文件系统读取文件内容
        // 或者服务器需要提供直接返回总结内容的 API
        summary.value = result.data.summary.auto_summary;
      } else if (result.data?.summary_text) {
        summary.value = result.data.summary_text;
      } else if (result.data?.summary?.text) {
        summary.value = result.data.summary.text;
      } else {
        summary.value = '';
      }
    } else if (result.code === 3 && result.message === 'metadata not found') {
      // 元数据不存在，清空显示
      metadata.value = null;
      summary.value = '';
    } else {
      ElMessage.warning(result.message || '加载结果失败');
      metadata.value = null;
      summary.value = '';
    }
  } catch (error: any) {
    console.error('Load results error:', error);
    // 如果是元数据不存在的错误，静默处理
    if (error?.response?.data?.code === 3) {
      metadata.value = null;
      summary.value = '';
    } else {
      ElMessage.error('加载结果失败');
      metadata.value = null;
      summary.value = '';
    }
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadResults();
});
</script>

<style scoped>
.results-page {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-container,
.empty-container {
  padding: 40px 0;
}

.results-content {
  margin-top: 20px;
}

.summary-content {
  line-height: 1.8;
  color: #333;
}

.summary-content :deep(h1),
.summary-content :deep(h2),
.summary-content :deep(h3) {
  margin-top: 20px;
  margin-bottom: 10px;
}

.summary-content :deep(p) {
  margin-bottom: 10px;
}

.summary-content :deep(ul),
.summary-content :deep(ol) {
  margin-left: 20px;
  margin-bottom: 10px;
}

.metadata-content {
  padding: 10px 0;
}
</style>
