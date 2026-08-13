# seleccion.py

from core import (
    Command,
    CommandResult,
    parse_kind
)

class SelectCommand(Command):
    name = "SELECCIONAR"
    aliases = ("SEL", "S")

    def start(self, ctx):
        ctx.write("Opciones: TODO, NADA, ULTIMO, VEMTAMA, tipo (LINEA, CIRCULO...) o IDs: 1,2,3")
        ctx.prompt("Selección:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write(f"Entidades seleccionadas: {ctx.selection_count()}")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando SELECCIONAR cancelado.")
            return CommandResult.FINISHED

        option = text.upper()

        # Seleccionar todo
        if option in {"TODO", "T", "ALL"}:
            ctx.select_all()
            ctx.write(f"Seleccionadas: {ctx.selection_count()}")
            return CommandResult.FINISHED

        # Quitar selección
        if option in {"NADA", "NONE", "CLEAR", "0"}:
            ctx.clear_selection()
            ctx.write("Selección borrada.")
            return CommandResult.FINISHED

        # Seleccionar última entidad
        if option in {"ULTIMO", "ULTIMA", "U", "LAST"}:
            ctx.select_last()
            ctx.write(f"Seleccionadas: {ctx.selection_count()}")
            return CommandResult.FINISHED

        # VENTANA 
        if option in {"VENTANA", "V"}:
            ctx.write("Selección por ventana con el ratón:")
            ctx.write("  Izquierda -> derecha: selecciona lo completamente dentro.")
            ctx.write("  Derecha -> izquierda: selecciona lo que toca/cruza.")
            ctx.write("  Shift + arrastrar añade.")
            ctx.write("  Ctrl + arrastrar quita.")
            ctx.prompt("Selección [Enter para terminar]:")
            return CommandResult.RUNNING

        # Seleccionar por tipo
        kind = parse_kind(option)

        if kind is not None:
            ctx.select_kind(kind)
            return CommandResult.FINISHED

        # Seleccionar por IDs: 1,2,3 o 1;2;3
        parts = [
            part.strip()
            for part in text.replace(";", ",").split(",")
            if part.strip()
        ]

        if parts and all(part.isdigit() for part in parts):
            changed = False

            for part in parts:
                entity_id = int(part)

                if ctx.toggle_selection(entity_id, redraw=False):
                    changed = True
                    entity = ctx.get_entity_by_id(entity_id)

                    state_text = "seleccionada" if entity.selected else "deseleccionada"
                    ctx.write(f"Entidad {entity_id} {state_text}.")
                else:
                    ctx.write(f"No existe la entidad {entity_id}.")

            if changed:
                ctx.redraw()

            ctx.write(f"Total seleccionadas: {ctx.selection_count()}")
            ctx.prompt("Selección [Enter para terminar]:")

            return CommandResult.RUNNING

        ctx.write("Opción no válida.")
        ctx.prompt("Selección [TODO/NADA/ULTIMO/tipo/IDs]:")

        return CommandResult.RUNNING

class ListCommand(Command):
    name = "LISTAR"
    aliases = ("LIST", "ENTIDADES")

    def start(self, ctx):
        if not ctx.entities:
            ctx.write("No hay entidades.")
            return CommandResult.FINISHED

        ctx.write("Entidades:")

        for entity in ctx.entities:
            mark = "*" if entity.selected else " "
            ctx.write(f" {mark} [{entity.id}] {entity.kind.upper()}")

        return CommandResult.FINISHED

    def handle_input(self, ctx, text: str) -> CommandResult:
        return CommandResult.FINISHED