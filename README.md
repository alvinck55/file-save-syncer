# windrose-tool

Automatically syncs your Windrose game save to Google Drive before and after each play session, so your whole group shares a single world. Supports multiple worlds (e.g. a vanilla save and a modded save) in the same config.

**How it works:**
1. You run `windrose-save-sync launch` instead of launching the game directly
2. The tool pulls the latest save from Google Drive
3. Your game launches normally (Steam must already be running)
4. A tray icon appears — right-click to push mid-session if needed
5. When you close the game, the save is automatically pushed back to Drive

---

## Requirements

- Python 3.9+
- Steam running in the background (you must be logged in)
- A Google account

---

## Installation

```bash
pip install -e .
```

Or if you're using a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

pip install -e .
```

---

## First-time setup

### Host (first player — sets up the shared Drive folder)

Run the setup wizard once:

```bash
windrose-save-sync init
```

You'll be prompted for:

| Prompt | Example |
|---|---|
| Game name | `Windrose` |
| Name for your first world | `main` |
| Path to save file or folder | `C:\Users\you\AppData\Local\R5\Saved\SaveProfiles\...\Worlds` |
| Track and sync mods? | `y` / `n` |
| Mod directory (if yes) | auto-detected or enter path |
| Mod sync mode (if yes) | `1` manifest only, `2` upload/download |
| Google Drive folder name | `windrose-saves` |

A browser window will open for Google sign-in. After you approve, the tool saves your credentials locally and creates the Drive folder.

---

## Playing

Make sure Steam is running, then:

```bash
windrose-save-sync launch
```

If you have more than one world configured, pass `--world`:

```bash
windrose-save-sync launch --world modded
```

This will:
- Pull the latest save for that world from Google Drive
- Launch the game
- Show a tray icon in your system tray (bottom-right on Windows)
- Wait for you to close the game
- Push your updated save back to Drive

### Mid-session sync

Right-click the tray icon while the game is running:

```
● windrose-save-sync
  ─────────────────────
  Last sync: 5m ago (pull)

  Push save now
  Pull save now
```

**Push save now** — uploads your current save to Drive without closing the game. Useful for handing off the world to another player mid-session.

**Pull save now** — downloads the Drive save over your local save. You'll be asked to confirm since this overwrites your current progress.

---

## Multiple worlds

You can keep multiple separate save paths in sync — for example a vanilla playthrough and a modded one. Each world has its own Drive file and is synced independently.

### Add a world

```bash
windrose-save-sync add-world modded "C:\Users\you\AppData\Local\R5\Saved\SaveProfiles\...\Worlds"
```

The path can be a single file or an entire folder. Folders are zipped on upload and extracted on download, preserving the full directory structure.

After confirming the path, you'll be prompted whether to enable mod sync for this world (see [Mod sync](#mod-sync) below).

### List all worlds

```bash
windrose-save-sync list-worlds
```

```
 Name    Type       Save path                          Drive file ID
 main    directory  C:\...\Saves                       1abc...
 modded  directory  C:\...\ModdedSaves                 (not yet synced)
```

### Launch, push, or pull a specific world

```bash
windrose-save-sync launch --world modded
windrose-save-sync push   --world modded
windrose-save-sync pull   --world main
```

If you only have one world, the `--world` flag is optional and the single world is used automatically. With multiple worlds, omitting the flag will prompt you to choose.

### Change a world's save path

```bash
windrose-save-sync set-save "C:\new\path\to\saves" --world main
```

This updates the save path and clears the cached Drive file ID so the next push uploads fresh.

---

## Mod sync

Windrose mods are `.pak` / `.ucas` / `.utoc` files installed in:

```
<game_dir>\R5\Content\Paks\~mods\
```

Because all players in a co-op session must have the exact same mods installed, windrose-tool can track and optionally distribute them automatically.

### Sync modes

| Mode | What it does |
|---|---|
| `off` | No mod tracking (default if you skip the prompt) |
| `manifest_only` | Records which mods are needed on push. Warns you of missing mods on pull — you install them manually from Nexus Mods. |
| `upload_download` | Uploads your `.pak`/`.ucas`/`.utoc` files to Drive on push. Downloads and installs them automatically on pull. |

### Merge vs replace on pull

When `upload_download` installs mods from Drive, it uses one of two strategies:

- **merge** (default) — copies incoming mod files into `~mods` without deleting anything already there. Since extra mods generally don't prevent a world from loading, having a superset of all your group's mods is safe and lets you maintain multiple worlds without manual cleanup.
- **replace** — wipes `~mods` first, then extracts only what's in the Drive zip. Use this only if you need a perfectly clean mod environment; it can break other worlds that depend on mods that get removed.

Set `mod_pull_strategy = "replace"` in `config.toml` to opt in.

### What's not automatic

- **Mod install for manifest_only mode** — the tool prints which `.pak` files are missing; you install them from [Nexus Mods](https://www.nexusmods.com/windrose) yourself.
- **Mod version numbers** — `.pak` files have no embedded version metadata; the tool fingerprints files by SHA-256 hash and will flag any changed files on pull.
- **World-generation mods** — if a world was created with a terrain mod, that mod must stay installed permanently or the world won't load. This applies regardless of sync mode.

---

## Manual commands

```bash
windrose-save-sync push    # upload local save to Drive right now
windrose-save-sync pull    # download latest save from Drive right now
windrose-save-sync status  # show last sync time and direction for all worlds
```

All three accept `--world <name>` when you have multiple worlds.

---

## Multiplayer handoff workflow

Since this is last-write-wins, coordinate with your group about who is actively playing:

1. **Adding a new player:** host runs `windrose-save-sync invite theirmail@gmail.com`, they run `windrose-save-sync join <folder-id>`
2. **Before you play:** run `windrose-save-sync launch` — it pulls automatically
3. **When you're done:** close the game — it pushes automatically
4. **Handing off mid-session:** right-click tray → **Push save now**, then tell the next player it's ready
5. **If someone else pushed while you're mid-session:** right-click tray → **Pull save now** (confirm the overwrite)

> Only one person should be playing a given world at a time. Two simultaneous sessions will result in one player's progress being overwritten.

---

## Config file

Your configuration lives at `~/.windrose/config.toml`:

```toml
[game]
name = "Windrose"
steam_app_id = "3041230"
process_name = "Windrose.exe"

[drive]
folder_id = "1BxiM..."
folder_name = "windrose-saves"

[[worlds]]
name = "main"
save_path = "C:\\Users\\you\\AppData\\Local\\R5\\Saved\\SaveProfiles\\...\\Worlds"
save_type = "directory"
drive_file_id = "1abc..."

[[worlds]]
name = "modded"
save_path = "C:\\Users\\you\\AppData\\Local\\R5\\Saved\\SaveProfiles\\...\\Worlds"
save_type = "directory"
mod_dir = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Windrose\\R5\\Content\\Paks\\~mods"
mod_sync = "upload_download"   # "off" | "manifest_only" | "upload_download"
mod_pull_strategy = "merge"    # "merge" | "replace"
```

> **Upgrading from an older version?** Configs with the old `save_path`/`save_type` fields under `[game]` are automatically migrated to a single world named `main` on the next run. No manual changes needed.

### Inviting other players

The host invites each player by their Gmail address:

```bash
windrose-save-sync invite friend@gmail.com
```

This grants them access to the shared Drive folder and sends them an email from Google with instructions. The command also prints the folder ID they'll need:

```
Invited friend@gmail.com — they'll receive an email from Google.
Tell them to run: windrose-save-sync join 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
```

### Everyone else (joining an existing shared world)

Once invited, each player runs the join command with the folder ID the host provided:

```bash
windrose-save-sync join 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
```

You'll be prompted for your save path, then asked to sign in with Google. The tool verifies folder access before saving your config.

---

## Files stored locally

All windrose files are in `~/.windrose/`:

| File | Purpose |
|---|---|
| `config.toml` | Your game, Drive, and worlds configuration |
| `token.json` | Your Google auth token (managed automatically) |
| `state.json` | Last sync time and status per world |

---

## Troubleshooting

**`windrose-save-sync launch` says "No config found"**
Run `windrose-save-sync init` first.

**Browser doesn't open during `windrose-save-sync init`**
Manually navigate to the URL printed in the terminal to complete OAuth.

**Game fails to start**
Make sure Steam is running and you're logged in before running `windrose-save-sync launch`.

**"Auth token expired" error**
Delete `~/.windrose/token.json` and re-run `windrose-save-sync init` to re-authenticate.

**Push failed / Drive unreachable**
Check your internet connection. Run `windrose-save-sync push` manually once you're back online.

---

## Developer setup

> This section is only for the person maintaining and distributing the tool — not for players.

The file `src/windrose/data/client_secret.json` is a placeholder. Before distributing the tool you must replace it with real GCP credentials:

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project, enable the **Google Drive API**
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
4. Choose **Desktop app**, download the JSON
5. Replace `src/windrose/data/client_secret.json` with the downloaded file

Players who install the tool will use these credentials automatically — they only need to sign in with their own Google account.
