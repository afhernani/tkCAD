from ...core import Command, CommandResult


class BloqueCommand(Command):
    name = "BLOQUE"
    aliases = ("BLOCK", "GRUPO")

    def __init__(self):
        self.ids = []

    def start(self, ctx):
        self.ids = [e.id for e in ctx.get_selected_entities()]
        if not self.ids:
            ctx.write("BLOQUE: selecciona entidades antes de usar el comando.")
            return CommandResult.FINISHED
        default = f"BLOQUE_{len(ctx.block_names) + 1}"
        ctx.prompt(f"Nombre del bloque <{default}>:")
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if text.upper() == "ESC":
            ctx.write("Comando BLOQUE cancelado.")
            return CommandResult.FINISHED

        default = f"BLOQUE_{len(ctx.block_names) + 1}"
        name = text if text else default

        if name in ctx.block_names.values():
            ctx.write("Ya existe un bloque con ese nombre. Elige otro.")
            return CommandResult.RUNNING

        ctx.make_block(self.ids, name)
        ctx.write(f"Bloque '{name}' creado con {len(self.ids)} entidades.")
        return CommandResult.FINISHED