import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import id from 'element-plus/es/locale/lang/id'
import 'iconify-icon'

import 'element-plus/dist/index.css'
import '@/styles/tema.css'

import App from './App.vue'
import router from './router'

createApp(App)
  .use(createPinia())
  .use(router)
  .use(ElementPlus, { locale: id })
  .mount('#app')
