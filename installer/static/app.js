"use strict";

const STEP_NAMES = ["Welcome", "Admin", "Domain", "Deploy", "TLS", "Review"];
const $ = (id) => document.getElementById(id);
const show = (el) => el.classList.remove("hidden");
const hide = (el) => el.classList.add("hidden");

const state = { step: 0, reconfigure: false, certValidated: false, result: null };

const USERNAME_RE = /^[a-zA-Z0-9._-]{2,64}$/;
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PEM_CERT_RE = /-----BEGIN CERTIFICATE-----/;
const PEM_KEY_RE = /-----BEGIN (?:RSA |EC )?PRIVATE KEY-----/;
const PEM_CERT_BLOCK_RE = /-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----/g;

// ---------------------------------------------------------------- step rail
function renderRail() {
  const ol = $("steps");
  ol.innerHTML = "";
  STEP_NAMES.forEach((name, i) => {
    const li = document.createElement("li");
    if (i === state.step) li.className = "active";
    else if (i < state.step) li.className = "done";
    li.innerHTML = `<span class="dot">${i < state.step ? "✓" : i + 1}</span>${name}`;
    ol.appendChild(li);
  });
}

function gotoStep(n) {
  state.step = n;
  document.querySelectorAll(".step").forEach((s) => {
    s.classList.toggle("hidden", Number(s.dataset.step) !== n);
  });
  renderRail();
  window.scrollTo(0, 0);
}

// ---------------------------------------------------------------- validation
function validateStep(n) {
  if (n === 1) {
    const username = $("admin_username").value.trim() || "admin";
    const email = $("admin_email").value.trim();
    const pw = $("admin_password").value;
    const pw2 = $("admin_password2").value;
    const err = $("adminErr");
    if (!USERNAME_RE.test(username)) {
      return fail(err, "Username must be 2–64 characters and use only letters, numbers, dots, underscores, or hyphens.");
    }
    if (!email) return fail(err, "Email is required for password recovery.");
    if (!EMAIL_RE.test(email)) return fail(err, "Enter a valid email address.");
    if (pw.length < 8) return fail(err, "Password must be at least 8 characters.");
    if (pw !== pw2) return fail(err, "Passwords do not match.");
    hide(err);
  }
  if (n === 2) {
    const domain = $("domain").value.trim();
    const err = $("domainErr");
    const re = /^(localhost|(\d{1,3}\.){3}\d{1,3}|([a-zA-Z0-9](-?[a-zA-Z0-9])*\.)+[a-zA-Z]{2,})$/;
    if (!re.test(domain)) return fail(err, "Enter a valid hostname (e.g. jpilot.example.com), IP, or 'localhost'.");
    hide(err);
  }
  if (n === 4) {
    const mode = document.querySelector('input[name="cert_mode"]:checked').value;
    if (mode === "custom" && !state.certValidated) {
      return fail($("certErr"), "Validate your certificate before continuing.");
    }
  }
  return true;
}

function fail(el, msg) {
  el.textContent = msg;
  show(el);
  return false;
}

// ---------------------------------------------------------------- collect
function collect() {
  const mode = document.querySelector('input[name="cert_mode"]:checked').value;
  const deployMode = document.querySelector('input[name="deploy_mode"]:checked').value;
  return {
    reconfigure: state.reconfigure,
    deploy_mode: deployMode,
    admin_username: $("admin_username").value.trim() || "admin",
    admin_password: $("admin_password").value,
    admin_email: $("admin_email").value.trim(),
    domain: $("domain").value.trim() || "localhost",
    app_name: $("app_name").value.trim() || "JPilot",
    cert_mode: mode,
    certificate: mode === "custom" ? $("certificate").value : "",
    chain: mode === "custom" ? $("chain").value : "",
    private_key: mode === "custom" ? $("private_key").value : "",
    accepted_terms: $("acceptTerms").checked,
  };
}

function syncInstallButton() {
  $("installBtn").disabled = !$("acceptTerms").checked;
}

function renderReview() {
  const d = collect();
  const rows = [
    ["Deploy mode", d.deploy_mode === "dev" ? "Development (hot reload)" : "Production (compiled)"],
    ["Admin username", d.admin_username],
    ["Admin email", d.admin_email],
    ["Domain", `https://${d.domain}`],
    ["Display name", d.app_name],
    ["TLS certificate", d.cert_mode === "custom" ? "Custom (provided)" : "Self-signed (generated)"],
    ["Encryption key", "Generated on install"],
    ["JWT secret", "Generated on install"],
  ];
  $("reviewList").innerHTML = rows
    .map(([k, v]) => `<dt>${k}</dt><dd>${escapeHtml(v)}</dd>`)
    .join("");
  $("acceptTerms").checked = false;
  hide($("termsErr"));
  syncInstallButton();
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// ---------------------------------------------------------------- PEM drop / browse
function invalidateCert() {
  state.certValidated = false;
  hide($("certOk"));
}

function showDropMessage(msg, tone = "info") {
  const el = $("certDropMsg");
  if (!msg) {
    hide(el);
    return;
  }
  el.textContent = msg;
  el.classList.toggle("field-error", tone === "error");
  el.classList.toggle("field-info", tone !== "error");
  show(el);
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error(`Could not read ${file.name}`));
    reader.readAsText(file);
  });
}

function splitCertificateBlocks(text) {
  return text.match(PEM_CERT_BLOCK_RE) || [];
}

function classifyPem(text) {
  const trimmed = text.trim();
  const hasCert = PEM_CERT_RE.test(trimmed);
  const hasKey = PEM_KEY_RE.test(trimmed);
  if (hasKey && !hasCert) return "private_key";
  if (hasCert && !hasKey) return "certificate";
  if (hasCert && hasKey) return "mixed";
  return "unknown";
}

function appendChainText(text) {
  const blocks = splitCertificateBlocks(text);
  const next = (blocks.length ? blocks : [text.trim()]).join("\n");
  const field = $("chain");
  field.value = field.value.trim() ? `${field.value.trim()}\n${next}` : next;
  invalidateCert();
}

function setPemField(field, text) {
  if (field === "certificate") $("certificate").value = text.trim();
  else if (field === "private_key") $("private_key").value = text.trim();
  else {
    appendChainText(text);
    return;
  }
  invalidateCert();
}

function ingestPemText(text, preferredField, fileName = "") {
  const kind = classifyPem(text);

  if (kind === "unknown") {
    showDropMessage(
      fileName
        ? `${fileName} does not look like a PEM certificate or private key.`
        : "Dropped content does not look like a PEM certificate or private key.",
      "error"
    );
    return false;
  }

  if (preferredField === "chain") {
    if (kind === "private_key") {
      setPemField("private_key", text);
      showDropMessage(
        fileName
          ? `${fileName} looks like a private key — placed in the private key field.`
          : "Placed the private key in the matching field."
      );
      return true;
    }
    appendChainText(text);
    showDropMessage("");
    return true;
  }

  const target =
    kind === "certificate" || kind === "private_key" ? kind : preferredField;

  if (target !== preferredField && kind !== "mixed") {
    showDropMessage(
      fileName
        ? `${fileName} looks like a ${kind === "private_key" ? "private key" : "certificate"} — placed in the matching field.`
        : `Placed the ${kind === "private_key" ? "private key" : "certificate"} in the matching field.`
    );
  } else {
    showDropMessage("");
  }

  if (target === "certificate") {
    const blocks = splitCertificateBlocks(text);
    if (blocks.length > 1) {
      setPemField("certificate", blocks[0]);
      appendChainText(blocks.slice(1).join("\n"));
      const routed = target !== preferredField && kind !== "mixed";
      if (!routed) {
        showDropMessage("Multiple certificates detected — leaf cert and intermediates were split automatically.");
      }
      return true;
    }
  }

  setPemField(target, text);
  return true;
}

async function loadPemFiles(files, preferredField) {
  const list = [...files].filter((file) => file && file.size > 0);
  if (!list.length) return;

  showDropMessage("");
  let loaded = 0;
  for (const file of list) {
    try {
      const text = await readFileAsText(file);
      if (ingestPemText(text, preferredField, file.name)) loaded += 1;
    } catch (error) {
      showDropMessage(error.message || `Could not read ${file.name}.`, "error");
    }
  }

  if (loaded > 1 && $("certDropMsg").classList.contains("hidden")) {
    showDropMessage(`Loaded ${loaded} files.`);
  }
}

function wirePemDropZones() {
  let dragField = null;

  document.querySelectorAll(".pem-drop-zone").forEach((zone) => {
    const field = zone.dataset.pemField;

    zone.addEventListener("dragenter", (event) => {
      event.preventDefault();
      dragField = field;
      zone.classList.add("is-dragover");
    });
    zone.addEventListener("dragover", (event) => {
      event.preventDefault();
      dragField = field;
      zone.classList.add("is-dragover");
    });
    zone.addEventListener("dragleave", (event) => {
      if (zone.contains(event.relatedTarget)) return;
      if (dragField === field) dragField = null;
      zone.classList.remove("is-dragover");
    });
    zone.addEventListener("drop", async (event) => {
      event.preventDefault();
      zone.classList.remove("is-dragover");
      dragField = null;
      await loadPemFiles(event.dataTransfer?.files || [], field);
    });
  });

  document.querySelectorAll(".pem-browse").forEach((btn) => {
    btn.addEventListener("click", () => {
      const field = btn.dataset.pemField;
      const input = document.querySelector(`.pem-file-input[data-pem-field="${field}"]`);
      input?.click();
    });
  });

  document.querySelectorAll(".pem-file-input").forEach((input) => {
    input.addEventListener("change", async (event) => {
      const field = input.dataset.pemField;
      await loadPemFiles(event.target.files || [], field);
      event.target.value = "";
    });
  });
}

// ---------------------------------------------------------------- API calls
async function validateCert() {
  const err = $("certErr"), ok = $("certOk");
  hide(err); hide(ok);
  const btn = $("validateCert");
  btn.disabled = true; btn.textContent = "Validating…";
  try {
    const res = await fetch("/api/validate-cert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        certificate: $("certificate").value,
        private_key: $("private_key").value,
        chain: $("chain").value,
      }),
    });
    const data = await res.json();
    if (data.ok) {
      state.certValidated = true;
      ok.textContent = `✓ Valid for ${data.common_name || "(no CN)"} — expires ${data.expires} (${data.expires_in_days} days).`;
      show(ok);
    } else {
      state.certValidated = false;
      fail(err, data.error || "Validation failed.");
    }
  } catch (e) {
    fail(err, "Could not reach the installer service.");
  } finally {
    btn.disabled = false; btn.textContent = "Validate certificate";
  }
}

async function install() {
  const btn = $("installBtn"), err = $("installErr"), termsErr = $("termsErr");
  hide(err);
  hide(termsErr);
  if (!$("acceptTerms").checked) {
    fail(termsErr, "You must accept the Terms of Service, Privacy Policy, Acceptable Use Policy, and EULA.");
    syncInstallButton();
    return;
  }
  btn.disabled = true; btn.textContent = "Installing…";
  try {
    const res = await fetch("/api/install", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collect()),
    });
    const data = await res.json();
    if (!res.ok) {
      fail(err, data.detail || "Installation failed.");
      btn.textContent = "Install JPilot";
      syncInstallButton();
      return;
    }
    state.result = data;
    showDone(data);
  } catch (e) {
    fail(err, "Could not reach the installer service.");
    btn.textContent = "Install JPilot";
    syncInstallButton();
  }
}

const LAUNCH_POLL_MS = 2000;
const LAUNCH_MAX_POLLS = 300;

function formatElapsed(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${String(secs).padStart(2, "0")} elapsed`;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function showLaunchReady(appUrl, username) {
  $("doneTitle").textContent = "JPilot is ready!";
  $("launchPanel").classList.add("hidden");
  show($("readyPanel"));
  $("launchFill").style.width = "100%";
  $("doneMsg").innerHTML =
    `Sign in as <strong>${escapeHtml(username)}</strong>. Passkeys can be enrolled later from ` +
    `<strong>Settings</strong>. Need help? Visit ` +
    `<a href="https://www.nexxus-tech.com" target="_blank" rel="noopener noreferrer">nexxus-tech.com</a>.`;
  const openBtn = $("openApp");
  openBtn.href = appUrl;
  show(openBtn);
  setTimeout(() => {
    window.location.href = appUrl;
  }, 2500);
}

async function pollLaunchProgress(appUrl, username) {
  const fill = $("launchFill");
  const status = $("launchStatus");
  const elapsedEl = $("launchElapsed");
  fill.style.width = "8%";
  status.textContent = "Building JPilot — please keep this tab open.";

  for (let n = 0; n < LAUNCH_MAX_POLLS; n++) {
    try {
      const res = await fetch("/api/launch-status");
      const data = await res.json();
      if (data.elapsed_seconds != null) {
        elapsedEl.textContent = formatElapsed(data.elapsed_seconds);
      }
      if (data.message) status.textContent = data.message;
      if (data.ready && data.app_url) {
        showLaunchReady(data.app_url, username);
        return;
      }
    } catch (e) {
      status.textContent = "Still starting JPilot…";
    }
    const pct = Math.min(92, 8 + (n / LAUNCH_MAX_POLLS) * 84);
    fill.style.width = `${pct}%`;
    await sleep(LAUNCH_POLL_MS);
  }

  $("doneTitle").textContent = "Still starting…";
  status.textContent =
    "This is taking longer than usual. Use the button below to open JPilot when you're ready.";
  $("openApp").href = appUrl;
  show($("openApp"));
}

function showDone(data) {
  document.querySelectorAll(".step").forEach(hide);
  hide($("readyPanel"));
  show($("launchPanel"));
  $("doneTitle").textContent = "Setting up JPilot";
  $("launchFill").style.width = "4%";
  $("launchStatus").textContent = "Saving your configuration…";
  $("launchElapsed").textContent = "";
  hide($("openApp"));

  $("sec_enc").textContent = data.secrets.NSAGENT_ENCRYPTION_KEY;
  $("sec_jwt").textContent = data.secrets.JWT_SECRET_KEY;
  $("doneMsg").textContent = "";
  const blob = new Blob(
    [`NSAGENT_ENCRYPTION_KEY=${data.secrets.NSAGENT_ENCRYPTION_KEY}\n` +
     `JWT_SECRET_KEY=${data.secrets.JWT_SECRET_KEY}\n`],
    { type: "text/plain" });
  $("downloadEnv").href = URL.createObjectURL(blob);
  state.step = STEP_NAMES.length;
  renderRail();
  show($("done"));
  pollLaunchProgress(data.app_url, collect().admin_username);
}

// ---------------------------------------------------------------- wiring
function wire() {
  document.querySelectorAll("[data-next]").forEach((b) =>
    b.addEventListener("click", () => {
      if (!validateStep(state.step)) return;
      if (state.step === 4) renderReview();
      gotoStep(state.step + 1);
    }));
  document.querySelectorAll("[data-back]").forEach((b) =>
    b.addEventListener("click", () => gotoStep(state.step - 1)));

  $("domain").addEventListener("input", (e) => {
    $("domainPreview").textContent = `https://${e.target.value.trim() || "localhost"}`;
  });

  document.querySelectorAll('input[name="cert_mode"]').forEach((r) =>
    r.addEventListener("change", () => {
      const custom = document.querySelector('input[name="cert_mode"]:checked').value === "custom";
      $("customCert").classList.toggle("hidden", !custom);
      state.certValidated = !custom;
    }));
  $("validateCert").addEventListener("click", validateCert);
  wirePemDropZones();
  ["certificate", "private_key", "chain"].forEach((id) =>
    $(id).addEventListener("input", () => {
      invalidateCert();
      hide($("certDropMsg"));
    }));

  $("acceptTerms").addEventListener("change", () => {
    hide($("termsErr"));
    syncInstallButton();
  });
  $("installBtn").addEventListener("click", install);
  $("guardContinue").addEventListener("click", () => {
    state.reconfigure = true;
    hide($("guard"));
    gotoStep(0);
  });

  document.querySelectorAll("[data-copy]").forEach((b) =>
    b.addEventListener("click", () => {
      navigator.clipboard.writeText($(b.dataset.copy).textContent);
      b.textContent = "Copied";
      setTimeout(() => (b.textContent = "Copy"), 1500);
    }));
}

async function boot() {
  wire();
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    if (data.already_installed) {
      document.querySelectorAll(".step").forEach(hide);
      show($("guard"));
      renderRail();
      return;
    }
  } catch (e) { /* show wizard anyway */ }
  gotoStep(0);
}

boot();
