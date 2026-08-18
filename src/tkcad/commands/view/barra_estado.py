from ...core import Command, CommandResult


class BarraEstadoCommand(Command):
    name = "BARRAESTADO"
    aliases = ("STATUS", "BAR")

    def start(self, ctx):
        visible = ctx.toggle_statusbar()
        ctx.write(f"Barra de estado {'visible' if visible else 'oculta'}.")
        return CommandResult.FINISHED