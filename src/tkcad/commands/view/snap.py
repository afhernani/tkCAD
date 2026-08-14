# snap.py

from ...core import Command, CommandResult, parse_number
# from ...geometry import


SNAP_MODE_ALIASES = {
    "GRID": "GRID",
    "MALLA": "GRID",
    "G": "GRID",

    "PUNTO": "POINT",
    "PUNTOS": "POINT",
    "POINT": "POINT",
    "PT": "POINT",

    "EXTREMO": "ENDPOINT",
    "EXTREMOS": "ENDPOINT",
    "EXT": "ENDPOINT",
    "ENDPOINT": "ENDPOINT",

    "MEDIO": "MIDPOINT",
    "PUNTOMEDIO": "MIDPOINT",
    "MIDPOINT": "MIDPOINT",
    "MID": "MIDPOINT",

    "INTERSECCION": "INTERSECTION",
    "INTERSECCIONES": "INTERSECTION",
    "INT": "INTERSECTION",
    "INTERSECTION": "INTERSECTION",

    "ORTO": "ORTHO",
    "ORTOGONAL": "ORTHO",
    "ORTHO": "ORTHO",
}


SNAP_MODE_DISPLAY = {
    "GRID": "GRID",
    "POINT": "PUNTO",
    "ENDPOINT": "EXTREMO",
    "MIDPOINT": "MEDIO",
    "INTERSECTION": "INTERSECCION",
    "ORTHO": "ORTO",
}


SNAP_COMMAND_OPTIONS = [
    "GRID",
    "PUNTO",
    "EXTREMO",
    "MEDIO",
    "INTERSECCION",
    "ORTO",
    "TODO",
    "NADA",
]


class SnapCommand(Command):
    name = "SNAP"
    aliases = ("SN", "SNA")

    def start(self, ctx):
        active = ctx.get_snap_modes()

        active_text = ", ".join(
            SNAP_MODE_DISPLAY.get(mode, mode)
            for mode in active
        )

        if not active_text:
            active_text = "NADA"

        ctx.write(f"Snap activos: {active_text}")

        ctx.write(
            "Opciones: GRID, PUNTO, EXTREMO, MEDIO, "
            "INTERSECCION, ORTO, TODO, NADA"
        )

        ctx.write(
            "Escribe un número para cambiar el tamaño de la malla."
        )

        ctx.prompt("Snap [Enter para terminar]:")

        return None

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        if not text:
            ctx.write("Comando SNAP terminado.")
            return CommandResult.FINISHED

        if text.upper() == "ESC":
            ctx.write("Comando SNAP cancelado.")
            return CommandResult.FINISHED

        # ----------------------------------------------------
        # Si escribe un número, cambiar tamaño de malla
        # ----------------------------------------------------
        try:
            grid_size = parse_number(text)

            ctx.set_grid_size(grid_size)

            ctx.write(f"Tamaño de malla: {ctx.grid_size}")

            ctx.prompt("Snap [Enter para terminar]:")

            return CommandResult.RUNNING

        except ValueError:
            pass

        option = text.upper()

        # ----------------------------------------------------
        # Activar todo
        # ----------------------------------------------------
        if option in {"TODO", "ALL"}:
            ctx.set_all_snap_modes()

            ctx.write("Todos los snaps activados.")

            active = ctx.get_snap_modes()

            active_text = ", ".join(
                SNAP_MODE_DISPLAY.get(mode, mode)
                for mode in active
            )

            ctx.write(f"Snap activos: {active_text}")

            ctx.prompt("Snap [Enter para terminar]:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Desactivar todo
        # ----------------------------------------------------
        if option in {"NADA", "NONE", "OFF"}:
            ctx.clear_snap_modes()

            ctx.write("Todos los snaps desactivados.")

            ctx.prompt("Snap [Enter para terminar]:")

            return CommandResult.RUNNING

        # ----------------------------------------------------
        # Alternar un modo
        # ----------------------------------------------------
        mode = SNAP_MODE_ALIASES.get(option)

        if mode is not None:
            active = ctx.toggle_snap_mode(mode)

            state_text = "activado" if active else "desactivado"

            ctx.write(f"Snap {SNAP_MODE_DISPLAY.get(mode, mode)} {state_text}.")

            active_modes = ctx.get_snap_modes()

            active_text = ", ".join(
                SNAP_MODE_DISPLAY.get(m, m)
                for m in active_modes
            )

            if not active_text:
                active_text = "NADA"

            ctx.write(f"Snap activos: {active_text}")

            ctx.prompt("Snap [Enter para terminar]:")

            return CommandResult.RUNNING

        ctx.write("Opción no válida.")

        ctx.prompt("Snap [Enter para terminar]:")

        return CommandResult.RUNNING

    def get_completions(self, ctx, text: str):
        text = text.upper()

        return [
            option
            for option in SNAP_COMMAND_OPTIONS
            if option.startswith(text)
        ]

class GridCommand(Command):
    name = "MALLA"
    aliases = ("GRID",)

    def start(self, ctx):
        active = ctx.toggle_snap_mode("GRID")

        if active:
            ctx.write("Malla / snap a malla activado.")
        else:
            ctx.write("Malla / snap a malla desactivado.")

        return CommandResult.FINISHED

    def handle_input(self, ctx, text: str) -> CommandResult:
        return CommandResult.FINISHED


class ShowGridCommand(Command):
    name = "VERMALLA"
    aliases = ("VERGRID",)

    def start(self, ctx):
        active = ctx.toggle_show_grid()

        if active:
            ctx.write("Malla visible: activada.")
        else:
            ctx.write("Malla visible: desactivada.")

        return CommandResult.FINISHED

    def handle_input(self, ctx, text: str) -> CommandResult:
        return CommandResult.FINISHED