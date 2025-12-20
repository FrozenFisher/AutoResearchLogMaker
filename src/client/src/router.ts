import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/files',
    },
    {
      path: '/files',
      name: 'Files',
      component: () => import('./views/Files.vue'),
    },
    {
      path: '/workflow',
      name: 'Workflow',
      component: () => import('./views/Workflow.vue'),
    },
    {
      path: '/tools',
      name: 'Tools',
      component: () => import('./views/Tools.vue'),
    },
    {
      path: '/results',
      name: 'Results',
      component: () => import('./views/Results.vue'),
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('./views/Settings.vue'),
    },
  ],
});

export default router;
