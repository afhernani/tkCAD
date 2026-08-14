
from ...core import Command, CommandResult

class HelpCommand(Command):
    name = "AYUDA"
    aliases = ("HELP", "COMANDOS", "?")

    def start(self, ctx):
        ctx.write("Comandos disponibles:")

        if hasattr(ctx, "get_command_help"):
            for name, aliases in ctx.get_command_help():
                if aliases:
                    ctx.write(f"  {name}  ({', '.join(aliases)})")
                else:
                    ctx.write(f"  {name}")

        elif hasattr(ctx, "get_command_names"):
            for name in ctx.get_command_names():
                ctx.write(f"  {name}")

        ctx.write("Pulsa Tab para autocompletar.")

        return CommandResult.FINISHED

    def handle_input(self, ctx, text: str) -> CommandResult:
        return CommandResult.FINISHED