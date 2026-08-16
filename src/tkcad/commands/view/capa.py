from ...core import Command, CommandResult


class CapaCommand(Command):
    name = "CAPA"
    aliases = ("CAPAS", "LA")

    def start(self, ctx):
        self._write_status(ctx)
        self._prompt(ctx)

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()

        # Enter vacío o ESC: salir del gestor de capas
        if not text or text.upper() == "ESC":
            return CommandResult.FINISHED

        tokens = text.split()
        option = tokens[0].upper()

        if option == "ON" and len(tokens) >= 2:
            name = tokens[1]
            layer = ctx.get_layer(name)
            if layer is None:
                ctx.write(f"No existe la capa: {name}")
            elif not layer.visible:
                ctx.toggle_layer_visible(name)
                ctx.write(f"Capa {name} visible.")
            else:
                ctx.write(f"La capa {name} ya era visible.")

        elif option == "OFF" and len(tokens) >= 2:
            name = tokens[1]
            layer = ctx.get_layer(name)
            if layer is None:
                ctx.write(f"No existe la capa: {name}")
            elif layer.visible:
                ctx.toggle_layer_visible(name)
                ctx.write(f"Capa {name} oculta.")
            else:
                ctx.write(f"La capa {name} ya estaba oculta.")

        elif option == "COLOR" and len(tokens) >= 3:
            name, color = tokens[1], tokens[2]
            if ctx.set_layer_color(name, color):
                ctx.write(f"Color de la capa {name}: {color}")
            else:
                ctx.write(f"No existe la capa: {name}")

        elif option == "BLOQ" and len(tokens) >= 2:
            name = tokens[1]
            layer = ctx.get_layer(name)
            if layer is None:
                ctx.write(f"No existe la capa: {name}")
            elif not layer.locked:
                ctx.toggle_layer_locked(name)
                ctx.write(f"Capa {name} bloqueada.")
            else:
                ctx.write(f"La capa {name} ya estaba bloqueada.")

        elif option == "DESBLOQ" and len(tokens) >= 2:
            name = tokens[1]
            layer = ctx.get_layer(name)
            if layer is None:
                ctx.write(f"No existe la capa: {name}")
            elif layer.locked:
                ctx.toggle_layer_locked(name)
                ctx.write(f"Capa {name} desbloqueada.")
            else:
                ctx.write(f"La capa {name} ya estaba desbloqueada.")

        elif option == "DEL" and len(tokens) >= 2:
            name = tokens[1]
            if ctx.delete_layer(name):
                ctx.write(f"Capa {name} borrada.")
            else:
                ctx.write(
                    f"No se puede borrar la capa {name} "
                    "(es la 0, la actual o tiene entidades)."
                )

        else:
            # Cualquier otro texto = nombre de capa: crear si falta y cambiar.
            name = text
            if ctx.get_layer(name) is None:
                ctx.add_layer(name)
                ctx.write(f"Capa {name} creada.")
            ctx.set_current_layer(name)
            ctx.write(f"Capa actual: {name}")

        self._prompt(ctx)
        return CommandResult.RUNNING

    def _write_status(self, ctx):
        ctx.write(f"Capa actual: {ctx.current_layer}")
        for name in ctx.get_layer_names():
            layer = ctx.get_layer(name)
            estado = "visible" if layer.visible else "oculta"
            bloqueo = "bloqueada" if layer.locked else "libre"
            color = layer.color if layer.color else "por tipo"
            marca = " *" if name == ctx.current_layer else ""
            ctx.write(f"  {name}{marca} [{estado}, {bloqueo}] color={color}")

    def _prompt(self, ctx):
        ctx.prompt(
            "Capa [nombre / ON x / OFF x / COLOR x c / "
            "BLOQ x / DESBLOQ x / DEL x / Enter=salir]:"
        )

    def get_completions(self, ctx, text: str):
        text = text.upper()
        options = ["ON", "OFF", "COLOR", "BLOQ", "DESBLOQ", "DEL"]
        nombres = [name.upper() for name in ctx.get_layer_names()]
        return [
            candidate for candidate in options + nombres
            if candidate.startswith(text)
        ]