from ...core import Command, CommandResult

class ExitCommand(Command):
    name = "EXIT"
    aliases = ("SALIR", "QUIT", "X")

    def start(self, ctx):
        ctx.write("Saliendo de la aplicación...")

        if hasattr(ctx, "exit_app"):
            ctx.exit_app()

        return CommandResult.FINISHED

    def handle_input(self, ctx, text: str) -> CommandResult:
        ctx.request_exit()
        return CommandResult.FINISHED