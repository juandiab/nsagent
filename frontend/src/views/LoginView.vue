<template>
  <div class="login-page flex align-items-center justify-content-center min-h-screen">
    <div class="login-bg" aria-hidden="true">
      <ConstellationCanvas />
      <div class="login-bg-overlay"></div>
    </div>

    <div
      class="login-panel"
      v-animateonscroll="{ enterClass: 'anim-panel-in' }"
    >
      <div v-if="serverVersion" class="login-panel-tags">
        <span class="login-meta-tag login-meta-version">{{ serverVersion }}</span>
      </div>

      <div
        class="login-brand flex flex-column align-items-center mb-5"
        v-animateonscroll="{ enterClass: 'anim-rise anim-delay-1' }"
      >
        <JPilot :size="73" />
        <h1 class="login-title m-0 mt-3">JPilot</h1>
        <span class="login-meta-tag login-meta-edition mt-2">Early Access</span>
        <p class="login-subtitle m-0 mt-2">
          {{ status?.passkeyRequired ? 'Sign in with your passkey' : 'Sign in to manage your platform' }}
        </p>
      </div>

      <form
        class="flex flex-column gap-4"
        v-animateonscroll="{ enterClass: 'anim-rise anim-delay-2' }"
        @submit.prevent="status?.passkeyRequired ? handlePasskeyLogin(false) : handlePasswordLogin()"
      >
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

        <Message
          v-if="status?.passkeyPolicy === 'disabled'"
          severity="secondary"
          :closable="false"
        >
          Passkeys are disabled on this platform. Sign in with your password.
        </Message>

        <Message
          v-else-if="status?.passkeyEnforced && !status?.hasPasskey"
          severity="warn"
          :closable="false"
        >
          Passkeys are required. Sign in with your password once, then register a passkey under Settings → Security.
        </Message>

        <Message
          v-else-if="status?.passkeyRecommended && !status?.hasPasskey"
          severity="info"
          :closable="false"
        >
          Passkeys are recommended for faster, phishing-resistant sign-in. Register one in Settings → Security after you sign in.
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
          :loading="loadingPasskey && passkeyMode === 'local'"
          :disabled="!agreed || loadingPasskey"
          @click="handlePasskeyLogin(false)"
        />

        <div
          v-if="status?.passkeyRequired"
          class="cross-device-panel"
          v-animateonscroll="{ enterClass: 'anim-rise anim-delay-3' }"
        >
          <div class="cross-device-panel-header">
            <i class="pi pi-mobile" aria-hidden="true"></i>
            <span>Sign in from your phone</span>
          </div>
          <p class="cross-device-copy">
            Passkey saved on another device? We will open a QR code so you can scan it with a phone
            that has this passkey (for example via iCloud Keychain or Google Password Manager).
          </p>
          <div class="cross-device-qr-area" :class="{ active: crossDeviceActive }">
            <div class="qr-placeholder" aria-hidden="true">
              <span v-for="cell in qrPattern" :key="cell" :class="{ filled: cell }"></span>
            </div>
            <p v-if="crossDeviceActive" class="cross-device-status">
              Scan the QR code in your browser&rsquo;s passkey dialog with your phone camera.
            </p>
            <p v-else class="cross-device-status muted">
              The scannable QR code opens when you start phone sign-in below.
            </p>
          </div>
          <Button
            type="button"
            label="Show QR code"
            icon="pi pi-qrcode"
            class="w-full"
            severity="secondary"
            outlined
            :loading="loadingPasskey && passkeyMode === 'cross-device'"
            :disabled="!agreed || loadingPasskey"
            @click="handlePasskeyLogin(true)"
          />
        </div>

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
            On this computer, use Touch ID, Face ID, or Windows Hello if your passkey is synced here.
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

        <template v-else-if="status?.exists && !status?.hasPasskey && status?.passkeyPolicy !== 'disabled'">
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
            @click="handlePasskeyLogin(false)"
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
import ConstellationCanvas from '../components/ConstellationCanvas.vue'
import JPilot from '../components/JPilot.vue'
import api from '../services/api'
import { setAuth } from '../services/auth'
import { getSystemVersion } from '../services/system'
import {
  fetchPasskeyStatus,
  loginWithPasskey,
  passkeyErrorMessage
} from '../services/webauthn'
import { WebAuthnAbortService } from '@simplewebauthn/browser'

const router = useRouter()
const route = useRoute()

const username = ref(route.query.username?.toString() || '')
const password = ref('')
const agreed = ref(false)
const loading = ref(false)
const loadingPasskey = ref(false)
const passkeyMode = ref('local')
const crossDeviceActive = ref(false)
const crossDeviceAutoStarted = ref(false)
const errorMessage = ref('')
const status = ref(null)
const serverVersion = ref('')
let statusTimer = null

const qrPattern = [
  true, true, true, false, true, true, true,
  true, false, true, false, true, false, true,
  true, true, true, false, false, true, true,
  false, true, false, true, true, false, true,
  true, false, true, true, true, false, true,
  true, true, true, false, true, false, true,
  false, false, true, false, true, true, true
]

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
  crossDeviceAutoStarted.value = false
  crossDeviceActive.value = false
  if (!value.trim()) {
    status.value = null
    return
  }
  statusTimer = setTimeout(() => {
    refreshStatus()
  }, 300)
})

watch([agreed, () => status.value?.passkeyRequired], ([isAgreed, passkeyRequired]) => {
  if (isAgreed && passkeyRequired && !crossDeviceAutoStarted.value) {
    crossDeviceAutoStarted.value = true
    handlePasskeyLogin(true)
  }
})

onMounted(async () => {
  if (username.value.trim()) {
    refreshStatus()
  }
  try {
    const info = await getSystemVersion()
    serverVersion.value = info.display_version
  } catch {
    serverVersion.value = ''
  }
})

onBeforeUnmount(() => {
  clearTimeout(statusTimer)
  WebAuthnAbortService.cancelCeremony()
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

async function handlePasskeyLogin(preferCrossDevice = false) {
  errorMessage.value = ''
  passkeyMode.value = preferCrossDevice ? 'cross-device' : 'local'
  crossDeviceActive.value = preferCrossDevice
  loadingPasskey.value = true
  try {
    await refreshStatus()
    if (!status.value?.hasPasskey) {
      errorMessage.value = 'No passkey registered for this account yet.'
      crossDeviceActive.value = false
      return
    }
    await loginWithPasskey(username.value, { preferCrossDevice })
    router.push(route.query.redirect || '/')
  } catch (error) {
    errorMessage.value = passkeyErrorMessage(error)
    crossDeviceActive.value = false
    if (preferCrossDevice) {
      crossDeviceAutoStarted.value = false
    }
  } finally {
    loadingPasskey.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  padding: 1.5rem;
  background: var(--p-surface-ground);
}

.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.login-bg-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 60% 50%, rgba(0, 123, 167, 0.1) 0%, transparent 65%),
    linear-gradient(180deg, transparent 70%, var(--p-surface-ground) 100%);
  pointer-events: none;
}

:global(.app-dark) .login-bg-overlay {
  background:
    radial-gradient(ellipse at 60% 50%, rgba(0, 123, 167, 0.12) 0%, transparent 65%),
    linear-gradient(180deg, transparent 70%, var(--p-surface-ground) 100%);
}

/* Entrance animations (PrimeVue AnimateOnScroll enterClass targets) */
.anim-panel-in {
  animation: panel-in 700ms cubic-bezier(0.22, 1, 0.36, 1) backwards;
}

.anim-rise {
  animation: rise-in 600ms cubic-bezier(0.22, 1, 0.36, 1) backwards;
}

.anim-delay-1 { animation-delay: 120ms; }
.anim-delay-2 { animation-delay: 240ms; }
.anim-delay-3 { animation-delay: 360ms; }

@keyframes panel-in {
  from {
    opacity: 0;
    transform: translateY(24px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes rise-in {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .anim-panel-in,
  .anim-rise {
    animation: none;
  }
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
  z-index: 1;
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
  position: relative;
  z-index: 1;
  width: min(100%, 24rem);
  padding: 2.5rem 2rem;
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: 1rem;
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.08),
    0 0 0 1px color-mix(in srgb, var(--p-primary-color) 12%, transparent),
    0 0 32px color-mix(in srgb, var(--p-primary-color) 14%, transparent);
}

:global(.app-dark) .login-panel {
  box-shadow:
    0 18px 50px rgba(0, 0, 0, 0.5),
    0 0 0 1px color-mix(in srgb, var(--p-primary-color) 22%, transparent),
    0 0 48px color-mix(in srgb, var(--p-primary-color) 28%, transparent);
}

.login-title {
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.login-panel-tags {
  position: absolute;
  top: 0.875rem;
  right: 0.875rem;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.375rem;
  flex-wrap: wrap;
  max-width: calc(100% - 1.75rem);
}

.login-meta-tag {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.65rem;
  border-radius: 100px;
  letter-spacing: 0.04em;
  background: transparent;
}

.login-meta-edition {
  border: 1px solid color-mix(in srgb, var(--p-primary-color) 45%, transparent);
  color: var(--p-primary-color);
}

.login-meta-version {
  border: 1px solid color-mix(in srgb, var(--p-text-muted-color) 40%, transparent);
  color: var(--p-text-muted-color);
  font-weight: 600;
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

.cross-device-panel {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  padding: 1rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: 0.75rem;
  background: color-mix(in srgb, var(--p-primary-color) 5%, var(--p-content-background));
}

.cross-device-panel-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.cross-device-panel-header .pi {
  color: var(--p-primary-color);
}

.cross-device-copy {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.45;
  color: var(--p-text-muted-color);
}

.cross-device-qr-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem;
  border-radius: 0.625rem;
  border: 1px dashed var(--p-content-border-color);
  background: var(--p-content-background);
}

.cross-device-qr-area.active {
  border-color: color-mix(in srgb, var(--p-primary-color) 45%, var(--p-content-border-color));
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--p-primary-color) 12%, transparent);
}

.qr-placeholder {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.18rem;
  width: 5.5rem;
  aspect-ratio: 1;
  padding: 0.35rem;
  border-radius: 0.35rem;
  background: #fff;
}

.qr-placeholder span {
  border-radius: 0.1rem;
  background: color-mix(in srgb, var(--p-text-color) 8%, #fff);
}

.qr-placeholder span.filled {
  background: var(--p-text-color);
}

.cross-device-qr-area.active .qr-placeholder {
  animation: qr-pulse 1.6s ease-in-out infinite;
}

.cross-device-status {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.45;
  text-align: center;
  color: var(--p-text-color);
}

.cross-device-status.muted {
  color: var(--p-text-muted-color);
}

@keyframes qr-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.82; transform: scale(0.98); }
}
</style>
