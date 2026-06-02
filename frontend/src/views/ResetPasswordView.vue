<template>
  <div class="login-page flex align-items-center justify-content-center min-h-screen">
    <div class="login-panel">
      <div class="login-brand flex flex-column align-items-center mb-5">
        <NetScalerLogo />
        <h1 class="login-title m-0 mt-3">Reset password</h1>
        <p class="login-subtitle m-0 mt-2 text-center">
          Enter the code sent to your email and choose a new password.
        </p>
      </div>

      <form class="flex flex-column gap-4" @submit.prevent="handleReset">
        <div class="flex flex-column gap-2">
          <label for="username" class="field-label">Username</label>
          <InputText
            id="username"
            v-model="username"
            autocomplete="username"
            class="w-full"
            :disabled="loading"
          />
        </div>

        <div class="flex flex-column gap-2">
          <label for="code" class="field-label">Reset code</label>
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
          <label for="newPassword" class="field-label">New password</label>
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
          <small class="field-hint">Minimum 8 characters.</small>
        </div>

        <Message v-if="errorMessage" severity="error" :closable="false">
          {{ errorMessage }}
        </Message>
        <Message v-if="successMessage" severity="success" :closable="false">
          {{ successMessage }}
        </Message>

        <Button
          type="submit"
          label="Update password"
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
import { confirmPasswordReset } from '../services/passwordReset'

const router = useRouter()
const route = useRoute()

const username = ref(route.query.username?.toString() || '')
const code = ref('')
const newPassword = ref('')
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

async function handleReset() {
  errorMessage.value = ''
  successMessage.value = ''
  loading.value = true
  try {
    await confirmPasswordReset({
      username: username.value.trim().toLowerCase(),
      code: code.value.trim(),
      newPassword: newPassword.value
    })
    successMessage.value = 'Password updated. You can sign in with your new password.'
    setTimeout(() => router.push('/login'), 1500)
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || error.message || 'Password reset failed'
  } finally {
    loading.value = false
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
