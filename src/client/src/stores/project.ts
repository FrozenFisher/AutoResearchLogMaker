import { defineStore } from 'pinia';
import { ref } from 'vue';
import { api } from '../api';

export interface ProjectItem {
  name: string;
  display_name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  is_current?: boolean;
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<ProjectItem[]>([]);
  const currentProject = ref<string>('default_project');
  const loading = ref(false);

  async function loadProjects() {
    loading.value = true;
    try {
      const result = await api.getProjects();
      if (result.code === 0 && result.data) {
        projects.value = result.data.projects || [];
        if (result.data.current_project) {
          currentProject.value = result.data.current_project;
        } else if (projects.value.length > 0) {
          currentProject.value = projects.value[0].name;
        }
      }
    } finally {
      loading.value = false;
    }
  }

  async function createProject(payload: {
    name: string;
    display_name?: string;
    description?: string;
  }) {
    const result = await api.createProject(payload);
    if (result.code === 0 && result.data) {
      await loadProjects();
      currentProject.value = result.data.name;
    }
    return result;
  }

  async function switchProject(name: string) {
    if (!name || name === currentProject.value) return;
    const result = await api.switchProject({ name });
    if (result.code === 0) {
      currentProject.value = name;
      await loadProjects();
    }
    return result;
  }

  async function deleteProject(name: string) {
    if (!name) return;
    const result = await api.deleteProject(name);
    if (result.code === 0) {
      await loadProjects();
      // 如果删除的是当前项目，切换到第一个可用项目或清空
      if (currentProject.value === name) {
        if (projects.value.length > 0) {
          currentProject.value = projects.value[0].name;
          await switchProject(projects.value[0].name);
        } else {
          currentProject.value = '';
        }
      }
    }
    return result;
  }

  function setProject(projectName: string) {
    currentProject.value = projectName;
  }

  return {
    projects,
    currentProject,
    loading,
    loadProjects,
    createProject,
    switchProject,
    deleteProject,
    setProject,
  };
});
