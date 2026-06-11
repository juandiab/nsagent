import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import { definePreset } from '@primevue/themes'
import Aura from '@primevue/themes/aura'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import Tooltip from 'primevue/tooltip'
import AnimateOnScroll from 'primevue/animateonscroll'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'
import './assets/styles/global.css'
import App from './App.vue'
import router from './router'
import { applyStoredTheme } from './services/theme'

const JpilotPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '{emerald.50}',
      100: '{emerald.100}',
      200: '{emerald.200}',
      300: '{emerald.300}',
      400: '{emerald.400}',
      500: '{emerald.500}',
      600: '{emerald.600}',
      700: '{emerald.700}',
      800: '{emerald.800}',
      900: '{emerald.900}',
      950: '{emerald.950}'
    }
  }
})

applyStoredTheme()

const app = createApp(App)
app.use(PrimeVue, {
  theme: {
    preset: JpilotPreset,
    options: {
      prefix: 'p',
      darkModeSelector: '.app-dark'
    }
  }
})
app.directive('tooltip', Tooltip)
app.directive('animateonscroll', AnimateOnScroll)
app.use(ConfirmationService)
app.use(ToastService)
app.use(router)
app.mount('#app')
