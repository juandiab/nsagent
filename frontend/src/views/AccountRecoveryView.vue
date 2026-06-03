<template>
  <div class="login-page flex align-items-center justify-content-center min-h-screen">
    <div class="login-panel">
      <div class="login-brand flex flex-column align-items-center mb-5">
        <NetScalerLogo />
        <h1 class="login-title m-0 mt-3">Account recovery</h1>
        <p class="login-subtitle m-0 mt-2 text-center">
          Recover access with a code sent to your email. Existing passkeys are removed for security.
        </p>
      </div>

      <form v-if="!recoveryToken" class="flex flex-column gap-4" @submit.prevent="handleConfirm">
        <div class="flex flex-column gap-2">
          <label for="username" class="field-label">Username</label>
          <InputText
            id="username"
            v-model="username"
            autocomplete="username"
            class="w-full"
            :disabled="loading || sendingCode"
          />
        </div>

        <Button
          type="button"
          label="Send recovery code"
          icon="pi pi-envelope"
          class="w-full"
          severity="secondary"
          outlined
          :loading="sendingCode"
          :disabled="!username.trim() || loading"
          @click="handleSendCode"
        />

        <div class="flex flex-column gap-2">
          <label for="code" class="field-label">Recovery code</label>
          <InputText
            id="code"
            v-model="code"
            autocomplete="one-time-code"
            class="w-full"
            inputmode="numeric"
            maxlength="6"
            :disabled="loading"
          />
        </div>

        <div class="flex flex-column gap-2">
          <label for="newPassword" class="field-label">New password (optional)</label>
          <Password
            id="newPassword"
            v-model="newPassword"
            autocomplete="new-password"
            class="w-full"
            :feedback="false"
            toggle-mask
            input-class="w-full"
            :disabled="loading"
          />
          <small class="field-hint">
            Leave empty to register a new passkey only (for passkey-only accounts).
            Minimum 8 characters when set.
          </small>
        </div>

        <Message v-if="errorMessage" severity="error" :closable="false">
          {{ errorMessage }}
        </Message>
        <Message v-if="infoMessage" severity="info" :closable="false">
          {{ infoMessage }}
        </Message>

        <Button
          type="submit"
          label="Confirm recovery"
          icon="pi pi-lock"
          class="w-full"
          :loading="loading"
        />

        <Button
          type="button"
          label="Back to sign in"
          icon="pi pi-arrow-left"
          class="w-full"
          text
          @click="router.push('/login')"
        />
      </form>

      <div v-else class="flex flex-column gap-4">
        <Message severity="success" :closable="false">
          {{ successMessage }}
        </Message>
        <Button
          type="button"
          label="Register new passkey"
          icon="pi pi-shield"
          class="w-full"
          :loading="registeringPasskey"
          @click="handleRegisterPasskey"
        />
        <small class="field-hint text-center">
          Use Touch ID, Face ID, Windows Hello, or a security key.
        </small>
        <Message v-if="errorMessage" severity="error" :closable="false">
          {{ errorMessage }}
        </Message>
        <Button
          type="button"
          label="Back to sign in"
          icon="pi pi-arrow-left"
          class="w-full"
          text
          @click="router.push('/login')"
        />
      </div>
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
import { confirmAccountRecovery, requestAccountRecovery } from '../services/passwordReset'
import { passkeyErrorMessage, registerPasskey } from '../services/webauthn'

const router = useRouter()
const route = useRoute()

const username = ref(route.query.username?.toString() || '')
const code = ref('')
const newPassword = ref('')
const loading = ref(false)
const sendingCode = ref(false)
const registeringPasskey = ref(false)
const errorMessage = ref('')
const infoMessage = ref('')
const successMessage = ref('')
const recoveryToken = ref('')

async function handleSendCode() {
  errorMessage.value = ''
  infoMessage.value = ''
  sendingCode.value = true
  try {
    const { data } = await requestAccountRecovery(username.value)
    infoMessage.value = data.message
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || error.message || 'Could not send recovery code'
  } finally {
    sendingCode.value = false
  }
}

async function handleConfirm() {
  errorMessage.value = ''
  infoMessage.value = ''
  loading.value = true
  try {
    const { data } = await confirmAccountRecovery({
      username: username.value,
      code: code.value,
      newPassword: newPassword.value
    })
    successMessage.value = data.message
    if (data.recoveryToken) {
      recoveryToken.value = data.recoveryToken
    } else {
      setTimeout(() => router.push({ path: '/login', query: { username: username.value.trim().toLowerCase() } }), 1500)
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || error.message || 'Account recovery failed'
  } finally {
    loading.value = false
  }
}

async function handleRegisterPasskey() {
  errorMessage.value = ''
  registeringPasskey.value = true
  try {
    await registerPasskey(username.value, 'Recovery passkey', recoveryToken.value)
    router.push('/')
  } catch (error) {
    errorMessage.value = passkeyErrorMessage(error)
  } finally {
    registeringPasskey.value = false
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
</style>
