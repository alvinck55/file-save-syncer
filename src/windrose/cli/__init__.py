import typer

app = typer.Typer(name="windrose", help="Sync Windrose game saves to Google Drive.")

from windrose.cli import init_cmd, join_cmd, invite_cmd, launch_cmd, push_cmd, pull_cmd, status_cmd  # noqa: E402, F401

app.command("init")(init_cmd.init)
app.command("join")(join_cmd.join)
app.command("invite")(invite_cmd.invite)
app.command("launch")(launch_cmd.launch)
app.command("push")(push_cmd.push)
app.command("pull")(pull_cmd.pull)
app.command("status")(status_cmd.status)
