import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: '/',
      component: () => import('../components/login.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../components/login.vue'),
    },
    {
      path: '/signin',
      name: 'signin',
      component: () => import('../components/signin.vue'),
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('../components/forgot-password.vue'),
    },
    {
      path: '/reset-password/:email',
      name: 'reset-password',
      component: () => import('../components/reset-password.vue'),
    },
    {
      path: '/workbench',
      name: 'workbench',
      component: () => import('../components/workbench.vue'),
      children: [
        {
          path: '/workbench/booklist',
          component: () => import('../views/booklist.vue'),
        },
        {
          path: '/workbench/createbook',
          component: () => import('../views/createbook.vue'),
          children: [
            {
              path: '/workbench/createbook/bookinfoform',
              component: () => import('../views/book-tool/bookinfoform.vue'),
            },
            {
              path: '/workbench/createbook/character',
              component: () => import('../views/book-tool/characterinfo.vue'),
            },
            {
              path: '/workbench/createbook/characterlist',
              component: () => import('../views/book-tool/characterlist.vue'),
            },
            {
              path: '/workbench/createbook/scene',
              component: () => import('../views/book-tool/sceneinfo.vue'),
            },
            {
              path: '/workbench/createbook/scenelist',
              component: () => import('../views/book-tool/scenelist.vue'),
            },
            {
              path: '/workbench/createbook/newcreationcharacter',
              component: () => import('../views/book-tool/new-creationcharacter.vue'),
            },
            {
              path: '/workbench/createbook/zero',
              component: () => import('../views/book-tool/zeropage.vue'),
            },
          ],
        },
        {
          path: '/workbench/empty',
          component: () => import('../views/empty.vue'),
        },
      ],
    },
  ],
})

export default router
