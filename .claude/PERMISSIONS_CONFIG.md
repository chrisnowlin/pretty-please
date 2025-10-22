# Claude Code Permissions Configuration

This document explains the permissions setup for this project's VSCode Claude Code implementation.

## Current Configuration

**File**: `.claude/settings.local.json`

### Active Permission Mode: `acceptEdits`

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [...],
    "deny": [],
    "ask": []
  }
}
```

## What This Means

### ✅ Auto-Approved Operations
- **File Edits** (Edit tool) - Automatically applied
- **File Writes** (Write tool) - Automatically created/overwritten
- **File Reads** (Read tool) - Automatically executed
- **Most other tools** - Automatically used

### ⚠️ Still Requires Permission
- **Bash commands** not in the `allow` list (security safeguard)
- **Destructive git operations** (reset, force push, etc.)
- **System-level commands** requiring explicit approval

### Specific Pre-Approved Bash Commands
Your `allow` list includes specific git operations that Claude has previously used successfully:
- `git add` (specific files)
- `git commit` (with specific messages)
- Various compilation and testing commands

---

## Permission Modes Available

### 1. `acceptEdits` (Currently Active)
**Best for**: Productive work with safety guards

- Auto-approves all file modifications
- Still asks for dangerous bash commands
- Good balance of convenience and safety
- Recommended for most development

**Use this for**: Regular coding tasks, refactoring, documentation

### 2. `bypassPermissions`
**Best for**: Fully trusted workflows

- Skips ALL permission checks
- No prompts for anything
- Maximum convenience, lowest safety
- Use only when absolutely needed

**To activate**: Edit `.claude/settings.local.json`
```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

### 3. `plan`
**Best for**: Safe exploration

- Read-only mode - no modifications allowed
- Perfect for analyzing code without risk
- Great for understanding unfamiliar code

**To activate**: Edit `.claude/settings.local.json`
```json
{
  "permissions": {
    "defaultMode": "plan"
  }
}
```

### 4. `normal` (Default)
**Best for**: Maximum control

- Ask for permission on every potentially sensitive operation
- Detailed prompts for each action
- Most cautious mode

**To activate**: Edit `.claude/settings.local.json`
```json
{
  "permissions": {
    "defaultMode": "normal"
  }
}
```

---

## How to Switch Modes

### Option 1: Edit Settings File (Persistent)
Edit `.claude/settings.local.json` and change the `defaultMode` value:

```json
"defaultMode": "acceptEdits"  // current
"defaultMode": "bypassPermissions"  // full bypass
"defaultMode": "plan"  // read-only
"defaultMode": "normal"  // ask for everything
```

### Option 2: VSCode Keyboard Shortcut (Session Only)
While in Claude Code conversation:
- Press **Shift+Tab** to cycle through modes
  - 1st press: `acceptEdits`
  - 2nd press: `plan`
  - 3rd press: Back to previous mode

---

## Security Recommendations

### ✅ Safe to Keep as-is
- `acceptEdits` mode is fine for development
- Your `allow` list whitelists specific git operations
- Most risky operations still require confirmation

### ⚠️ Consider Adding Deny Rules
If you have sensitive files you want to protect:

```json
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./config/credentials.json)"
    ]
  }
}
```

### 🔒 For Production Deployments
- Use `plan` mode for safety
- Or create an enterprise `managed-settings.json`
- Restrict bash commands more aggressively

---

## Troubleshooting

### "Claude is asking for permission when I don't want it"
- Make sure `defaultMode` is set to `acceptEdits`
- Check that your `.claude/settings.local.json` is properly formatted JSON
- Restart Claude Code session

### "I want even fewer prompts"
- Change to `bypassPermissions` mode
- Warning: This skips safety checks entirely

### "I want more control back"
- Change to `normal` mode
- You'll be prompted for every sensitive operation

---

## File Locations

- **Project settings**: `.claude/settings.local.json` (not committed to git)
- **User settings**: `~/.claude/settings.json` (all projects)
- **Reference**: This file (`.claude/PERMISSIONS_CONFIG.md`)

---

## Next Steps

1. Test the current `acceptEdits` mode
2. Adjust if needed based on your workflow
3. Consider adding `deny` rules for sensitive files
4. Refer back to this guide when you need to switch modes

