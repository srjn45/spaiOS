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
        echo "  → Config written to $CONFIG_DIR/spaid.toml — edit to set your API key/model"
    else
        echo "  → Config already at $CONFIG_DIR/spaid.toml — not overwriting"
    fi

    echo "Installing systemd user service..."
    cat > "$SYSTEMD_DIR/spaid.service" <<EOF
[Unit]
Description=spaiSH daemon
After=network.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/spaid
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable --now spaid
    echo "  → spaid service enabled and started"

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
    echo "  • Edit $CONFIG_DIR/spaid.toml — set your API endpoint and model"
    echo "  • Set your API key: export SPAI_API_KEY='your-key'  (add to ~/.bashrc)"
    echo "  • Check service:   systemctl --user status spaid"
    echo "  • Start overlay:   $SPAIOS_DIR/.venv/bin/spaiOS"
}

# ── uninstall ─────────────────────────────────────────────────────────────────

do_uninstall() {
    echo "Stopping and disabling spaid service..."
    if systemctl --user is-active --quiet spaid 2>/dev/null; then
        systemctl --user stop spaid
    fi
    if systemctl --user is-enabled --quiet spaid 2>/dev/null; then
        systemctl --user disable spaid
    fi
    rm -f "$SYSTEMD_DIR/spaid.service"
    systemctl --user daemon-reload 2>/dev/null || true
    echo "  → spaid service removed"

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
