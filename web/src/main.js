import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import id from 'element-plus/es/locale/lang/id'
import 'iconify-icon'

import 'element-plus/dist/index.css'
import '@/styles/tema.css'

import App from './App.vue'
import router from './router'

// Locale Indonesia bawaan Element Plus mengisi datepicker.year dengan "Tahun",
// dan komponennya merangkai angka tahun langsung dengan kata itu sehingga
// kepala kalender berbunyi "2026 Tahun Agustus". Kata itu dikosongkan supaya
// tinggal "2026 Agustus"; angka tahunnya tetap ada karena tanpa itu tidak
// ketahuan sedang menjelajah tahun berapa.
const localeId = {
  ...id,
  el: { ...id.el, datepicker: { ...id.el.datepicker, year: '' } },
}

createApp(App)
  .use(createPinia())
  .use(router)
  .use(ElementPlus, { locale: localeId })
  .mount('#app')
