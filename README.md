# resume-job-description-keyword-matcher

## Introduction

Parses a provided resume and job description for keyword matches and similarity.

## Requirements

* Docker (with buildkit enabled, see `/etc/docker/daemon.json`)
* docker compose

## Features

* Keyword matches between job and resume

## Installation and Setup

Generate a public cert and private key pair for Traefik.  For example:

```shell
cd ./traefik/
openssl req -x509 -nodes -days 4096 -newkey rsa:2048 -out cert.crt -keyout cert.key -subj "/C=US/ST=Self/L=Self/O=Self/CN=192.168.1.226" -addext "subjectAltName = IP:192.168.1.226"
```

Or use Let's Encrypt or some other method.

Edit the `./traefik/traefik.yaml` file and adjust the `*.crt` and `*.key` names as needed.

Edit `docker-compose.yml` and adjust the Traefik IP address or hostname

Bring up all the services via Docker

```shell
docker compose up -d --build
```

Access the web-ui: `https://<your IP or hostname>:8449` via your browser.
You may need to accept the cert if it's self-signed.

## For Developers

For file formatting and cleanup

```shell
pre-commit run --all-files
```

## References

* [https://github.com/explosion/spaCy](https://github.com/explosion/spaCy)
