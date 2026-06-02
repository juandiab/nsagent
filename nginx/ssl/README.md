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
