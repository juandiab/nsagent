<template>
  <div class="login-page flex align-items-center justify-content-center min-h-screen">
    <div class="login-panel">
      <div class="login-brand flex flex-column align-items-center mb-5">
        <NetScalerLogo />
        <h1 class="login-title m-0 mt-3">NetScaler Copilot</h1>
        <p class="login-subtitle m-0 mt-2">Sign in to manage your platform</p>
      </div>

      <form class="flex flex-column gap-4" @submit.prevent="handlePasswordLogin">
        <div class="flex flex-column gap-2">
          <label for="username" class="field-label">Username</label>
          <InputText
            id="username"
            v-model="username"
            autocomplete="username"
            class="w-full"
            :disabled="loading"
            @blur="refreshStatus"
          />
        </div>

        <div class="flex flex-column gap-2">
          <label for="password" class="field-label">Password</label>
          <Password
            id="password"
            v-model="password"
            autocomplete="current-password"
            class="w-full"
            :feedback="false"
            toggle-mask
            input-class="w-full"
            :disabled="loading"
          />
        </div>

        <Message v-if="errorMessage" severity="error" :closable="false">
          {{ errorMessage }}
        </Message>

        <Button
          type="submit"
          label="Sign in"
          icon="pi pi-sign-in"
          class="w-full"
          :loading="loading"
        />

        <template v-if="status?.hasPasskey">
          <div class="login-divider">
            <span>or</span>
          </div>
          <Button
            type="button"
            label="Sign in with passkey"
            icon="pi pi-shield"
            class="w-full"
            severity="secondary"
            outlined
            :loading="loadingPasskey"
            @click="handlePasskeyLogin"
          />
          <small class="field-hint text-center">
            Use Touch ID, Face ID, Windows Hello, or a security key.
          </small>
        </template>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import NetScalerLogo from '../components/NetScalerLogo.vue'
import api from '../services/api'
import { setAuth } from '../services/auth'
import {
  fetchPasskeyStatus,
  loginWithPasskey,
  passkeyErrorMessage
} from '../services/webauthn'

const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const loading = ref(false)
const loadingPasskey = ref(false)
const errorMessage = ref('')
const status = ref(null)

async function refreshStatus() {
  const cleaned = username.value.trim()
  if (!cleaned) {
    status.value = null
    return
  }
  try {
    status.value = await fetchPasskeyStatus(cleaned)
  } catch {
    status.value = null
  }
}

async function handlePasswordLogin() {
  errorMessage.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/auth/login', {
      username: username.value.trim().toLowerCase(),
      password: password.value
    })
    setAuth(data.accessToken, data.user)
    router.push(route.query.redirect || '/')
  } catch {
    errorMessage.value = 'Invalid username or password'
  } finally {
    loading.value = false
  }
}

async function handlePasskeyLogin() {
  errorMessage.value = ''
  loadingPasskey.value = true
  try {
    await refreshStatus()
    if (!status.value?.hasPasskey) {
      errorMessage.value = 'No passkey registered for this account yet.'
      return
    }
    await loginWithPasskey(username.value)
    router.push(route.query.redirect || '/')
  } catch (error) {
    errorMessage.value = passkeyErrorMessage(error)
  } finally {
    loadingPasskey.value = false
  }
}
</script>

<style scoped>
.login-page {
  padding: 1.5rem;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--p-primary-100) 50%, transparent), transparent 40%),
    var(--p-surface-0);
}

.login-panel {
  width: min(100%, 24rem);
  padding: 2.5rem 2rem;
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: 1rem;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.06);
}

.login-title {
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.login-subtitle {
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.field-label {
  font-size: 0.8125rem;
  font-weight: 500;
}

.field-hint {
  color: var(--p-text-muted-color);
  font-size: 0.75rem;
}

.login-divider {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--p-text-muted-color);
  font-size: 0.75rem;
}

.login-divider::before,
.login-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--p-content-border-color);
}
</style>
