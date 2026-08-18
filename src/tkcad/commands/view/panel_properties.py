from ...core import Command, CommandResult


class PanelPropiedadesCommand(Command):
    name = "PANELPROPIEDADES"
    aliases = ("PROP", "PPROP")

    def start(self, ctx):
        visible = ctx.toggle_properties_panel()
        ctx.write(f"Panel de propiedades {'visible' if visible else 'oculto'}.")
        return CommandResult.FINISHED