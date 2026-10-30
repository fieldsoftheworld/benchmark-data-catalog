#!/usr/bin/env bash
# First-boot setup for the catalog build instance (EC2 user data; runs as root).
#
# Installs what README's "Working on it" needs on Ubuntu 24.04: uv (which
# provides the pinned CPython 3.11), tippecanoe (built from source), Node 22
# for chiitiler, the source-coop CLI, and tmux. Clones this repository into
# /home/ubuntu/benchmark-data-catalog and runs `uv sync` there.
#
# Also installs an idle watchdog: the instance powers itself off (its
# shutdown behaviour is "stop", so the disk and staging/ survive) after an
# hour with no build/upload process and nobody logged in.
#
# Progress: /var/log/ftw-bootstrap.log; done when /var/lib/ftw-bootstrap.done exists.
set -euxo pipefail
exec > >(tee -a /var/log/ftw-bootstrap.log) 2>&1

REPO=https://github.com/fieldsoftheworld/benchmark-data-catalog
BRANCH="${FTW_CATALOG_BRANCH:-main}"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y build-essential git tmux htop unzip curl ca-certificates \
    libsqlite3-dev zlib1g-dev

# Node 22 for chiitiler (Ubuntu's packaged node is too old).
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs

# tippecanoe for ftwd's docs stage (PMTiles + vector styles).
if ! command -v tippecanoe >/dev/null; then
    git clone --depth 1 https://github.com/felt/tippecanoe /tmp/tippecanoe
    make -C /tmp/tippecanoe -j"$(nproc)"
    make -C /tmp/tippecanoe install
    rm -rf /tmp/tippecanoe
fi

sudo -u ubuntu -H env REPO="$REPO" BRANCH="$BRANCH" bash -euxo pipefail <<'EOF'
curl -LsSf https://astral.sh/uv/install.sh | sh
curl --proto '=https' --tlsv1.2 -LsSf \
    https://github.com/source-cooperative/source-coop-cli/releases/latest/download/source-coop-cli-installer.sh | sh

# credential_process runs without a login shell, so it needs the absolute path.
SOURCE_COOP="$HOME/.cargo/bin/source-coop"
[ -x "$SOURCE_COOP" ] || SOURCE_COOP="$HOME/.local/bin/source-coop"
mkdir -p "$HOME/.aws"
cat > "$HOME/.aws/config" <<AWS
[profile source-coop]
credential_process = $SOURCE_COOP creds
endpoint_url = https://data.source.coop
region = us-west-2
AWS

if [ ! -d "$HOME/benchmark-data-catalog" ]; then
    git clone --branch "$BRANCH" "$REPO" "$HOME/benchmark-data-catalog"
fi
cd "$HOME/benchmark-data-catalog"
"$HOME/.local/bin/uv" sync
EOF

# Idle watchdog: power off after 6 consecutive idle checks, 10 minutes apart.
cat > /usr/local/bin/ftw-idle-check <<'EOF'
#!/usr/bin/env bash
STATE=/var/lib/ftw-idle-count
busy=$(pgrep -fc 'ftwd|run_batch|build.py|upload_data|publish.py|thumbnail.py' || true)
users=$(who | wc -l)
if [ "$busy" -gt 0 ] || [ "$users" -gt 0 ]; then
    echo 0 > "$STATE"
    exit 0
fi
count=$(( $(cat "$STATE" 2>/dev/null || echo 0) + 1 ))
echo "$count" > "$STATE"
if [ "$count" -ge 6 ]; then
    logger "ftw-idle-check: idle for an hour, powering off"
    systemctl poweroff
fi
EOF
chmod +x /usr/local/bin/ftw-idle-check
cat > /etc/systemd/system/ftw-idle-check.service <<'EOF'
[Unit]
Description=Power off the catalog build instance when idle
[Service]
Type=oneshot
ExecStart=/usr/local/bin/ftw-idle-check
EOF
cat > /etc/systemd/system/ftw-idle-check.timer <<'EOF'
[Unit]
Description=Check every 10 minutes whether the build instance is idle
[Timer]
OnBootSec=30min
OnUnitActiveSec=10min
[Install]
WantedBy=timers.target
EOF
echo 0 > /var/lib/ftw-idle-count
systemctl daemon-reload
systemctl enable --now ftw-idle-check.timer

touch /var/lib/ftw-bootstrap.done
