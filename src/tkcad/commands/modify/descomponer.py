from ...core import Command, CommandResult


class DescomponerCommand(Command):
    name = "DESCOMPONER"
    aliases = ("EXPLODE",)

    def __init__(self):
        self.ids = []
        self.n_blocks = 0

    def start(self, ctx):
        selected = ctx.get_selected_entities()
        if not selected:
            ctx.write("DESCOMPONER: no hay nada seleccionado.")
            return CommandResult.FINISHED

        blocks = {getattr(e, "block_id", None) for e in selected}
        blocks.discard(None)
        if not blocks:
            ctx.write("DESCOMPONER: la selección no contiene bloques.")
            return CommandResult.FINISHED

        self.ids = [e.id for e in selected]
        self.n_blocks = len(blocks)
        ctx.prompt(
            f"¿Descomponer {self.n_blocks} bloque(s)? "
            f"[Enter=confirmar / ESC=cancelar]:"
        )
        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        if text.strip().upper() == "ESC":
            ctx.write("DESCOMPONER cancelado.")
            return CommandResult.FINISHED

        n = ctx.explode_block(self.ids)
        ctx.write(f"Descompuestos {n} bloque(s).")
        return CommandResult.FINISHED