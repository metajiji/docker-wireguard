# Wireguard in docker with gui

## Setup

Copy example files

```bash
cp .env.example .env
cp wg-server.env.example wg-server.env
cp wg-ui.env.example wg-ui.env
```

Edit for you things and start the project

```bash
docker-compose up -d
```

Configure firewall

```bash
firewall-cmd --list-all-zones
firewall-cmd --permanent --add-service=http  # http services
firewall-cmd --permanent --add-service=https  # https servies
firewall-cmd --permanent --add-port=8080/tcp  # traefik dashboard
firewall-cmd --permanent --add-port=5182/udp  # wireguard
firewall-cmd --reload
firewall-cmd --list-all --zone=public
```

## Links

- <https://www.procustodibus.com/blog/2021/03/wireguard-allowedips-calculator/>
