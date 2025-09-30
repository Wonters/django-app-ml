import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Models from '@/views/Models.vue'
import Experiments from '@/views/Experiments.vue'
import Predictions from '@/views/Predictions.vue'
import Tasks from '@/views/Tasks.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { title: 'Dashboard - Django ML App' }
  },
  {
    path: '/models',
    name: 'Models',
    component: Models,
    meta: { title: 'Modèles - Django ML App' }
  },
  {
    path: '/experiments',
    name: 'Experiments',
    component: Experiments,
    meta: { title: 'Expériences - Django ML App' }
  },
  {
    path: '/predictions',
    name: 'Predictions',
    component: Predictions,
    meta: { title: 'Prédictions - Django ML App' }
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: Tasks,
    meta: { title: 'Tâches - Django ML App' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard pour mettre à jour le titre de la page
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }
  next()
})

export default router 