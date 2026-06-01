<template>
  <div class="page">
    <PageHeader
      title="Users"
      subtitle="Manage platform accounts and passkeys"
      searchable
      v-model:search="searchQuery"
    >
      <template #actions>
        <Button label="Add user" icon="pi pi-user-plus" size="small" @click="openCreateDialog" />
      </template>
    </PageHeader>

    <div class="content-panel">
      <DataTable
        :value="filteredUsers"
        :loading="loading"
        striped-rows
        paginator
        :rows="10"
        empty-message="No users found."
      >
        <Column field="username" header="Username" sortable />
        <Column field="displayName" header="Display name" sortable />
        <Column field="role" header="Role" sortable>
          <template #body="{ data }">
            <Tag :value="data.role" :severity="data.role === 'admin' ? 'warn' : 'secondary'" />
          </template>
        </Column>
        <Column header="Passkeys">
          <template #body="{ data }">
            <Tag
              :value="data.passkeyCount ? `${data.passkeyCount} registered` : 'Not set up'"
              :severity="data.passkeyCount ? 'success' : 'danger'"
            />
          </template>
        </Column>
        <Column header="Actions" style="min-width: 10rem">
          <template #body="{ data }">
            <div class="flex gap-1">
              <Button
                v-tooltip.top="'View passkeys'"
                icon="pi pi-key"
                text
                rounded
                size="small"
                @click="openPasskeysDialog(data)"
              />
              <Button
                icon="pi pi-pencil"
                text
                rounded
                size="small"
                @click="openEditDialog(data)"
              />
              <Button
                v-tooltip.top="'Delete'"
                icon="pi pi-trash"
                text
                rounded
                size="small"
                severity="danger"
                @click="confirmDelete(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog
      v-model:visible="dialogVisible"
      :header="isEditing ? 'Edit user' : 'Add user'"
      modal
      :style="{ width: 'min(28rem, 92vw)' }"
      :draggable="false"
    >
      <div class="flex flex-column gap-3">
        <div v-if="!isEditing" class="flex flex-column gap-2">
          <label for="username" class="field-label">Username</label>
          <InputText id="username" v-model="form.username" class="w-full" autocomplete="off" />
          <small class="field-hint">Letters, numbers, dots, dashes, and underscores only.</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="displayName" class="field-label">Display name</label>
          <InputText id="displayName" v-model="form.displayName" class="w-full" />
        </div>
        <div class="flex flex-column gap-2">
          <label for="role" class="field-label">Role</label>
          <Select id="role" v-model="form.role" :options="roles" class="w-full" />
        </div>
        <div v-if="!isEditing" class="flex flex-column gap-2">
          <label for="password" class="field-label">Initial password</label>
          <Password
            id="password"
            v-model="form.password"
            class="w-full"
            :feedback="false"
            toggle-mask
            input-class="w-full"
            autocomplete="new-password"
          />
          <small class="field-hint">Minimum 8 characters. The user can change it later and add a passkey in Settings.</small>
        </div>
        <Message v-if="!isEditing" severity="info" :closable="false">
          Users sign in with this password first, then register a passkey under Settings → Security.
        </Message>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="dialogVisible = false" />
        <Button :label="isEditing ? 'Save' : 'Create'" :loading="saving" @click="saveUser" />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="passkeysVisible"
      :header="passkeysUser ? `Passkeys — ${passkeysUser.username}` : 'Passkeys'"
      modal
      :style="{ width: 'min(32rem, 92vw)' }"
      :draggable="false"
    >
      <div v-if="passkeysLoading" class="py-4 text-center">Loading…</div>
      <div v-else-if="!passkeys.length" class="py-2">
        <Message severity="warn" :closable="false">
          No passkey registered yet. The user can add one after signing in under Settings → Security.
        </Message>
      </div>
      <DataTable v-else :value="passkeys" size="small">
        <Column field="label" header="Label" />
        <Column field="createdAt" header="Added">
          <template #body="{ data }">
            {{ formatDate(data.createdAt) }}
          </template>
        </Column>
        <Column field="lastUsedAt" header="Last used">
          <template #body="{ data }">
            {{ data.lastUsedAt ? formatDate(data.lastUsedAt) : '—' }}
          </template>
        </Column>
        <Column header="">
          <template #body="{ data }">
            <Button
              icon="pi pi-trash"
              text
              rounded
              size="small"
              severity="danger"
              @click="confirmDeletePasskey(data)"
            />
          </template>
        </Column>
      </DataTable>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import PageHeader from '../components/PageHeader.vue'
import {
  createUser,
  deletePasskey,
  deleteUser,
  getUser,
  listUsers,
  updateUser
} from '../services/users'

const confirm = useConfirm()
const toast = useToast()

const users = ref([])
const loading = ref(false)
const saving = ref(false)
const searchQuery = ref('')
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const passkeysVisible = ref(false)
const passkeysLoading = ref(false)
const passkeysUser = ref(null)
const passkeys = ref([])

const roles = ['user', 'admin']

const form = ref({
  username: '',
  displayName: '',
  password: '',
  role: 'user'
})

const filteredUsers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return users.value
  return users.value.filter((user) =>
    [user.username, user.displayName, user.role].some((value) =>
      String(value || '').toLowerCase().includes(q)
    )
  )
})

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString()
}

async function loadUsers() {
  loading.value = true
  try {
    const { data } = await listUsers()
    users.value = data
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Failed to load users',
      detail: error.response?.data?.detail || error.message,
      life: 5000
    })
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.value = { username: '', displayName: '', password: '', role: 'user' }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(user) {
  isEditing.value = true
  editingId.value = user.id
  form.value = {
    username: user.username,
    displayName: user.displayName,
    role: user.role
  }
  dialogVisible.value = true
}

async function saveUser() {
  saving.value = true
  try {
    if (isEditing.value) {
      await updateUser(editingId.value, {
        displayName: form.value.displayName,
        role: form.value.role
      })
      toast.add({ severity: 'success', summary: 'User updated', life: 3000 })
    } else {
      await createUser({
        username: form.value.username.trim().toLowerCase(),
        displayName: form.value.displayName.trim(),
        password: form.value.password,
        role: form.value.role
      })
      toast.add({ severity: 'success', summary: 'User created', life: 3000 })
    }
    dialogVisible.value = false
    await loadUsers()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Save failed',
      detail: error.response?.data?.detail || error.message,
      life: 5000
    })
  } finally {
    saving.value = false
  }
}

function confirmDelete(user) {
  confirm.require({
    message: `Delete user "${user.username}"?`,
    header: 'Delete user',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await deleteUser(user.id)
        toast.add({ severity: 'success', summary: 'User deleted', life: 3000 })
        await loadUsers()
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Delete failed',
          detail: error.response?.data?.detail || error.message,
          life: 5000
        })
      }
    }
  })
}

async function openPasskeysDialog(user) {
  passkeysUser.value = user
  passkeysVisible.value = true
  passkeysLoading.value = true
  try {
    const { data } = await getUser(user.id)
    passkeys.value = data.passkeys || []
  } catch (error) {
    passkeys.value = []
    toast.add({
      severity: 'error',
      summary: 'Failed to load passkeys',
      detail: error.response?.data?.detail || error.message,
      life: 5000
    })
  } finally {
    passkeysLoading.value = false
  }
}

function confirmDeletePasskey(passkey) {
  confirm.require({
    message: `Remove passkey "${passkey.label}"?`,
    header: 'Remove passkey',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await deletePasskey(passkeysUser.value.id, passkey.id)
        toast.add({ severity: 'success', summary: 'Passkey removed', life: 3000 })
        await openPasskeysDialog(passkeysUser.value)
        await loadUsers()
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: 'Remove failed',
          detail: error.response?.data?.detail || error.message,
          life: 5000
        })
      }
    }
  })
}

onMounted(loadUsers)
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.content-panel {
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: 1rem;
  padding: 1rem;
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
