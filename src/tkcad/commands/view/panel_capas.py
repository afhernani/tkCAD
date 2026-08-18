from ...core import Command, CommandResult


class PanelCapasCommand(Command):
    name = "PANELCAPAS"
    aliases = ("PANEL", "PCAPAS")

    def start(self, ctx):
        visible = ctx.toggle_layer_panel()
        ctx.write(f"Panel de capas {'visible' if visible else 'oculto'}.")
        return CommandResult.FINISHED