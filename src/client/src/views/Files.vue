<template>
  <div class="files-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>文件管理</span>
          <el-space>
            <el-date-picker
              v-model="selectedDate"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="loadFiles"
            />
            <el-button type="primary" @click="showUploadDialog = true">
              <el-icon><Upload /></el-icon>
              上传文件
            </el-button>
          </el-space>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="files.length === 0" class="empty-container">
        <el-empty description="暂无文件，请上传文件" />
      </div>

      <el-table
        v-else
        :data="files"
        style="width: 100%"
        @row-dblclick="previewFile"
      >
        <el-table-column prop="filename" label="文件名" width="300" />
        <el-table-column prop="size_bytes" label="大小" width="120">
          <template #default="{ row }">
            {{ row.size_bytes ? formatFileSize(row.size_bytes) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="150" />
        <el-table-column prop="uploaded_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.uploaded_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" width="200">
          <template #default="{ row }">
            <el-tag
              v-for="tag in row.tags"
              :key="tag"
              size="small"
              style="margin-right: 4px"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="previewFile(row)">
              预览
            </el-button>
            <el-button link type="danger" size="small" @click="deleteFile(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文件" width="500px">
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
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、图片、Excel 文件，单个文件不超过 50MB
          </div>
        </template>
      </el-upload>

      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="uploadFiles" :loading="uploading">
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 文件预览 -->
    <el-drawer
      v-model="previewVisible"
      title="文件预览"
      size="60%"
      :with-header="true"
    >
      <div v-if="previewLoading" class="preview-loading">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="!previewUrl && !previewText" class="preview-empty">
        <el-empty description="请选择要预览的文件" />
      </div>
      <div v-else class="preview-content">
        <template v-if="previewType === 'image'">
          <img :src="previewUrl" class="preview-image" />
        </template>
        <template v-else-if="previewType === 'pdf'">
          <iframe :src="previewUrl" class="preview-iframe" />
        </template>
        <template v-else>
          <pre class="preview-text">{{ previewText }}</pre>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, inject } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus';
import { Upload, UploadFilled } from '@element-plus/icons-vue';
import { useProjectStore } from '../stores/project';
import { api } from '../api';
import dayjs from 'dayjs';

const route = useRoute();
const projectStore = useProjectStore();
const selectedDate = ref(dayjs().format('YYYY-MM-DD'));
const files = ref<any[]>([]);
const loading = ref(false);
const showUploadDialog = ref(false);
const uploadRef = ref();
const fileList = ref<UploadFile[]>([]);
const uploading = ref(false);

const previewVisible = ref(false);
const previewLoading = ref(false);
const previewUrl = ref<string>('');
const previewType = ref<'image' | 'pdf' | 'text'>('text');
const previewText = ref<string>('');

const currentProject = computed(() => projectStore.currentProject);

// 注入时间线刷新方法
const refreshTimeline = inject<() => Promise<void>>('refreshTimeline');

const loadFiles = async () => {
  if (!selectedDate.value) {
    return;
  }

  loading.value = true;
  try {
    const result = await api.getMetadata(currentProject.value, selectedDate.value);
    if (result.code === 0) {
      files.value = result.data?.files || [];
    } else if (result.code === 3 && result.message === 'metadata not found') {
      // 元数据不存在（该日期还没有文件），这是正常的
      files.value = [];
    } else {
      ElMessage.warning(result.message || '加载文件列表失败');
      files.value = [];
    }
  } catch (error: any) {
    console.error('Load files error:', error);
    // 如果是元数据不存在的错误，静默处理
    if (error?.response?.data?.code === 3) {
      files.value = [];
    } else {
      ElMessage.error('加载文件列表失败');
      files.value = [];
    }
  } finally {
    loading.value = false;
  }
};

const handleFileChange = (file: UploadFile) => {
  console.log('File changed:', file);
};

const handleFileRemove = (file: UploadFile) => {
  console.log('File removed:', file);
};

const beforeUpload = (file: File) => {
  const isValidType =
    file.type === 'application/pdf' ||
    file.type.startsWith('image/') ||
    file.type.includes('excel') ||
    file.type.includes('spreadsheet');

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

const uploadFiles = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件');
    return;
  }

  uploading.value = true;
  const uploadedCount = { success: 0, fail: 0 };

  try {
    for (const file of fileList.value) {
      if (file.raw) {
        try {
          await api.uploadFile(currentProject.value, selectedDate.value!, file.raw, {
            source: 'manual_upload',
            tags: [],
            notes: '',
          });
          uploadedCount.success++;
        } catch (error) {
          uploadedCount.fail++;
          console.error('Upload file error:', error);
        }
      }
    }

    if (uploadedCount.success > 0) {
      ElMessage.success(`成功上传 ${uploadedCount.success} 个文件`);
      showUploadDialog.value = false;
      fileList.value = [];
      uploadRef.value?.clearFiles();
      await loadFiles();
      // 刷新时间线
      if (refreshTimeline) {
        await refreshTimeline();
      }
    }

    if (uploadedCount.fail > 0) {
      ElMessage.warning(`${uploadedCount.fail} 个文件上传失败`);
    }
  } finally {
    uploading.value = false;
  }
};

const previewFile = async (file: any) => {
  const row = file?.filename ? file : file?.row || file;
  if (!row || !row.filename) return;

  previewVisible.value = true;
  previewLoading.value = true;
  previewUrl.value = '';
  previewText.value = '';

  try {
    const blob = await api.previewFile(
      currentProject.value,
      selectedDate.value!,
      row.filename
    );
    const mime = (blob as any).type as string;
    const url = URL.createObjectURL(blob as any);

    if (mime.startsWith('image/')) {
      previewType.value = 'image';
      previewUrl.value = url;
    } else if (mime === 'application/pdf') {
      previewType.value = 'pdf';
      previewUrl.value = url;
    } else {
      previewType.value = 'text';
      const text = await (blob as Blob).text();
      previewText.value = text;
    }
  } catch (error) {
    ElMessage.error('预览文件失败');
    console.error('Preview file error:', error);
  } finally {
    previewLoading.value = false;
  }
};

const deleteFile = async (file: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这个文件吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    ElMessage.info('删除功能开发中...');
  } catch {
    // 用户取消
  }
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

const formatTime = (time: string): string => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss');
};

onMounted(async () => {
  const qDate = route.query.date;
  if (typeof qDate === 'string') {
    selectedDate.value = qDate;
  }
  await loadFiles();

  const qFile = route.query.file;
  if (typeof qFile === 'string') {
    const f = files.value.find((x) => x.file_id === qFile);
    if (f) {
      await previewFile(f);
    }
  }
});

watch(
  () => route.query.date,
  async (val) => {
    if (typeof val === 'string' && val !== selectedDate.value) {
      selectedDate.value = val;
      await loadFiles();
    }
  }
);
</script>

<style scoped>
.files-page {
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

.preview-loading,
.preview-empty {
  padding: 20px;
}

.preview-content {
  width: 100%;
  height: 100%;
  overflow: auto;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  display: block;
  margin: 0 auto;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.preview-text {
  white-space: pre-wrap;
  font-family: Menlo, Monaco, Consolas, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}
</style>


