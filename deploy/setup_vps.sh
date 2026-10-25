#!/bin/bash
# One-shot setup of the bot on a fresh Ubuntu 22.04/24.04 VPS. Run as root:
#   bash setup_vps.sh
# Secrets are typed at the prompts (hidden); they are never printed or stored in shell history.
set -euo pipefail

REPO_URL="https://github.com/Zinedine92/btc-telegram-trader.git"
APP_DIR="/opt/btc-bot"
APP_USER="botuser"

[ "$(id -u)" -eq 0 ] || { echo "Run as root (sudo -i)."; exit 1; }

echo "== 1/6 Checking that Binance is reachable from this server =="
code=$(curl -s -o /dev/null -m 15 -w '%{http_code}' https://api.binance.com/api/v3/ping || true)
echo "api.binance.com ping -> HTTP $code"
if [ "$code" != "200" ]; then
  echo "Binance is NOT reachable from this server (expected 200). Aborting before any secret is entered."
  echo "Try another data-center location or provider."
  exit 1
fi

echo "== 2/6 Installing packages =="
apt-get update -y
apt-get install -y python3 python3-venv python3-pip git curl util-linux

echo "== 3/6 Creating user and fetching code =="
id "$APP_USER" >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin "$APP_USER"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$APP_DIR"
fi

echo "== 4/6 Python environment =="
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install "python-telegram-bot==22.5" "python-dotenv==1.1.1"

echo "== 5/6 Configuration (.env) =="
if [ -f "$APP_DIR/.env" ]; then
  echo ".env already exists, keeping it."
else
  read -r -s -p "Telegram BOT_TOKEN: " BOT_TOKEN; echo
  read -r -p "Your numeric Telegram user ID (from /myid): " OWNER_ID
  read -r -s -p "Binance API key (READ-ONLY key, or leave empty): " BKEY; echo
  read -r -s -p "Binance API secret (or leave empty): " BSEC; echo
  case "$OWNER_ID" in ''|*[!0-9]*) echo "User ID must be digits only."; exit 1;; esac
  umask 177
  {
    printf 'BOT_TOKEN=%s\n' "$BOT_TOKEN"
    printf 'ALLOWED_USER_IDS=%s\n' "$OWNER_ID"
    # LIVE + opt-in flag are needed only to READ the real account; this bot has no order-placing code.
    printf 'BINANCE_MODE=LIVE\n'
    printf 'ENABLE_LIVE_TRADING=YES\n'
    [ -n "$BKEY" ] && printf 'BINANCE_API_KEY=%s\n' "$BKEY"
    [ -n "$BSEC" ] && printf 'BINANCE_API_SECRET=%s\n' "$BSEC"
    printf 'PORT=0\n'
  } > "$APP_DIR/.env"
  unset BOT_TOKEN BKEY BSEC
fi
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
chmod 600 "$APP_DIR/.env"

echo "== 6/6 Installing the service (auto-start on boot, auto-restart on crash) =="
install -m 644 "$APP_DIR/deploy/btc-bot.service" /etc/systemd/system/btc-bot.service
systemctl daemon-reload
systemctl enable --now btc-bot.service
sleep 5
systemctl --no-pager --lines=5 status btc-bot.service || true

echo
echo "Done. Server public IP (for Binance API IP restriction):"
curl -s -m 10 https://ifconfig.me || true
echo
echo "Logs: journalctl -u btc-bot -n 50 --no-pager"
echo "Stop: systemctl stop btc-bot      Restart: systemctl restart btc-bot"
echo "Update: git -C $APP_DIR pull --ff-only && systemctl restart btc-bot"
