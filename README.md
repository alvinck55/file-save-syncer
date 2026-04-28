# windrose-tool

Automatically syncs your Windrose game save to Google Drive before and after each play session, so your whole group shares a single world.

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
| Path to game executable | `C:\Program Files\Steam\steamapps\common\Windrose\Windrose.exe` |
| Path to save file or folder | `C:\Users\you\AppData\LocalLow\Windrose\Saves` |
| Path to client_secret.json | `C:\Users\you\Downloads\client_secret_xxx.json` |
| Google Drive folder name | `windrose-saves` |

A browser window will open for Google sign-in. After you approve, the tool saves your credentials locally and creates the Drive folder.

---

## Playing

Make sure Steam is running, then:

```bash
windrose launch
```

This will:
- Pull the latest world save from Google Drive
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

## Manual commands

You can also sync without launching the game:

```bash
windrose push    # upload local save to Drive right now
windrose pull    # download latest save from Drive right now
windrose status  # show last sync time and direction
```

---

## Multiplayer handoff workflow

Since this is last-write-wins, coordinate with your group about who is actively playing:

1. **Adding a new player:** host runs `windrose invite theirmail@gmail.com`, they run `windrose join <folder-id>`
2. **Before you play:** run `windrose launch` — it pulls automatically
3. **When you're done:** close the game — it pushes automatically
4. **Handing off mid-session:** right-click tray → **Push save now**, then tell the next player it's ready
5. **If someone else pushed while you're mid-session:** right-click tray → **Pull save now** (confirm the overwrite)

> Only one person should be playing at a time. Two simultaneous sessions will result in one player's progress being overwritten.

---

## Config file

Your configuration lives at `~/.windrose/config.toml`:

```toml
[game]
name = "Windrose"
exe_path = "C:\\Program Files\\Steam\\steamapps\\common\\Windrose\\Windrose.exe"
save_path = "C:\\Users\\you\\AppData\\LocalLow\\Windrose\\Saves"
save_type = "directory"

[drive]
folder_id = "1BxiM..."
folder_name = "windrose-saves"
file_id = "1abc..."
```

To change the save path or executable, edit this file directly or re-run `windrose init`.

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

You'll be prompted for your game exe path and save path, then asked to sign in with Google. The tool verifies folder access before saving your config.

---

## Files stored locally

All windrose files are in `~/.windrose/`:

| File | Purpose |
|---|---|
| `config.toml` | Your game and Drive configuration |
| `token.json` | Your Google auth token (managed automatically) |
| `state.json` | Last sync time and status |

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
