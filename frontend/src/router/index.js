import { createRouter, createWebHistory } from 'vue-router';
import UploadScreen from '../views/UploadScreen.vue';
import ProcessingScreen from '../views/ProcessingScreen.vue';
import ResultsScreen from '../views/ResultsScreen.vue';

const routes = [
  {
    path: '/',
    name: 'Upload',
    component: UploadScreen,
  },
  {
    path: '/processing',
    name: 'Processing',
    component: ProcessingScreen,
  },
  {
    path: '/results',
    name: 'Results',
    component: ResultsScreen,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router; 