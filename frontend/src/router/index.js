import { createRouter, createWebHistory } from 'vue-router';
import UploadScreen from '../views/UploadScreen.vue';
import ProcessingScreen from '../views/ProcessingScreen.vue';
import ResultsScreen from '../views/ResultsScreen.vue';
import ChatScreen from '../views/ChatScreen.vue';
import AuthScreen from '../views/AuthScreen.vue';

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
    beforeEnter: (to, from, next) => {
      const isAuthenticated = localStorage.getItem('access_token');
      if (isAuthenticated) {
        next('/spaces/default');
      } else {
        next();
      }
    },
  },
  {
    path: '/processing',
    name: 'Processing',
    component: ProcessingScreen,
    beforeEnter: (to, from, next) => {
      const isAuthenticated = localStorage.getItem('access_token');
      if (isAuthenticated) {
        next();
      } else {
        next('/login');
      }
    },
  },
  {
    path: '/results',
    name: 'Results',
    component: ResultsScreen,
  },
  {
    path: '/spaces/:spaceId',
    name: 'Chat',
    component: ChatScreen,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router; 