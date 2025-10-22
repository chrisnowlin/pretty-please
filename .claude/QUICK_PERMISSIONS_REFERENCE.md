# Quick Permissions Reference

## Current Status ✅
**Mode**: `acceptEdits` - Auto-approve file edits, ask for risky bash commands

## Quick Mode Changes

### Edit `.claude/settings.local.json`:

```json
// For automatic file editing (RECOMMENDED - CURRENT)
"defaultMode": "acceptEdits"

// For complete bypass - NO PROMPTS (USE WITH CAUTION)
"defaultMode": "bypassPermissions"

// For read-only - SAFE EXPLORATION
"defaultMode": "plan"

// For maximum control - ASK FOR EVERYTHING
"defaultMode": "normal"
```

## Keyboard Shortcut in VSCode
Press **Shift+Tab** to cycle through modes in your Claude Code session

## What's Auto-Approved Right Now?
✅ File reads (Read tool)
✅ File edits (Edit tool)
✅ File writes (Write tool)
✅ Pre-whitelisted git commands

## What Still Needs Approval?
⚠️ Bash commands not in whitelist
⚠️ Destructive git operations
⚠️ System-level commands

## To Add More Pre-Approved Commands
Add to `"allow"` array in `.claude/settings.local.json`:
```json
"allow": [
  "Bash(npm run build)",
  "Bash(pytest tests/)",
  "Bash(git log --oneline)"
]
```

## To Block Sensitive Files
Add to `"deny"` array in `.claude/settings.local.json`:
```json
"deny": [
  "Read(./.env)",
  "Read(./secrets/**)"
]
```

---

**For full details**: See `PERMISSIONS_CONFIG.md`
