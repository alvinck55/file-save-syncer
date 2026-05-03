import typer

app = typer.Typer(name="windrose", help="Sync Windrose game saves to Google Drive.")

from windrose.cli import (  # noqa: E402, F401
    init_cmd,
    join_cmd,
    invite_cmd,
    launch_cmd,
    push_cmd,
    pull_cmd,
    status_cmd,
    set_save_cmd,
    set_mods_cmd,
    add_world_cmd,
    list_worlds_cmd,
)

app.command("init")(init_cmd.init)
app.command("join")(join_cmd.join)
app.command("invite")(invite_cmd.invite)
app.command("launch")(launch_cmd.launch)
app.command("push")(push_cmd.push)
app.command("pull")(pull_cmd.pull)
app.command("status")(status_cmd.status)
app.command("set-save")(set_save_cmd.set_save)
app.command("set-mods")(set_mods_cmd.set_mods)
app.command("add-world")(add_world_cmd.add_world)
app.command("list-worlds")(list_worlds_cmd.list_worlds)
