import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useProjectStore = defineStore('project', () => {
  const currentProject = ref<string>('default_project');

  function setProject(projectName: string) {
    currentProject.value = projectName;
  }

  return {
    currentProject,
    setProject,
  };
});
