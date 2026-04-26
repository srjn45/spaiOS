# Notion Setup Guide

spaiOS uses Notion as the human-readable mirror of the repo docs. Claude reads from repo markdown; humans read from Notion. Both must stay in sync.

---

## Step 1: Create a Notion Integration

1. Go to https://www.notion.so/profile/integrations
2. Click "New integration"
3. Name it "spaiOS Claude Sync"
4. Type: Internal
5. Capabilities: Read content, Update content, Insert content
6. Click Save
7. Copy the **Internal Integration Secret** (starts with `secret_...`)

---

## Step 2: Configure Claude Code MCP

Add the Notion MCP server to Claude Code's config.

Edit `~/.claude.json` (or create if it doesn't exist):
```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "OPENAPI_MCP_HEADERS": "{\"Authorization\": \"Bearer YOUR_SECRET_HERE\", \"Notion-Version\": \"2022-06-28\"}"
      }
    }
  }
}
```

Replace `YOUR_SECRET_HERE` with the integration secret from Step 1.

Restart Claude Code after editing.

---

## Step 3: Create the spaiOS Notion Space

In Notion:
1. Create a new **page** at the top level of your workspace called "spaiOS"
2. Share it with your integration: open the page → Share → search "spaiOS Claude Sync" → Invite
3. Create the following subpages (Claude will populate them):

```
spaiOS (root page)
├── Project Overview
├── Design Specification
├── Phases
│   ├── Phase 1: The Spark
│   ├── Phase 2: The Reach
│   ├── Phase 3: The Shell
│   └── Phase 4: The Nervous System
├── RFCs
│   ├── RFC-001: Architecture
│   ├── RFC-002: Tech Stack
│   ├── RFC-003: Phase Structure
│   ├── RFC-004: Kernel Integration
│   └── RFC-005: Interaction Model
├── Task Board (database — kanban view)
│   Properties: Name, Status (Backlog/In Progress/Done), Phase, Session Date
└── Session Log (database — table view)
    Properties: Date, Summary, Phase, Tasks Completed, Next Session
```

---

## Step 4: Get Page IDs

For each page above, get its ID from the URL:
`https://notion.so/spaiOS-PROJECT-OVERVIEW-<PAGE_ID>`

The ID is the last 32 characters (with hyphens removed format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).

Store them in `docs/notion-map.json` (this file is gitignored):
```json
{
  "root": "PAGE_ID_HERE",
  "design_spec": "PAGE_ID_HERE",
  "phase_1": "PAGE_ID_HERE",
  "phase_2": "PAGE_ID_HERE",
  "phase_3": "PAGE_ID_HERE",
  "phase_4": "PAGE_ID_HERE",
  "rfc_001": "PAGE_ID_HERE",
  "rfc_002": "PAGE_ID_HERE",
  "rfc_003": "PAGE_ID_HERE",
  "rfc_004": "PAGE_ID_HERE",
  "rfc_005": "PAGE_ID_HERE",
  "task_board_db": "DATABASE_ID_HERE",
  "session_log_db": "DATABASE_ID_HERE"
}
```

---

## Step 5: Initial Sync

Once MCP is configured and `notion-map.json` is populated, tell Claude:
> "Sync all docs to Notion"

Claude will read each markdown file in `docs/` and push content to the corresponding Notion page.

---

## Ongoing Sync

At the end of any session where `docs/` files changed, Claude will:
1. Identify which docs changed (via git diff)
2. Read the updated markdown
3. Push to the corresponding Notion page using the MCP tools
4. Confirm sync complete in the session summary

This keeps Notion current without manual copy-paste.
