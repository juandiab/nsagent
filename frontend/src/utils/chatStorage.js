export function readStorageJson(storage, key) {
  if (!storage) return null
  try {
    const raw = storage.getItem(key)
    if (raw) return JSON.parse(raw)
  } catch {
    // ignore corrupt storage
  }
  return null
}

export function writeStorageJson(storage, key, value) {
  if (!storage) return false
  try {
    storage.setItem(key, JSON.stringify(value))
    return true
  } catch {
    return false
  }
}

/** One-time copy from sessionStorage → localStorage when upgrading persistence. */
export function migrateStorageJson(key, fromStorage, toStorage) {
  const existing = readStorageJson(toStorage, key)
  if (existing != null) return existing

  const legacy = readStorageJson(fromStorage, key)
  if (legacy == null) return null

  if (writeStorageJson(toStorage, key, legacy)) {
    try {
      fromStorage.removeItem(key)
    } catch {
      // ignore
    }
  }
  return legacy
}
