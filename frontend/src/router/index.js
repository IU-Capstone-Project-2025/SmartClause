import { createRouter, createWebHistory } from 'vue-router';
import UploadScreen from '../views/UploadScreen.vue';
import ProcessingScreen from '../views/ProcessingScreen.vue';
import ResultsScreen from '../views/ResultsScreen.vue';
import ChatScreen from '../views/ChatScreen.vue';
import AuthScreen from '../views/AuthScreen.vue';
import DocumentAnalysis from '../views/DocumentAnalysis.vue';

const routes = [
  {
    path: '/',
    name: 'Upload',
    component: UploadScreen,
  },
  {
    path: '/login',
    name: 'Login',
    component: AuthScreen,
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
  {
    path: '/spaces/:spaceId/documents/:documentId/analysis',
    name: 'Analysis',
    component: DocumentAnalysis,
    meta: { requiresAuth: true },
  },
  {
    path: '/spaces/:spaceId?',
    name: 'Chat',
    component: ChatScreen,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('access_token');
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);

  if (requiresAuth && !isAuthenticated) {
    next({ path: '/login', query: { redirect: to.fullPath } });
  } else if (to.path === '/login' && isAuthenticated) {
    next({ path: '/spaces', replace: true });
  } else {
    next();
  }
});

export default router; 