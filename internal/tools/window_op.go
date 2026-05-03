package tools

import (
	"fmt"
	"os/exec"
	"strconv"
	"strings"
)

// GetActiveWinIDHex returns the active window's X11 ID as a hex string (e.g. "0x3a00005").
func GetActiveWinIDHex() (string, error) {
	out, err := exec.Command("xdotool", "getactivewindow").Output()
	if err != nil {
		return "", fmt.Errorf("xdotool getactivewindow: %w", err)
	}
	dec := strings.TrimSpace(string(out))
	n, err := strconv.ParseInt(dec, 10, 64)
	if err != nil {
		return dec, nil
	}
	return fmt.Sprintf("0x%x", n), nil
}

// ScreenGeometry returns the display's pixel dimensions.
func ScreenGeometry() (w, h int, err error) {
	out, err := exec.Command("xdotool", "getdisplaygeometry").Output()
	if err != nil {
		return 0, 0, fmt.Errorf("xdotool getdisplaygeometry: %w", err)
	}
	parts := strings.Fields(strings.TrimSpace(string(out)))
	if len(parts) < 2 {
		return 0, 0, fmt.Errorf("unexpected geometry output: %q", string(out))
	}
	w, err = strconv.Atoi(parts[0])
	if err != nil {
		return
	}
	h, err = strconv.Atoi(parts[1])
	return
}

// SnapLeft snaps the window to the left half of the screen.
func SnapLeft(winID string) error {
	sw, sh, err := ScreenGeometry()
	if err != nil {
		return err
	}
	return snapTo(winID, 0, 0, sw/2, sh)
}

// SnapRight snaps the window to the right half of the screen.
func SnapRight(winID string) error {
	sw, sh, err := ScreenGeometry()
	if err != nil {
		return err
	}
	half := sw / 2
	return snapTo(winID, half, 0, sw-half, sh)
}

// MaximizeWindow maximizes the window.
func MaximizeWindow(winID string) error {
	if _, err := exec.LookPath("wmctrl"); err == nil {
		return exec.Command("wmctrl", "-i", "-r", winID, "-b", "add,maximized_vert,maximized_horz").Run()
	}
	// Fallback: xdotool key super+Up (unreliable but best-effort without wmctrl)
	return exec.Command("xdotool", "windowfocus", "--sync", winID,
		"key", "--clearmodifiers", "super+Up").Run()
}

// CloseWindow closes the window.
func CloseWindow(winID string) error {
	return exec.Command("xdotool", "windowclose", winID).Run()
}

// snapTo moves and resizes the window. Uses wmctrl if available (handles maximized state);
// falls back to xdotool otherwise.
func snapTo(winID string, x, y, w, h int) error {
	if _, err := exec.LookPath("wmctrl"); err == nil {
		// Remove maximized state before repositioning.
		exec.Command("wmctrl", "-i", "-r", winID, "-b", "remove,maximized_vert,maximized_horz").Run()
		return exec.Command("wmctrl", "-i", "-r", winID, "-e",
			fmt.Sprintf("0,%d,%d,%d,%d", x, y, w, h)).Run()
	}
	// xdotool fallback: may not remove maximized state on GNOME but worth trying.
	exec.Command("xdotool", "windowmove", "--sync", winID,
		strconv.Itoa(x), strconv.Itoa(y)).Run()
	return exec.Command("xdotool", "windowsize", "--sync", winID,
		strconv.Itoa(w), strconv.Itoa(h)).Run()
}
