# SSL Certificates Directory

This directory should contain your SSL/TLS certificates for HTTPS support.

## Required Files

Place the following certificate files in this directory:

- `wildcard.nexxus-tech.com.crt` - SSL certificate for the domain
- `wildcard.nexxus-tech.com.key` - Private key (keep secure!)
- `fullchain.crt` - Full certificate chain
- `ca-chain.crt` - Certificate authority chain

## Additional Certificate Files (optional)

- `STAR_nexxus-tech_com.crt`
- `SSL2BUYEMEARSADomainValidationSecureServerCA.crt`
- `USERTrustRSACertificationAuthority.crt`
- `SectigoPublicServerAuthenticationRootR46_USERTrust.crt`

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
