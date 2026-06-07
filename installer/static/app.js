"use strict";

const STEP_NAMES = ["Welcome", "Admin", "Domain", "Deploy", "TLS", "Review"];
const $ = (id) => document.getElementById(id);
const show = (el) => el.classList.remove("hidden");
const hide = (el) => el.classList.add("hidden");

const state = { step: 0, reconfigure: false, certValidated: false, result: null };

const USERNAME_RE = /^[a-zA-Z0-9._-]{2,64}$/;
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

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

function showDone(data) {
  document.querySelectorAll(".step").forEach(hide);
  $("sec_enc").textContent = data.secrets.NSAGENT_ENCRYPTION_KEY;
  $("sec_jwt").textContent = data.secrets.JWT_SECRET_KEY;
  $("doneMsg").innerHTML =
    `Your terminal is now launching JPilot at <code>${escapeHtml(data.app_url)}</code>. ` +
    `The first boot takes about a minute — use the button below once it's up, and sign ` +
    `in with <strong>${escapeHtml(collect().admin_username)}</strong>. Passkeys can be enrolled afterwards from ` +
    `<strong>Settings</strong>.`;
  $("openApp").href = data.app_url;
  const blob = new Blob(
    [`NSAGENT_ENCRYPTION_KEY=${data.secrets.NSAGENT_ENCRYPTION_KEY}\n` +
     `JWT_SECRET_KEY=${data.secrets.JWT_SECRET_KEY}\n`],
    { type: "text/plain" });
  $("downloadEnv").href = URL.createObjectURL(blob);
  state.step = STEP_NAMES.length;
  renderRail();
  show($("done"));
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
  ["certificate", "private_key", "chain"].forEach((id) =>
    $(id).addEventListener("input", () => { state.certValidated = false; hide($("certOk")); }));

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
