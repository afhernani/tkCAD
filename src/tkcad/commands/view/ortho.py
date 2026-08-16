from ...core import Command, CommandResult


class OrthoCommand(Command):
    name = "ORTHO"
    aliases = ("ORT", "F8")

    def start(self, ctx):
        ctx.toggle_ortho()
        return CommandResult.FINISHED