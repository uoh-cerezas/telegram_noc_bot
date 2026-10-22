# Telegram NOC bot

Standalone read-only Telegram bot for the FIC Cerezas NOC. The bot consumes
the NOC HTTP API and does not connect directly to MongoDB, TTN or the reporting
pipeline.

## Commands

```text
/start
/help
/status
/gateways
/sensors
/sensor <device_id>
/gateway <gateway_id>
/alerts
```

`/sensors` returns a compact summary grouped by TTN application
(beneficiario/campo) and includes only sensors with valid GPS coordinates.
Use `/sensor <device_id>` for one located sensor's detail.

The bot is read-only: it does not generate reports, modify sensors, restart
gateways or write to databases.

## Telegram setup

Create the bot with `@BotFather`, configure its commands and obtain a token.
Start a conversation with the bot and send `/start`. The numeric value in
`message.from.id` from `getUpdates` is the user ID to authorize.

Never commit the token. If it is exposed, revoke it in BotFather with
`/revoke` and generate a new one with `/token`.

## Local dry run

```bash
cd /Users/ignacio/repos/fic/repos/telegram_noc_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

TELEGRAM_MODE=mock python bot.py --dry-run /status
TELEGRAM_MODE=mock python bot.py --dry-run /gateways
TELEGRAM_MODE=mock python bot.py --dry-run /sensors
TELEGRAM_MODE=mock python bot.py --dry-run /sensor sensor-rengo-01
python -m unittest discover -s tests -v
```

## Local live execution

Start the NOC first on port `8060`, then create a local env file:

```bash
cp .env.example .env.local
chmod 600 .env.local
nano .env.local
```

Set the real `TELEGRAM_BOT_TOKEN` and authorized Telegram IDs. The local API
URL is `http://127.0.0.1:8060` when the bot runs directly on the host.

```bash
set -a
source .env.local
set +a
python bot.py
```

## Docker local execution

The local Compose file reaches an NOC published on the Docker host through
`host.docker.internal` by default:

```bash
cp .env.example .env.local
chmod 600 .env.local
# Edit .env.local with the real token and Telegram user ID.

set -a
source .env.local
set +a
docker compose --env-file .env.local up --build -d
docker compose logs -f telegram-noc-bot
```

Stop it with:

```bash
docker compose --env-file .env.local down
```

## Production deployment alongside the NOC

The bot is a separate container. It only needs to share the existing
`FIC-app-network` Docker network with `ttn-noc`; no host port is required.

On the server, place the repository at:

```text
/home/uoh/cerezas_web_server/services/telegram-noc-bot
```

Store the secret environment file outside Git, for example:

```text
/home/uoh/cerezas_web_server/config/telegram-noc.env
```

Its relevant values are:

```dotenv
TELEGRAM_MODE=live
TELEGRAM_BOT_TOKEN=replace-with-new-botfather-token
TELEGRAM_ALLOWED_USER_IDS=885967755
NOC_API_URL=http://ttn-noc:8060
NOC_REQUEST_TIMEOUT=180
NOC_DOCKER_NETWORK=FIC-app-network
```

Deploy with:

```bash
cd /home/uoh/cerezas_web_server/services/telegram-noc-bot
docker compose \
  --env-file /home/uoh/cerezas_web_server/config/telegram-noc.env \
  -f compose.yaml -f compose.production.yaml \
  up --build -d
```

Verify:

```bash
docker compose \
  --env-file /home/uoh/cerezas_web_server/config/telegram-noc.env \
  -f compose.yaml -f compose.production.yaml \
  ps

docker logs -f telegram-noc-bot
```

The bot uses Telegram long polling, so it does not need an exposed HTTP port
or a reverse-proxy route.
