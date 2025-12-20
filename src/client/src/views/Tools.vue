<template>
  <div class="tools-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>工具配置</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加工具
          </el-button>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>

      <el-table v-else :data="tools" style="width: 100%">
        <el-table-column prop="name" label="工具名称" width="200" />
        <el-table-column prop="type" label="类型" width="150" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="editTool(row)">
              编辑
            </el-button>
            <el-button link type="danger" size="small" @click="deleteTool(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑工具对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingTool ? '编辑工具' : '添加工具'"
      width="600px"
    >
      <el-form :model="toolForm" label-width="100px">
        <el-form-item label="工具名称" required>
          <el-input v-model="toolForm.name" placeholder="输入工具名称" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="toolForm.type" placeholder="选择工具类型" @change="onTypeChange">
            <el-option
              v-for="item in toolTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="toolForm.description"
            type="textarea"
            :rows="3"
            placeholder="输入工具描述"
          />
        </el-form-item>
        <el-form-item label="配置">
          <el-input
            v-model="toolForm.configJson"
            type="textarea"
            :rows="6"
            :placeholder="currentTemplatePlaceholder"
          />
          <div v-if="currentTemplateHelp" class="template-help">
            {{ currentTemplateHelp }}
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTool" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { api } from '../api';

const tools = ref<any[]>([]);
const loading = ref(false);
const showAddDialog = ref(false);
const editingTool = ref<any>(null);
const saving = ref(false);
const toolForm = ref({
  name: '',
  type: 'custom',
  description: '',
  configJson: '{}',
});
const defaultTools = ref<Record<string, any>>({});
const templates = ref<Record<string, any>>({});

const toolTypeOptions = computed(() => {
  const tpl = templates.value || {};
  return Object.keys(tpl).map((key) => ({
    value: key,
    label: tpl[key].label || key,
  }));
});

const currentTemplate = computed(() => {
  return templates.value[toolForm.value.type] || null;
});

const currentTemplatePlaceholder = computed(() => {
  if (!currentTemplate.value) {
    return '输入 JSON 配置，例如: {"server_url": "https://example.com"}';
  }
  const fields = currentTemplate.value.fields || [];
  const example: Record<string, any> = {};
  fields.forEach((f: any) => {
    example[f.name] = f.default ?? null;
  });
  return (
    '根据下方字段说明填写 JSON 配置，例如：\n' +
    JSON.stringify(example, null, 2)
  );
});

const currentTemplateHelp = computed(() => {
  if (!currentTemplate.value) return '';
  const desc = currentTemplate.value.description || '';
  const fields = currentTemplate.value.fields || [];
  const fieldLines = fields.map(
    (f: any) =>
      `- ${f.label || f.name} (${f.name}): ${f.help || ''} ` +
      (f.required ? '[必填]' : '')
  );
  return [desc, ...fieldLines].join('\n');
});

const loadTools = async () => {
  loading.value = true;
  try {
    const [listResult, defaultResult, templateResult] = await Promise.all([
      api.getToolList(),
      api.getDefaultTools(),
      api.getToolTemplates(),
    ]);
    if (listResult.code === 0) {
      const raw = listResult.data;
      if (Array.isArray(raw)) {
        tools.value = raw;
      } else if (raw && typeof raw === 'object') {
        // 后端返回的是 { tool_name: config, ... } 的对象，这里转成数组
        tools.value = Object.values(raw);
      } else {
        tools.value = [];
      }
    }
    if (defaultResult.code === 0) {
      defaultTools.value = defaultResult.data?.default_tools || {};
    }
    if (templateResult.code === 0) {
      templates.value = templateResult.data || {};
    }
  } catch (error) {
    ElMessage.error('加载工具配置失败');
    console.error('Load tools error:', error);
  } finally {
    loading.value = false;
  }
};

const editTool = async (tool: any) => {
  editingTool.value = tool;
  toolForm.value = {
    name: tool.name,
    type: tool.type || 'custom',
    description: tool.description || '',
    configJson: JSON.stringify(tool.config || {}, null, 2),
  };
  showAddDialog.value = true;
};

const onTypeChange = () => {
  // 切换类型时，如果存在模板，则用模板默认值初始化配置
  if (currentTemplate.value) {
    const fields = currentTemplate.value.fields || [];
    const config: Record<string, any> = {};
    fields.forEach((f: any) => {
      config[f.name] = f.default ?? null;
    });
    toolForm.value.configJson = JSON.stringify(config, null, 2);
  }
};

const deleteTool = async (tool: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这个工具吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    ElMessage.info('删除功能开发中...');
  } catch {
    // 用户取消
  }
};

const saveTool = async () => {
  if (!toolForm.value.name) {
    ElMessage.warning('请输入工具名称');
    return;
  }

  try {
    JSON.parse(toolForm.value.configJson);
  } catch {
    ElMessage.error('配置 JSON 格式错误');
    return;
  }

  saving.value = true;
  try {
    const config = {
      name: toolForm.value.name,
      type: toolForm.value.type,
      description: toolForm.value.description,
      config: JSON.parse(toolForm.value.configJson),
      enabled: true,
    };

    let result;
    if (editingTool.value) {
      result = await api.editTool(toolForm.value.name, config);
    } else {
      result = await api.addTool(toolForm.value.name, config);
    }

    if (result.code === 0) {
      ElMessage.success(editingTool.value ? '编辑成功' : '添加成功');
      showAddDialog.value = false;
      resetForm();
      await loadTools();
    } else {
      throw new Error(result.message || '保存失败');
    }
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败');
    console.error('Save tool error:', error);
  } finally {
    saving.value = false;
  }
};

const resetForm = () => {
  editingTool.value = null;
  toolForm.value = {
    name: '',
    type: 'custom',
    description: '',
    configJson: '{}',
  };
};

onMounted(() => {
  loadTools();
});
</script>

<style scoped>
.tools-page {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-container {
  padding: 40px 0;
}
</style>
