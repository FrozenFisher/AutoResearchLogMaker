<template>
  <div class="settings-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>LLM 设置</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px" class="settings-form">
        <el-form-item label="LLM Base URL" required>
          <el-input
            v-model="form.baseUrl"
            placeholder="例如：http://127.0.0.1:8001 或 https://api.example.com/v1"
          />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="form.apiKey"
            type="password"
            show-password
            placeholder="可选，OpenAI 兼容接口的 API Key"
          />
        </el-form-item>
        <el-form-item label="默认模型">
          <el-select
            v-model="form.defaultModel"
            placeholder="可选，默认使用的模型 ID"
            filterable
            allow-create
            default-first-option
            style="width: 100%"
          >
            <el-option
              v-for="m in models"
              :key="m.id"
              :label="m.id"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="saving"
            @click="saveConfig"
          >
            保存
          </el-button>
          <el-button
            :loading="testing"
            @click="testConnection"
          >
            测试连接并获取模型
          </el-button>
          <el-button
            :loading="reinitializing"
            @click="reinitializeModels"
          >
            重新初始化模型
          </el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div class="status-section">
        <div class="status-header">
          <span class="status-title">模型初始化状态</span>
        </div>
        <div v-if="statusLoading" class="status-loading">
          <el-skeleton :rows="3" animated />
        </div>
        <div v-else class="status-content">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="LangChain 可用">
              <el-tag :type="llmStatus.langchain_available ? 'success' : 'danger'">
                {{ llmStatus.langchain_available ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="OpenAI 已配置">
              <el-tag :type="llmStatus.openai_configured ? 'success' : 'warning'">
                {{ llmStatus.openai_configured ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="已初始化模型数量">
              {{ llmStatus.available_models }}
            </el-descriptions-item>
            <el-descriptions-item label="已初始化模型列表">
              <el-space wrap>
                <el-tag
                  v-for="model in llmStatus.models"
                  :key="model"
                  :type="model === llmStatus.default_model ? 'primary' : 'info'"
                >
                  {{ model }}
                  <span v-if="model === llmStatus.default_model" style="margin-left: 4px">(默认)</span>
                </el-tag>
                <span v-if="llmStatus.models.length === 0" style="color: #909399">暂无已初始化模型</span>
              </el-space>
            </el-descriptions-item>
            <el-descriptions-item label="默认模型">
              {{ llmStatus.default_model || '未设置' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <el-divider />

      <div class="models-section">
        <div class="models-header">
          <span class="models-title">可用模型</span>
          <span class="models-subtitle">从当前 LLM Base URL 获取的 /v1/models 列表</span>
        </div>
        <div v-if="modelsLoading" class="models-loading">
          <el-skeleton :rows="5" animated />
        </div>
        <div v-else-if="models.length === 0" class="models-empty">
          <el-empty description="暂无模型信息，点击“测试连接并获取模型”试试" :image-size="80" />
        </div>
        <div v-else>
          <el-table :data="models" style="width: 100%">
            <el-table-column prop="id" label="模型 ID" />
            <el-table-column prop="owned_by" label="Owned By" width="200" />
            <el-table-column prop="object" label="Object" width="150" />
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { api } from '../api';

const form = ref({
  baseUrl: '',
  apiKey: '',
  defaultModel: '',
});

const saving = ref(false);
const testing = ref(false);
const reinitializing = ref(false);
const modelsLoading = ref(false);
const statusLoading = ref(false);
const models = ref<Array<{ id: string; owned_by?: string; object?: string }>>([]);
const llmStatus = ref({
  langchain_available: false,
  openai_configured: false,
  available_models: 0,
  models: [] as string[],
  default_model: '',
});

const loadConfig = async () => {
  try {
    const result = await api.getLlmConfig();
    if (result.code === 0 && result.data) {
      form.value.baseUrl = result.data.base_url || '';
      // apiKey 不回显，仅保留占位
      form.value.apiKey = '';
      form.value.defaultModel = result.data.default_model || '';
    }
  } catch (error) {
    console.error('Load LLM config error:', error);
  }
};

const saveConfig = async () => {
  if (!form.value.baseUrl) {
    ElMessage.warning('请填写 LLM Base URL');
    return;
  }
  saving.value = true;
  try {
    const result = await api.updateLlmConfig({
      base_url: form.value.baseUrl,
      api_key: form.value.apiKey || undefined,
      default_model: form.value.defaultModel || undefined,
    });
    if (result.code === 0) {
      ElMessage.success(result.message || '配置已保存');
      // 保存后自动加载状态（因为后端会自动初始化）
      await loadStatus();
    }
  } catch (error) {
    console.error('Save LLM config error:', error);
  } finally {
    saving.value = false;
  }
};

const loadModels = async () => {
  modelsLoading.value = true;
  try {
    const result = await api.getLlmModels();
    if (result.code === 0 && Array.isArray(result.data)) {
      models.value = result.data;
    } else {
      models.value = [];
    }
  } catch (error) {
    console.error('Load LLM models error:', error);
    models.value = [];
  } finally {
    modelsLoading.value = false;
  }
};

const testConnection = async () => {
  testing.value = true;
  try {
    await saveConfig();
    await loadModels();
    if (models.value.length > 0) {
      ElMessage.success(`连接成功，发现 ${models.value.length} 个模型`);
    } else {
      ElMessage.warning('连接成功，但未返回任何模型');
    }
  } finally {
    testing.value = false;
  }
};

const loadStatus = async () => {
  statusLoading.value = true;
  try {
    const result = await api.getLlmStatus();
    if (result.code === 0 && result.data) {
      llmStatus.value = {
        langchain_available: result.data.langchain_available || false,
        openai_configured: result.data.openai_configured || false,
        available_models: result.data.available_models || 0,
        models: result.data.models || [],
        default_model: result.data.default_model || '',
      };
    }
  } catch (error) {
    console.error('Load LLM status error:', error);
  } finally {
    statusLoading.value = false;
  }
};

const reinitializeModels = async () => {
  reinitializing.value = true;
  try {
    const result = await api.reinitializeLlmModels();
    if (result.code === 0) {
      ElMessage.success(result.message || '模型重新初始化成功');
      await loadStatus();
    } else {
      ElMessage.error(result.message || '模型重新初始化失败');
    }
  } catch (error) {
    console.error('Reinitialize LLM models error:', error);
    ElMessage.error('重新初始化模型失败');
  } finally {
    reinitializing.value = false;
  }
};

onMounted(() => {
  loadConfig();
  loadStatus();
});
</script>

<style scoped>
.settings-page {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-form {
  max-width: 640px;
}

.models-section {
  margin-top: 16px;
}

.models-header {
  margin-bottom: 8px;
}

.models-title {
  font-weight: 500;
  margin-right: 8px;
}

.models-subtitle {
  font-size: 12px;
  color: #909399;
}

.models-loading,
.models-empty {
  padding: 12px 0;
}

.status-section {
  margin-top: 16px;
}

.status-header {
  margin-bottom: 12px;
}

.status-title {
  font-weight: 500;
  font-size: 14px;
}

.status-loading {
  padding: 12px 0;
}

.status-content {
  padding: 12px 0;
}
</style>


