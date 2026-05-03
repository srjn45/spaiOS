package tools

import (
	"fmt"
	"os/exec"
	"strings"
	"syscall"
)

// LaunchApp launches an application by name in the background, detached from spaid.
// Returns an error if the binary cannot be found or the process fails to start.
func LaunchApp(name string) error {
	if name == "" {
		return fmt.Errorf("app name required")
	}
	cmd := exec.Command(name)
	// Detach so the child outlives spaid and doesn't inherit our stdio.
	cmd.SysProcAttr = &syscall.SysProcAttr{Setsid: true}
	cmd.Stdout = nil
	cmd.Stderr = nil
	cmd.Stdin = nil
	return cmd.Start()
}

// ListWindows returns a slice of "<hex_id> <title>" strings for all mapped X11 windows.
// Requires wmctrl.
func ListWindows() ([]string, error) {
	out, err := exec.Command("wmctrl", "-l").Output()
	if err != nil {
		return nil, fmt.Errorf("wmctrl -l: %w", err)
	}
	var windows []string
	for _, line := range strings.Split(strings.TrimSpace(string(out)), "\n") {
		line = strings.TrimSpace(line)
		if line != "" {
			windows = append(windows, line)
		}
	}
	return windows, nil
}
