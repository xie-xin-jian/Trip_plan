import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import App from './App.vue'
import Home from './views/Home.vue'
import Result from './views/Result.vue'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import MyPlans from './views/MyPlans.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Home', component: Home },
    { path: '/result', name: 'Result', component: Result },
    { path: '/login', name: 'Login', component: Login },
    { path: '/register', name: 'Register', component: Register },
    { path: '/my-plans', name: 'MyPlans', component: MyPlans }
  ]
})

const app = createApp(App)

app.use(router)
app.use(Antd)

app.mount('#app')

