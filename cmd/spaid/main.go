package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"spaish/internal/agent"
	"spaish/internal/ai"
	"spaish/internal/config"
	"spaish/internal/executor"
	"spaish/internal/llm"
	"spaish/internal/protocol"
	"spaish/internal/router"
	"spaish/internal/session"
	"spaish/internal/socket"
	"spaish/internal/tools"
)

func configPath() string {
	if d := os.Getenv("XDG_CONFIG_HOME"); d != "" {
		return filepath.Join(d, "spaish", "spaid.toml")
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".config", "spaish", "spaid.toml")
}

func sockPath() string {
	if d := os.Getenv("XDG_DATA_HOME"); d != "" {
		return filepath.Join(d, "spaish", "spaid.sock")
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".local", "share", "spaish", "spaid.sock")
}

// loadSession returns the session for the given ID, falling back to "default".
func loadSession(id string) *session.Session {
	if id == "" {
		id = "default"
	}
	sess, err := session.LoadByID(id)
	if err != nil {
		log.Printf("session load warning (id=%s): %v — starting fresh", id, err)
		return new(session.Session)
	}
	return sess
}

const shellSystemPrompt = `You are an AI assistant embedded in the user's terminal shell.
Be concise — one short paragraph maximum.
When suggesting a specific command, wrap it in backticks.
Do not use markdown code blocks — plain text only.`

const overlaySystemPrompt = `You are spaiOS, an AI assistant running as a desktop overlay on the user's Linux desktop.

When the user asks you to control a window or launch an app, output a TOOL_CALL line first, then your confirmation:

TOOL_CALL: {"tool":"snap_window","side":"left"}                        — snap the focused window to left half
TOOL_CALL: {"tool":"snap_window","side":"right"}                       — snap the focused window to right half
TOOL_CALL: {"tool":"snap_window","side":"top"}                         — snap the focused window to top half
TOOL_CALL: {"tool":"snap_window","side":"bottom"}                      — snap the focused window to bottom half
TOOL_CALL: {"tool":"snap_window","side":"left","target":"Firefox"}     — snap a named window to left half
TOOL_CALL: {"tool":"maximize_window"}                                  — maximize the focused window
TOOL_CALL: {"tool":"maximize_window","target":"Firefox"}               — maximize a named window
TOOL_CALL: {"tool":"close_window","target":"Firefox"}                  — close a named window
TOOL_CALL: {"tool":"open_app","app":"firefox"}                         — launch an application by binary name

Rules:
- When the user names a specific app (e.g. "Firefox", "Chrome", "Warp"), always set "target" to that name.
- Only omit "target" when the user says "this window" or "the window" with no app name.
- Output the TOOL_CALL line by itself on its own line, then your 1-2 sentence confirmation.
- Plain text only, no markdown.`

func shellUserMessage(ev *protocol.ShellEvent) string {
	switch ev.Trigger {
	case "error":
		return fmt.Sprintf("Command: %s\nOutput: %s\nExit code: %d\n\nWhat went wrong and how do I fix it?",
			ev.Command, ev.Output, ev.ExitCode)
	case "prompt":
		if ev.Query == "" {
			return "What should I do next?"
		}
		return ev.Query
	case "pattern":
		return fmt.Sprintf("I've run this sequence multiple times:\n%s\n\nCreate a concise shell alias or function to automate it.",
			ev.Command)
	case "rethink":
		if ev.Query != "" {
			return ev.Query
		}
		return "Please reconsider your previous response."
	default:
		return fmt.Sprintf("Command: %s\nOutput: %s\nExit code: %d\n\nWhat went wrong and how do I fix it?",
			ev.Command, ev.Output, ev.ExitCode)
	}
}

// executeWindowTool parses the JSON from a TOOL_CALL line and runs the tool.
// Returns a short status string for logging; errors are surfaced there only (not to user).
func executeWindowTool(jsonStr string, activeWinID string) string {
	var call struct {
		Tool   string `json:"tool"`
		Side   string `json:"side,omitempty"`
		App    string `json:"app,omitempty"`
		Target string `json:"target,omitempty"` // window name to search for via wmctrl
	}
	if err := json.NewDecoder(strings.NewReader(jsonStr)).Decode(&call); err != nil {
		return fmt.Sprintf("parse error: %v", err)
	}

	// Resolve window ID: named target takes priority, then captured active window.
	resolveWinID := func() (string, error) {
		if call.Target != "" {
			id, err := tools.FindWindowByName(call.Target)
			if err != nil {
				return "", fmt.Errorf("window %q not found: %w", call.Target, err)
			}
			return id, nil
		}
		if activeWinID != "" {
			return activeWinID, nil
		}
		id, err := tools.GetActiveWinIDHex()
		if err != nil {
			return "", fmt.Errorf("no active window: %w", err)
		}
		return id, nil
	}

	switch call.Tool {
	case "snap_window":
		winID, err := resolveWinID()
		if err != nil {
			return err.Error()
		}
		switch call.Side {
		case "right":
			err = tools.SnapRight(winID)
		case "top":
			err = tools.SnapTop(winID)
		case "bottom":
			err = tools.SnapBottom(winID)
		default: // "left" or unspecified
			err = tools.SnapLeft(winID)
		}
		if err != nil {
			return fmt.Sprintf("snap error: %v", err)
		}
		return "snapped " + call.Side

	case "maximize_window":
		winID, err := resolveWinID()
		if err != nil {
			return err.Error()
		}
		if err := tools.MaximizeWindow(winID); err != nil {
			return fmt.Sprintf("maximize error: %v", err)
		}
		return "maximized"

	case "close_window":
		winID, err := resolveWinID()
		if err != nil {
			return err.Error()
		}
		// Safety guard: never close the spaiOS overlay window.
		if title := tools.GetWindowTitle(winID); strings.Contains(strings.ToLower(title), "spaios") {
			return "refused: cannot close spaiOS overlay"
		}
		if err := tools.CloseWindow(winID); err != nil {
			return fmt.Sprintf("close error: %v", err)
		}
		return "closed"

	case "open_app":
		if err := tools.LaunchApp(call.App); err != nil {
			return fmt.Sprintf("launch error: %v", err)
		}
		return "launched " + call.App

	default:
		return fmt.Sprintf("unknown tool: %s", call.Tool)
	}
}

func buildOverlayMessages(q *protocol.OverlayQuery, sess *session.Session) []ai.Message {
	sysMsg := overlaySystemPrompt
	if q.ActiveWindow != nil && q.ActiveWindow.Title != "" {
		sysMsg += fmt.Sprintf("\n\nActive window: %s (win_id: %s)", q.ActiveWindow.Title, q.ActiveWindow.WinID)
	}
	msgs := []ai.Message{{Role: "system", Content: sysMsg}}
	msgs = append(msgs, sess.MessagesForPrompt()...)
	msgs = append(msgs, ai.Message{Role: "user", Content: q.Query})
	return msgs
}

func buildShellMessages(ev *protocol.ShellEvent, sess *session.Session) []ai.Message {
	sysMsg := shellSystemPrompt + "\n\nWorking directory: " + ev.CWD
	msgs := []ai.Message{{Role: "system", Content: sysMsg}}
	if ev.Trigger == "rethink" && ev.FullHistory != "" {
		msgs = append(msgs, session.ParseHistoryMessages(ev.FullHistory)...)
	} else {
		msgs = append(msgs, sess.MessagesForPrompt()...)
	}
	msgs = append(msgs, ai.Message{Role: "user", Content: shellUserMessage(ev)})
	return msgs
}

func main() {
	logPath := filepath.Join(filepath.Dir(sockPath()), "spaid.log")
	os.MkdirAll(filepath.Dir(logPath), 0700)
	logFile, err := os.OpenFile(logPath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0600)
	if err == nil {
		log.SetOutput(logFile)
		defer logFile.Close()
	}

	cfg, err := config.Load(configPath())
	if err != nil {
		log.Fatalf("config error: %v", err)
	}

	llmState, err := llm.LoadState(llm.DefaultStatePath())
	if err != nil {
		log.Printf("llm state load warning: %v — using defaults", err)
		llmState, _ = llm.LoadState(llm.DefaultStatePath())
	}
	llmMgr := llm.NewManager(llmState)

	// Prefer the active model from llm-state over the config value.
	// This lets `spai llm use <model>` take effect after a daemon restart.
	localModel := cfg.Local.LocalModel
	if llmState.ActiveModel != "" {
		localModel = llmState.ActiveModel
	}

	cloud := ai.NewCloudProvider(cfg.Provider.Endpoint, cfg.APIKey(), cfg.Provider.Model)
	var local ai.Provider
	switch llmState.ActiveRuntime {
	case "bitnet":
		rt, _ := llm.Get("bitnet")
		local = ai.NewOpenAICompatProvider(rt.Endpoint, localModel)
	default: // "ollama" or unset
		local = ai.NewLocalProvider(cfg.Local.OllamaEndpoint, localModel)
	}
	rtr := router.New(cfg, cloud, local)

	sock := sockPath()
	log.Printf("spaid starting, socket: %s", sock)

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT)
	go func() {
		<-sigCh
		log.Println("spaid shutting down")
		os.Remove(sock)
		os.Exit(0)
	}()

	onQuery := func(req *protocol.Request, enc *json.Encoder) {
		sess := loadSession(req.SessionID)
		respCh, err := rtr.Route(context.Background(), req, sess)
		if err != nil {
			enc.Encode(protocol.Response{Type: "error", Content: err.Error()})
			return
		}
		var fullText strings.Builder
		for resp := range respCh {
			enc.Encode(resp)
			if resp.Type == "text" {
				fullText.WriteString(resp.Content)
			}
		}
		assistantText := fullText.String()
		sess.AddExchange(req.Query, assistantText)
		if err := sess.SaveCache(); err != nil {
			log.Printf("session save error: %v", err)
		}
		go sess.AppendHistory(time.Now().UTC(), req.Query, assistantText, "")
	}

	onExec := func(req *protocol.Request, enc *json.Encoder) {
		for _, cmd := range req.Commands {
			enc.Encode(protocol.Response{Type: "output", Content: fmt.Sprintf("$ %s\n", cmd)})
			var out strings.Builder
			if err := executor.Execute(cmd, &out); err != nil {
				enc.Encode(protocol.Response{Type: "output", Content: out.String()})
				enc.Encode(protocol.Response{Type: "error", Content: fmt.Sprintf("command failed: %v", err)})
				return
			}
			enc.Encode(protocol.Response{Type: "output", Content: out.String()})
		}
		enc.Encode(protocol.Response{Type: "done"})
	}

	onLLM := func(req *protocol.Request, enc *json.Encoder) {
		if req.LLM == nil {
			enc.Encode(protocol.Response{Type: "error", Content: "missing llm payload"})
			enc.Encode(protocol.Response{Type: "done"})
			return
		}
		for resp := range llmMgr.Handle(req.LLM) {
			enc.Encode(resp)
		}
	}

	onAgent := func(req *protocol.Request, enc *json.Encoder, dec *json.Decoder) {
		if req.Agent == nil {
			enc.Encode(protocol.Response{Type: "error", Content: "missing agent payload"})
			enc.Encode(protocol.Response{Type: "done"})
			return
		}

		sess := loadSession(req.SessionID)
		provider, err := rtr.SelectProvider(req.ForceLocal)
		if err != nil {
			enc.Encode(protocol.Response{Type: "error", Content: err.Error()})
			enc.Encode(protocol.Response{Type: "done"})
			return
		}

		agentCfg := agent.Config{
			Autonomous:    cfg.Agent.Autonomous || req.Agent.Autonomous,
			MaxIterations: cfg.Agent.MaxIterations,
			Verbose:       cfg.Agent.Verbose || req.Agent.Verbose,
			WorkingDir:    req.WorkingDir,
			GitBranch:     req.GitBranch,
			Stdin:         req.Stdin,
		}

		ctx, cancel := context.WithCancel(context.Background())
		defer cancel()

		confirmFn := func(confirmReq protocol.ConfirmRequest) bool {
			data, err := json.Marshal(confirmReq)
			if err != nil {
				return false
			}
			enc.Encode(protocol.Response{Type: "confirm_request", Content: string(data)})
			var reply protocol.Request
			if err := dec.Decode(&reply); err != nil || reply.ConfirmResponse == nil {
				return false
			}
			return reply.ConfirmResponse.Approved
		}

		a := agent.New(provider, agentCfg, confirmFn)

		var fullText strings.Builder
		var outputText strings.Builder
		for resp := range a.Run(ctx, req.Agent, sess) {
			enc.Encode(resp)
			if resp.Type == "text" {
				fullText.WriteString(resp.Content)
			}
			if resp.Type == "output" {
				outputText.WriteString(resp.Content)
			}
		}
		assistantText := fullText.String()
		sess.AddExchange(req.Agent.Query, assistantText)
		if err := sess.SaveCache(); err != nil {
			log.Printf("session save error: %v", err)
		}
		go sess.AppendHistory(time.Now().UTC(), req.Agent.Query, assistantText, outputText.String())
	}

	onSession := func(req *protocol.Request, enc *json.Encoder) {
		if req.Session == nil {
			enc.Encode(protocol.Response{Type: "error", Content: "missing session payload"})
			enc.Encode(protocol.Response{Type: "done"})
			return
		}

		sess := loadSession(req.SessionID)

		switch req.Session.Command {
		case "clear":
			if req.Session.Lines == 0 {
				if err := sess.Clear(); err != nil {
					log.Printf("session clear error: %v", err)
				}
				enc.Encode(protocol.Response{Type: "text", Content: "Session cleared.\n"})
			} else {
				sess.Trim(req.Session.Lines)
				if err := sess.SaveCache(); err != nil {
					log.Printf("session save error: %v", err)
				}
				enc.Encode(protocol.Response{Type: "text", Content: fmt.Sprintf("Session trimmed to %d messages.\n", req.Session.Lines)})
			}
			enc.Encode(protocol.Response{Type: "done"})

		case "compact":
			if len(sess.Messages) == 0 && sess.Summary == "" {
				enc.Encode(protocol.Response{Type: "text", Content: "Nothing to compact — session is empty.\n"})
				enc.Encode(protocol.Response{Type: "done"})
				return
			}

			provider, err := rtr.SelectProvider(req.ForceLocal)
			if err != nil {
				enc.Encode(protocol.Response{Type: "error", Content: err.Error()})
				enc.Encode(protocol.Response{Type: "done"})
				return
			}

			compactMsgs := []ai.Message{
				{Role: "system", Content: "Summarise the following conversation concisely. Focus on what was worked on and what was achieved. One short paragraph."},
			}
			compactMsgs = append(compactMsgs, sess.Messages...)

			textCh, err := provider.Complete(context.Background(), compactMsgs)
			if err != nil {
				enc.Encode(protocol.Response{Type: "error", Content: err.Error()})
				enc.Encode(protocol.Response{Type: "done"})
				return
			}

			var summary strings.Builder
			for chunk := range textCh {
				summary.WriteString(chunk)
				enc.Encode(protocol.Response{Type: "text", Content: chunk})
			}

			sess.Compact(summary.String())
			if err := sess.SaveCache(); err != nil {
				log.Printf("session save error: %v", err)
			}
			enc.Encode(protocol.Response{Type: "done"})

		case "rebuild-context":
			history, err := sess.ReadAllHistory()
			if err != nil || history == "" {
				enc.Encode(protocol.Response{Type: "text", Content: "No history to rebuild from.\n"})
				enc.Encode(protocol.Response{Type: "done"})
				return
			}

			provider, err := rtr.SelectProvider(req.ForceLocal)
			if err != nil {
				enc.Encode(protocol.Response{Type: "error", Content: err.Error()})
				enc.Encode(protocol.Response{Type: "done"})
				return
			}

			rebuildMsgs := []ai.Message{
				{Role: "system", Content: "Summarise this conversation history concisely in one paragraph."},
				{Role: "user", Content: history},
			}

			textCh, err := provider.Complete(context.Background(), rebuildMsgs)
			if err != nil {
				enc.Encode(protocol.Response{Type: "error", Content: err.Error()})
				enc.Encode(protocol.Response{Type: "done"})
				return
			}

			var summary strings.Builder
			for chunk := range textCh {
				summary.WriteString(chunk)
				enc.Encode(protocol.Response{Type: "text", Content: chunk})
			}

			sess.Messages = session.ParseHistoryMessages(history)
			sess.SetSummary(summary.String())
			if err := sess.SaveCache(); err != nil {
				log.Printf("session save error: %v", err)
			}
			enc.Encode(protocol.Response{Type: "done"})

		default:
			enc.Encode(protocol.Response{Type: "error", Content: "unknown session command: " + req.Session.Command})
			enc.Encode(protocol.Response{Type: "done"})
		}
	}

	onShell := func(req *protocol.Request, enc *json.Encoder) {
		if req.Shell == nil {
			enc.Encode(protocol.Response{Type: "error", Content: "missing shell payload"})
			enc.Encode(protocol.Response{Type: "done"})
			return
		}
		ev := req.Shell
		sess := loadSession(req.SessionID)
		provider, err := rtr.SelectProvider(req.ForceLocal)
		if err != nil {
			enc.Encode(protocol.Response{Type: "error", Content: err.Error()})
			enc.Encode(protocol.Response{Type: "done"})
			return
		}

		msgs := buildShellMessages(ev, sess)
		textCh, err := provider.Complete(context.Background(), msgs)
		if err != nil {
			enc.Encode(protocol.Response{Type: "error", Content: err.Error()})
			enc.Encode(protocol.Response{Type: "done"})
			return
		}

		var fullText strings.Builder
		for chunk := range textCh {
			fullText.WriteString(chunk)
			enc.Encode(protocol.Response{Type: "text", Content: chunk})
		}
		enc.Encode(protocol.Response{Type: "done"})

		userMsg := shellUserMessage(ev)
		aiReply := fullText.String()
		sess.AddExchange(userMsg, aiReply)
		if err := sess.SaveCache(); err != nil {
			log.Printf("session save error: %v", err)
		}
		go sess.AppendHistory(time.Now().UTC(), userMsg, aiReply, "")
	}

	onOverlay := func(req *protocol.Request, enc *json.Encoder) {
		if req.Overlay == nil {
			enc.Encode(protocol.Response{Type: "error", Content: "missing overlay payload"})
			enc.Encode(protocol.Response{Type: "done"})
			return
		}
		q := req.Overlay
		winTitle := "(none)"
		if q.ActiveWindow != nil {
			winTitle = q.ActiveWindow.Title
		}
		log.Printf("overlay_query: session=%s query=%q win=%s", req.SessionID, q.Query, winTitle)

		sess := loadSession(req.SessionID)
		provider, err := rtr.SelectProvider(req.ForceLocal)
		if err != nil {
			enc.Encode(protocol.Response{Type: "error", Content: err.Error()})
			enc.Encode(protocol.Response{Type: "done"})
			return
		}

		msgs := buildOverlayMessages(q, sess)
		textCh, err := provider.Complete(context.Background(), msgs)
		if err != nil {
			enc.Encode(protocol.Response{Type: "error", Content: err.Error()})
			enc.Encode(protocol.Response{Type: "done"})
			return
		}

		// Buffer full response so we can parse TOOL_CALL lines before sending text.
		var rawBuf strings.Builder
		for chunk := range textCh {
			rawBuf.WriteString(chunk)
		}
		raw := rawBuf.String()

		// Resolve active window ID for tool execution.
		activeWinID := ""
		if q.ActiveWindow != nil {
			activeWinID = q.ActiveWindow.WinID
		}

		// Separate TOOL_CALL lines from display text; execute tools in order.
		var userText strings.Builder
		for _, line := range strings.Split(raw, "\n") {
			trimmed := strings.TrimSpace(line)
			if strings.HasPrefix(trimmed, "TOOL_CALL:") {
				jsonStr := strings.TrimSpace(strings.TrimPrefix(trimmed, "TOOL_CALL:"))
				status := executeWindowTool(jsonStr, activeWinID)
				log.Printf("tool_call: %s → %s", jsonStr, status)
			} else {
				userText.WriteString(line + "\n")
			}
		}

		reply := strings.TrimSpace(userText.String())
		if reply != "" {
			enc.Encode(protocol.Response{Type: "text", Content: reply})
		}
		enc.Encode(protocol.Response{Type: "done"})

		sess.AddExchange(q.Query, reply)
		if err := sess.SaveCache(); err != nil {
			log.Printf("session save error: %v", err)
		}
		go sess.AppendHistory(time.Now().UTC(), q.Query, reply, "")
	}

	if err := socket.Serve(sock, onQuery, onExec, onLLM, onAgent, onSession, onShell, onOverlay); err != nil {
		log.Fatalf("socket error: %v", err)
	}
}
