# Task: E2E Browser Agent Validation

**Date:** 2026-05-01
**Phase:** Phase 2 — Milestone 2
**Session goal:** Manually validate all four new ChromeAgent tools end-to-end via voice commands, then mark Milestone 2 complete and plan Milestone 3.
**Notion task ID:** phase2_m2_chrome_app_control

## What We're Building

No new code this session — this is a validation gate. We test fill_form, click_link_by_text, get_tabs, and clear_history through the full voice → Orchestrator → ChromeAgent → CDP stack to confirm they work in real browser conditions.

## Approach

1. Launch Chrome with remote debugging enabled via `scripts/launch-chrome.sh`
2. Launch spaiOS in a second terminal
3. Test scenario A: fill_form — "fill in the search box with 'lo-fi beats' and submit"
4. Test scenario B: click_link_by_text — navigate to Google results, say "click the Wikipedia link"
5. Test scenario C: get_tabs — say "what tabs do I have open"
6. Test scenario D: age-gate — open an age-gated site, say "click the I am 18 button" (or similar)
7. If all pass: update Notion task to done, read phase doc, plan Milestone 3

## Files Touched

- No source changes expected — validation only
- `NEXT.md` — update at end of session

## Done When

- [ ] fill_form fills and submits a real search form without error
- [ ] click_link_by_text clicks a visible link by partial text match
- [ ] get_tabs returns correct tab URLs
- [ ] (bonus) clear_history executes without CDP error
- [ ] All results confirmed in terminal output, no Python exceptions
- [ ] Notion task marked done
- [ ] NEXT.md updated with Milestone 3 plan
