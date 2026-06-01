import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import Tooltip from 'primevue/tooltip'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'
import './assets/styles/global.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      prefix: 'p',
      darkModeSelector: false
    }
  }
})
app.directive('tooltip', Tooltip)
app.use(ConfirmationService)
app.use(ToastService)
app.use(router)
app.mount('#app')
