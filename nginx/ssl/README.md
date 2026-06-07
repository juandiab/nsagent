# SSL Certificates Directory

This directory should contain your SSL/TLS certificates for HTTPS support.

## Required Files

Nginx requires the following files:

- `cert.crt` - Full certificate chain (your certificate + intermediate CA certificates)
- `cert.key` - Private key (keep secure!)

## Converting Your Certificates

If you have separate certificate files, combine them into the nginx format:

### Step 1: Prepare Your Files

You should have:
- Your domain certificate (e.g., `yourdomain.crt`)
- Your private key (e.g., `yourdomain.key`)
- CA bundle/chain (e.g., `ca-bundle.crt` or intermediate certificates)

### Step 2: Create the Full Chain Certificate

Combine your certificate with the CA chain:

```bash
# Concatenate your certificate and CA chain
cat yourdomain.crt ca-bundle.crt > cert.crt

# Or if you have separate intermediate certificates:
cat yourdomain.crt intermediate.crt root.crt > cert.crt
```

**Order matters:** Your domain certificate first, then intermediate certificates, then root CA.

### Step 3: Copy the Private Key

```bash
# Simply copy or rename your private key
cp yourdomain.key cert.key

# Make sure the key is secure (readable only by owner)
chmod 600 cert.key
```

### Step 4: Verify the Certificate Chain

```bash
# Check if the certificate and key match
openssl x509 -noout -modulus -in cert.crt | openssl md5
openssl rsa -noout -modulus -in cert.key | openssl md5
# The MD5 hashes should match

# Verify the certificate chain
openssl verify -CAfile cert.crt cert.crt
```

## Example with Wildcard Certificate

If you have a wildcard certificate like `*.nexxus-tech.com`:

```bash
# Create full chain
cat wildcard.nexxus-tech.com.crt ca-bundle.crt > cert.crt

# Copy private key
cp wildcard.nexxus-tech.com.key cert.key
chmod 600 cert.key
```

## Important Notes

- **Never commit certificate files to git** - they are already excluded in `.gitignore`
- Keep your private key (`.key` files) secure and never share them
- These files are mounted into the nginx container at `/etc/nginx/ssl`
- To copy certificates from production server:
  ```bash
  scp -r "root@178.105.210.197:/opt/nexxus-web/nginx/ssl/*" nginx/ssl/
  ```

## Docker Configuration

The SSL certificates are mounted as a volume in `docker-compose.yml`:
```yaml
volumes:
  - ${SSL_CERTS_PATH:-./nginx/ssl}:/etc/nginx/ssl:ro
```

**Important:** These files are mounted as a Docker volume, which means:
- ✅ Certificates are **preserved** when containers are rebuilt or updated
- ✅ Files persist on the host filesystem (not inside the container)
- ✅ Running `docker-compose up --build` will **NOT** delete these files
- ✅ Running `git pull` will **NOT** affect these files (they're in `.gitignore`)

You can override the path using the `SSL_CERTS_PATH` environment variable.

## Replacing the certificate (rotation)

JPilot terminates HTTPS in the **nginx** container. Certificates live on the **host** under
`nginx/ssl/` (or whatever path `SSL_CERTS_PATH` points to in `.env`). Updating the files does
not require rebuilding images — reload nginx after swapping the PEMs.

### Before you start

- Confirm the new certificate covers your public hostname (`NGINX_HOSTNAME` in `.env`) and any
  SANs users actually hit.
- `WEBAUTHN_ORIGIN` and `CORS_ORIGINS` must stay aligned with the URL in the browser (scheme +
  host + port). Changing hostname usually means updating `.env` and restarting `backend-api`, not
  only nginx.
- Back up the current files:
  ```bash
  cp nginx/ssl/cert.crt nginx/ssl/cert.crt.bak
  cp nginx/ssl/cert.key nginx/ssl/cert.key.bak
  chmod 600 nginx/ssl/cert.key.bak
  ```

### Option A — Replace files on the server (typical)

1. Prepare `cert.crt` (leaf + intermediate chain) and `cert.key` as described above.
2. Verify cert and key match:
   ```bash
   openssl x509 -noout -modulus -in cert.crt | openssl md5
   openssl rsa -noout -modulus -in cert.key | openssl md5
   ```
3. Install into the certs directory (paths relative to the JPilot project root):
   ```bash
   install -m 644 cert.crt nginx/ssl/cert.crt
   install -m 600 cert.key nginx/ssl/cert.key
   ```
   If you use a custom path, substitute `nginx/ssl/` with the value of `SSL_CERTS_PATH`.
4. Reload nginx (no full stack restart):
   ```bash
   ./compose.sh exec nginx nginx -s reload
   ```
5. Verify from a client:
   ```bash
   openssl s_client -connect "${NGINX_HOSTNAME}:443" -servername "${NGINX_HOSTNAME}" </dev/null 2>/dev/null | openssl x509 -noout -dates -subject
   ```
   Or open `https://<your-domain>` and confirm the new expiry in the browser.

### Option B — Re-run the installer wizard

If you prefer a guided upload with validation (CN/SAN, expiry, key match):

```bash
./install.sh --reconfigure      # macOS / Linux
.\install.ps1 -Reconfigure      # Windows
```

Choose **custom certificate**, paste or upload the new PEMs (and chain), then complete the
wizard. This overwrites `nginx/ssl/cert.crt` and `nginx/ssl/cert.key` and restarts the stack.

### Rollback

If the new cert breaks TLS:

```bash
mv nginx/ssl/cert.crt.bak nginx/ssl/cert.crt
mv nginx/ssl/cert.key.bak nginx/ssl/cert.key
./compose.sh exec nginx nginx -s reload
```

### Difficulty

| Approach | Effort | Notes |
|----------|--------|-------|
| Swap PEMs + `nginx -s reload` | **Low** (~5 min) | Standard ops; no code changes |
| Installer `--reconfigure` | **Low** | Same outcome with built-in PEM validation |
| Automated renewal (e.g. certbot + cron) | **Medium** | Not bundled; you script deploy into `nginx/ssl/` and reload |
| In-app cert upload UI | **High** | Would need new Settings flow, API, and secure file handling |
