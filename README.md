# windrose-tool

Automatically syncs your Windrose game save to Google Drive before and after each play session, so your whole group shares a single world. Supports multiple worlds (e.g. a vanilla save and a modded save) in the same config.

**How it works:**
1. You run `windrose launch` instead of launching the game directly
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
windrose init
```

You'll be prompted for:

| Prompt | Example |
|---|---|
| Game name | `Windrose` |
| Name for your first world | `main` |
| Path to save file or folder | `C:\Users\you\AppData\LocalLow\Windrose\Saves` |
| Google Drive folder name | `windrose-saves` |

A browser window will open for Google sign-in. After you approve, the tool saves your credentials locally and creates the Drive folder.

---

## Playing

Make sure Steam is running, then:

```bash
windrose launch
```

If you have more than one world configured, pass `--world`:

```bash
windrose launch --world modded
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
● windrose
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
windrose add-world modded "C:\Users\you\AppData\LocalLow\Windrose\ModdedSaves"
```

The path can be a single file or an entire folder. Folders are zipped on upload and extracted on download, preserving the full directory structure.

### List all worlds

```bash
windrose list-worlds
```

```
 Name    Type       Save path                          Drive file ID
 main    directory  C:\...\Saves                       1abc...
 modded  directory  C:\...\ModdedSaves                 (not yet synced)
```

### Launch, push, or pull a specific world

```bash
windrose launch --world modded
windrose push   --world modded
windrose pull   --world main
```

If you only have one world, the `--world` flag is optional and the single world is used automatically. With multiple worlds, omitting the flag will prompt you to choose.

### Change a world's save path

```bash
windrose set-save "C:\new\path\to\saves" --world main
```

This updates the save path and clears the cached Drive file ID so the next push uploads fresh.

---

## Manual commands

```bash
windrose push    # upload local save to Drive right now
windrose pull    # download latest save from Drive right now
windrose status  # show last sync time and direction for all worlds
```

All three accept `--world <name>` when you have multiple worlds.

---

## Multiplayer handoff workflow

Since this is last-write-wins, coordinate with your group about who is actively playing:

1. **Adding a new player:** host runs `windrose invite theirmail@gmail.com`, they run `windrose join <folder-id>`
2. **Before you play:** run `windrose launch` — it pulls automatically
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
save_path = "C:\\Users\\you\\AppData\\LocalLow\\Windrose\\Saves"
save_type = "directory"
drive_file_id = "1abc..."

[[worlds]]
name = "modded"
save_path = "C:\\Users\\you\\AppData\\LocalLow\\Windrose\\ModdedSaves"
save_type = "directory"
```

> **Upgrading from an older version?** Configs with the old `save_path`/`save_type` fields under `[game]` are automatically migrated to a single world named `main` on the next run. No manual changes needed.

### Inviting other players

The host invites each player by their Gmail address:

```bash
windrose invite friend@gmail.com
```

This grants them access to the shared Drive folder and sends them an email from Google with instructions. The command also prints the folder ID they'll need:

```
Invited friend@gmail.com — they'll receive an email from Google.
Tell them to run: windrose join 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
```

### Everyone else (joining an existing shared world)

Once invited, each player runs the join command with the folder ID the host provided:

```bash
windrose join 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
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

**`windrose launch` says "No config found"**
Run `windrose init` first.

**Browser doesn't open during `windrose init`**
Manually navigate to the URL printed in the terminal to complete OAuth.

**Game fails to start**
Make sure Steam is running and you're logged in before running `windrose launch`.

**"Auth token expired" error**
Delete `~/.windrose/token.json` and re-run `windrose init` to re-authenticate.

**Push failed / Drive unreachable**
Check your internet connection. Run `windrose push` manually once you're back online.

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
