<template>
  <div class="login-page flex align-items-center justify-content-center min-h-screen">
    <div class="login-panel">
      <div class="login-brand flex flex-column align-items-center mb-5">
        <NetScalerLogo />
        <h1 class="login-title m-0 mt-3">JPilot</h1>
        <p class="login-subtitle m-0 mt-2">
          {{ status?.passkeyRequired ? 'Sign in with your passkey' : 'Sign in to manage your platform' }}
        </p>
      </div>

      <form class="flex flex-column gap-4" @submit.prevent="status?.passkeyRequired ? handlePasskeyLogin() : handlePasswordLogin()">
        <div class="flex flex-column gap-2">
          <label for="username" class="field-label">Username</label>
          <InputText
            id="username"
            v-model="username"
            autocomplete="username"
            class="w-full"
            :disabled="loading || loadingPasskey"
            @blur="refreshStatus"
          />
        </div>

        <template v-if="!status?.passkeyRequired">
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
        </template>

        <Message v-if="errorMessage" severity="error" :closable="false">
          {{ errorMessage }}
        </Message>

        <div class="flex align-items-start gap-2">
          <Checkbox v-model="agreed" :binary="true" input-id="agree" />
          <label for="agree" class="agree-label">
            I have read and agree to the
            <RouterLink to="/legal/terms" target="_blank">Terms of Service</RouterLink>,
            <RouterLink to="/legal/privacy" target="_blank">Privacy Policy</RouterLink>,
            <RouterLink to="/legal/acceptable-use" target="_blank">Acceptable Use Policy</RouterLink>, and
            <RouterLink to="/legal/eula" target="_blank">EULA</RouterLink>.
          </label>
        </div>

        <Button
          v-if="status?.passkeyRequired"
          type="button"
          label="Sign in with passkey"
          icon="pi pi-shield"
          class="w-full"
          :loading="loadingPasskey"
          :disabled="!agreed"
          @click="handlePasskeyLogin"
        />

        <Button
          v-else
          type="submit"
          label="Sign in"
          icon="pi pi-sign-in"
          class="w-full"
          :loading="loading"
          :disabled="!agreed"
        />

        <template v-if="status?.passkeyRequired">
          <small class="field-hint text-center">
            Use Touch ID, Face ID, Windows Hello, or a security key.
          </small>
        </template>

        <template v-else>
          <div class="text-center">
            <RouterLink
              :to="{ path: '/account-recovery', query: username.trim() ? { username: username.trim() } : {} }"
              class="reset-link"
            >
              Lost access? Recover with email code
            </RouterLink>
          </div>
        </template>

        <template v-if="status?.passkeyRequired">
          <div class="text-center">
            <RouterLink
              :to="{ path: '/account-recovery', query: { username: username.trim().toLowerCase() } }"
              class="reset-link"
            >
              Lost passkey or device? Account recovery
            </RouterLink>
          </div>
        </template>

        <template v-else-if="status?.exists && !status?.hasPasskey">
          <div class="login-divider">
            <span>optional</span>
          </div>
          <Button
            type="button"
            label="Sign in with passkey"
            icon="pi pi-shield"
            class="w-full"
            severity="secondary"
            outlined
            :loading="loadingPasskey"
            :disabled="!agreed"
            @click="handlePasskeyLogin"
          />
          <small class="field-hint text-center">
            Available after you register a passkey in Settings.
          </small>
        </template>
      </form>
    </div>

    <footer class="login-legal">
      <RouterLink to="/legal/privacy">Privacy Policy</RouterLink>
      <span aria-hidden="true">·</span>
      <RouterLink to="/legal/terms">Terms of Service</RouterLink>
      <span aria-hidden="true">·</span>
      <RouterLink to="/legal/eula">EULA</RouterLink>
      <span aria-hidden="true">·</span>
      <RouterLink to="/legal/acceptable-use">Acceptable Use</RouterLink>
    </footer>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
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

const username = ref(route.query.username?.toString() || '')
const password = ref('')
const agreed = ref(false)
const loading = ref(false)
const loadingPasskey = ref(false)
const errorMessage = ref('')
const status = ref(null)
let statusTimer = null

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

watch(username, (value) => {
  clearTimeout(statusTimer)
  if (!value.trim()) {
    status.value = null
    return
  }
  statusTimer = setTimeout(() => {
    refreshStatus()
  }, 300)
})

onMounted(() => {
  if (username.value.trim()) {
    refreshStatus()
  }
})

onBeforeUnmount(() => {
  clearTimeout(statusTimer)
})

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
  } catch (error) {
    const detail = error.response?.data?.detail
    errorMessage.value = typeof detail === 'string' ? detail : 'Invalid username or password'
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
  position: relative;
  padding: 1.5rem;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--p-primary-100) 50%, transparent), transparent 40%),
    var(--p-surface-0);
}

.agree-label {
  font-size: 0.8125rem;
  line-height: 1.4;
  color: var(--p-text-muted-color);
}

.agree-label a {
  color: var(--p-primary-color);
  text-decoration: none;
}

.login-legal {
  position: absolute;
  bottom: 1.25rem;
  left: 0;
  right: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0 1rem;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
}

.login-legal a {
  color: var(--p-text-muted-color);
  text-decoration: none;
}

.login-legal a:hover {
  color: var(--p-primary-color);
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

.reset-link {
  color: var(--p-primary-color);
  font-size: 0.8125rem;
  text-decoration: none;
}

.reset-link:hover {
  text-decoration: underline;
}
</style>
