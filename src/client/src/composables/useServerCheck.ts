import { ref } from 'vue';
import { api } from '../api';
import { ElMessage } from 'element-plus';

export function useServerCheck() {
  const isChecking = ref(false);
  const isConnected = ref(false);
  const serverUrl = ref(import.meta.env.VITE_API_BASE || 'http://localhost:8000');

  const checkConnection = async (showMessage = true): Promise<boolean> => {
    isChecking.value = true;
    try {
      const result = await api.healthCheck();
      isConnected.value = true;
      if (showMessage) {
        ElMessage.success('服务器连接正常');
      }
      return true;
    } catch (error: any) {
      isConnected.value = false;
      if (showMessage) {
        let message = '无法连接到服务器';
        
        if (error?.code === 'ECONNREFUSED') {
          message = `无法连接到服务器 ${serverUrl.value}。请确保服务器已启动。`;
        } else if (error?.code === 'ETIMEDOUT') {
          message = '连接超时。请检查服务器状态。';
        } else {
          message = `连接失败: ${error?.message || '未知错误'}`;
        }
        
        ElMessage.error(message);
      }
      return false;
    } finally {
      isChecking.value = false;
    }
  };

  // 自动检查连接（启动时）
  const autoCheck = async () => {
    await checkConnection(false);
  };

  return {
    isChecking,
    isConnected,
    serverUrl,
    checkConnection,
    autoCheck,
  };
}
