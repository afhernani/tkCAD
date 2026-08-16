from ...core import Command, CommandResult


class UndoCommand(Command):
    name = "DESHACER"
    aliases = ("U", "UNDO")

    def start(self, ctx):
        if ctx.undo():
            ctx.write("Acción deshecha.")
        else:
            ctx.write("Nada que deshacer.")
        return CommandResult.FINISHED


class RedoCommand(Command):
    name = "REHACER"
    aliases = ("REDO",)

    def start(self, ctx):
        if ctx.redo():
            ctx.write("Acción rehecha.")
        else:
            ctx.write("Nada que rehacer.")
        return CommandResult.FINISHED