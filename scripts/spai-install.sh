#!/usr/bin/env bash
set -euo pipefail

SPAISH_DIR="${SPAISH_DIR:-$HOME/Development/spaiSH}"
SPAIOS_DIR="${SPAIOS_DIR:-$HOME/Development/spaiOS}"

INSTALL_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/spaish"
SYSTEMD_DIR="$HOME/.config/systemd/user"
AUTOSTART_DIR="$HOME/.config/autostart"

# ── helpers ──────────────────────────────────────────────────────────────────

die() { echo "ERROR: $*" >&2; exit 1; }

check_deps() {
    local missing=()
    for cmd in go uv xdotool wmctrl systemctl; do
        command -v "$cmd" &>/dev/null || missing+=("$cmd")
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "Missing required tools: ${missing[*]}"
        echo ""
        # xdotool and wmctrl are apt-installable; go and uv need their own setup
        local apt_pkgs=()
        local manual=()
        for t in "${missing[@]}"; do
            case "$t" in
                xdotool|wmctrl) apt_pkgs+=("$t") ;;
                *) manual+=("$t") ;;
            esac
        done
        [[ ${#apt_pkgs[@]} -gt 0 ]] && echo "  Run: sudo apt install ${apt_pkgs[*]}"
        [[ ${#manual[@]} -gt 0 ]] && echo "  Install manually: ${manual[*]}"
        exit 1
    fi
}

install_litellm() {
    if command -v litellm &>/dev/null; then
        echo "  → litellm already installed at $(command -v litellm)"
    else
        echo "Installing litellm..."
        uv tool install litellm --quiet
        echo "  → litellm installed"
    fi
    LITELLM_BIN="$(command -v litellm)"
}

check_source_dirs() {
    [[ -d "$SPAISH_DIR" ]] || die "spaiSH source not found at $SPAISH_DIR (set \$SPAISH_DIR to override)"
    [[ -d "$SPAIOS_DIR" ]] || die "spaiOS source not found at $SPAIOS_DIR (set \$SPAIOS_DIR to override)"
}

inject_session_id() {
    local rc_file="$1"
    [[ -f "$rc_file" ]] || return 0
    if grep -q 'SPAI_SESSION_ID' "$rc_file"; then
        echo "  → SPAI_SESSION_ID already in $rc_file — skipping"
    else
        printf '\n# spaiSH: per-shell session isolation\nexport SPAI_SESSION_ID=$$\n' >> "$rc_file"
        echo "  → Added SPAI_SESSION_ID to $rc_file"
    fi
}

# ── install ───────────────────────────────────────────────────────────────────

do_install() {
    check_deps
    check_source_dirs
    mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$SYSTEMD_DIR" "$AUTOSTART_DIR"

    echo "Building spaiSH binaries..."
    (cd "$SPAISH_DIR" && go build -o "$INSTALL_DIR/spai" ./cmd/spai/)
    (cd "$SPAISH_DIR" && go build -o "$INSTALL_DIR/spaid" ./cmd/spaid/)
    (cd "$SPAISH_DIR" && go build -o "$INSTALL_DIR/spaish" ./cmd/spaish/)
    echo "  → spai / spaid / spaish installed to $INSTALL_DIR"

    echo "Installing spaiOS Python package..."
    (cd "$SPAIOS_DIR" && uv pip install -e . --quiet)
    echo "  → spaiOS installed into $SPAIOS_DIR/.venv"

    echo "Installing config..."
    if [[ ! -f "$CONFIG_DIR/spaid.toml" ]]; then
        cp "$SPAISH_DIR/config/spaid.toml" "$CONFIG_DIR/spaid.toml"
        echo "  → Config written to $CONFIG_DIR/spaid.toml"
    else
        echo "  → Config already at $CONFIG_DIR/spaid.toml — not overwriting"
    fi

    if [[ ! -f "$CONFIG_DIR/litellm.yaml" ]]; then
        cp "$SPAISH_DIR/config/litellm.yaml" "$CONFIG_DIR/litellm.yaml"
        echo "  → LiteLLM config written to $CONFIG_DIR/litellm.yaml"
    else
        echo "  → LiteLLM config already at $CONFIG_DIR/litellm.yaml — not overwriting"
    fi

    if [[ ! -f "$CONFIG_DIR/api-keys" ]]; then
        cat > "$CONFIG_DIR/api-keys" <<'EOF'
# API keys for LiteLLM proxy
# Uncomment and fill in the keys you have — litellm falls back automatically
# ANTHROPIC_API_KEY=your-key-here
# OPENAI_API_KEY=your-key-here
EOF
        echo "  → API keys template written to $CONFIG_DIR/api-keys — add your keys there"
    else
        echo "  → API keys file already at $CONFIG_DIR/api-keys — not overwriting"
    fi

    echo "Installing litellm proxy..."
    install_litellm

    echo "Installing systemd user services..."
    cat > "$SYSTEMD_DIR/litellm-proxy.service" <<EOF
[Unit]
Description=LiteLLM proxy for spaiSH
After=network.target

[Service]
Type=simple
EnvironmentFile=-$CONFIG_DIR/api-keys
Environment=LITELLM_MASTER_KEY=spai-local
ExecStart=$LITELLM_BIN --config $CONFIG_DIR/litellm.yaml --port 4000
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

    cat > "$SYSTEMD_DIR/spaid.service" <<EOF
[Unit]
Description=spaiSH daemon
After=litellm-proxy.service

[Service]
Type=simple
Environment=LITELLM_MASTER_KEY=spai-local
ExecStart=$INSTALL_DIR/spaid
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable --now litellm-proxy
    systemctl --user enable --now spaid
    echo "  → litellm-proxy and spaid services enabled and started"

    echo "Installing spaiOS autostart entry..."
    cat > "$AUTOSTART_DIR/spaios.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=spaiOS
Exec=$SPAIOS_DIR/.venv/bin/spaiOS
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
    echo "  → Autostart entry written to $AUTOSTART_DIR/spaios.desktop"

    echo "Configuring shell session isolation..."
    inject_session_id "$HOME/.bashrc"
    inject_session_id "$HOME/.zshrc"

    echo ""
    echo "spaiOS ready. Press Super+Space or say your wake word."
    echo ""
    echo "Next steps:"
    echo "  • Add API keys:    $CONFIG_DIR/api-keys  (uncomment lines for keys you have)"
    echo "    Priority:  Claude (ANTHROPIC_API_KEY) → GPT-4o-mini (OPENAI_API_KEY) → local Ollama"
    echo "  • Reload LiteLLM:  systemctl --user restart litellm-proxy  (after editing api-keys)"
    echo "  • Check services:  systemctl --user status litellm-proxy spaid"
    echo "  • Start overlay:   $SPAIOS_DIR/.venv/bin/spaiOS"
}

# ── uninstall ─────────────────────────────────────────────────────────────────

do_uninstall() {
    echo "Stopping and disabling services..."
    for svc in spaid litellm-proxy; do
        if systemctl --user is-active --quiet "$svc" 2>/dev/null; then
            systemctl --user stop "$svc"
        fi
        if systemctl --user is-enabled --quiet "$svc" 2>/dev/null; then
            systemctl --user disable "$svc"
        fi
        rm -f "$SYSTEMD_DIR/$svc.service"
    done
    systemctl --user daemon-reload 2>/dev/null || true
    echo "  → spaid and litellm-proxy services removed"

    echo "Removing binaries..."
    rm -f "$INSTALL_DIR/spai" "$INSTALL_DIR/spaid" "$INSTALL_DIR/spaish"
    echo "  → Binaries removed from $INSTALL_DIR"

    echo "Removing autostart entry..."
    rm -f "$AUTOSTART_DIR/spaios.desktop"
    echo "  → Autostart entry removed"

    echo ""
    echo "Uninstall complete. Config preserved at $CONFIG_DIR/spaid.toml"
}

# ── dispatch ──────────────────────────────────────────────────────────────────

CMD="${1:-}"
case "$CMD" in
    install)   do_install ;;
    uninstall) do_uninstall ;;
    reinstall) do_uninstall; echo ""; do_install ;;
    *)
        echo "Usage: $0 {install|uninstall|reinstall}"
        echo ""
        echo "  install    Build Go binaries, install Python package, register systemd service + autostart"
        echo "  uninstall  Stop service, remove binaries and autostart entry (config preserved)"
        echo "  reinstall  Uninstall then install (full rebuild)"
        exit 1
        ;;
esac
