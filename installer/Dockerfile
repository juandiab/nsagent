FROM python:3.12-slim

# openssl is used by entrypoint.sh to mint the installer's own ephemeral TLS cert
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /installer

COPY installer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY installer/ .
COPY THIRD_PARTY_NOTICES.txt /usr/share/jpilot/THIRD_PARTY_NOTICES.txt
RUN chmod +x /installer/entrypoint.sh

EXPOSE 9443

ENTRYPOINT ["/installer/entrypoint.sh"]
