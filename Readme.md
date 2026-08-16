# tkCAD — Editor CAD 2D en Python y Tkinter

tkCAD es un editor de dibujo tipo CAD 2D construido con **Python** y **Tkinter**, con una ventana de comandos estilo CAD, entrada de puntos por teclado y ratón, snaps, selección por ventana, grips de edición y proyectos guardables en JSON.

![tkCAD](docs/screenshot.png)

---

## ✨ Características

- 🖱️ **Interfaz** con consola de comandos, canvas y grips interactivos
- 📐 **Dibujo**: línea, polilínea, círculo, arco, polígono, elipse
- 🛠️ **Edición**: mover, copiar, borrar, rotar, escalar, simetría, recortar, extender
- 🎯 **Snaps**: punto, extremo, punto medio, intersección, ortogonal, cuadrícula
- 📁 **Archivos**: guardar/cargar proyectos en JSON
- 🧠 **Autocompletado** con `Tab` y **historial** con flechas
- 🎨 **Vista previa progresiva** al dibujar polilíneas

## 📦 Instalación

### Requisitos

- [Pixi](https://pixi.sh/) instalado
- Windows 64-bit (otras plataformas con ajustes en `pixi.toml`)

### Pasos

```bash
# Clonar el repositorio

git clone https://github.com/TU_USUARIO/tkCAD.git
cd tkCAD

# Instalar el entorno (crea .pixi/ con todas las dependencias)

pixi install
```

---------

## 🚀 Uso

## Ejecutar la aplicación

```bash
pixi run app
```

Esto lanza la app con `python -m tkcad`. El paquete se instala en modo editable, así que cualquier cambio en `src/tkcad/` se refleja al instante sin reinstalar.

### Entrar al entorno interactivo

```bash
pixi shell
python -m tkcad
```

### Ejecutar los tests

```bash
pixi run test
```

---

## ⌨️ Ventana de comandos

Situada en la parte inferior de la aplicación:

- **Zona de salida**: muestra prompts, mensajes y resultados.
- **Campo de entrada**: donde se escriben comandos y datos.

Teclas especiales:

| Tecla     | Acción                            |
| --------- | --------------------------------- |
| `Enter`   | Enviar entrada / terminar comando |
| `Tab`     | Autocompletar comandos y opciones |
| `↑` / `↓` | Historial de entradas             |
| `Esc`     | Cancelar comando activo           |

---

## 🧰 Comandos disponibles

| Comando       | Alias                   | Descripción                                                                    |
| ------------- | ----------------------- | ------------------------------------------------------------------------------ |
| `LINEA`       | `L`, `LINE`             | Dibuja segmentos encadenados.                                                  |
| `POLILINEA`   | `PL`, `POLYLINE`        | Polilínea; `C` cierra, `Enter` termina.                                        |
| `CIRCULO`     | `C`, `CIRCLE`           | Centro + radio (número, `D` diámetro, punto o clic).                           |
| `ARCO`        | `A`, `ARC`              | Centro, punto inicial y punto final o ángulo incluido (`A`).                   |
| `POLIGONO`    | `POL`, `PG`             | Polígono regular: lados, centro y radio (o `@dist<ángulo` para rotación).      |
| `ELIPSE`      | `EL`, `ELLIPSE`         | Centro, extremo del primer eje y extremo del segundo eje.                      |
| `MOVER`       | `M`, `MOVE`, `MV`       | Mueve la selección (o un tipo) con punto base y destino.                       |
| `COPIAR`      | `CP`, `COPY`            | Copia la selección (o un tipo) con desplazamiento.                             |
| `BORRAR`      | `DEL`, `ERASE`, `D`     | Borra selección o tipo, con confirmación `[S/N]`.                              |
| `ROTAR`       | `R`, `ROTATE`, `RO`     | Rota la selección alrededor de un punto base.                                  |
| `ESCALAR`     | `ES`, `SCALE`, `SC`     | Escala la selección con factor positivo desde un punto base.                   |
| `SIMETRIA`    | `SIM`, `MIRROR`, `MI`   | Refleja la selección respecto a un eje de dos puntos.                          |
| `RECORTAR`    | `TR`, `TRIM`, `RT`      | Recorta una `LINEA` usando otra `LINEA` como límite (IDs + punto a conservar). |
| `EXTENDER`    | `EX`, `EXTEND`          | Extiende una `LINEA` hasta una `LINEA` límite (IDs).                           |
| `SELECCIONAR` | `SEL`, `S`              | `TODO`, `NADA`, `ULTIMO`, `VENTANA`, tipo o IDs (`1,2,3`).                     |
| `LISTAR`      | `LIST`, `ENTIDADES`     | Lista entidades con ID y marca de selección (`*`).                             |
| `AYUDA`       | `HELP`, `COMANDOS`, `?` | Muestra los comandos disponibles con alias.                                    |
| `EXIT`        | `SALIR`, `QUIT`, `X`    | Sale de la aplicación (global, funciona dentro de comandos).                   |
| `GUARDAR`     | `SAVE`, `G`             | Guarda el proyecto (archivo actual, ruta o diálogo).                           |
| `GUARDARCOMO` | `SAVEAS`, `GCOMO`       | Guarda en un archivo nuevo (diálogo o ruta).                                   |
| `ABRIR`       | `OPEN`, `O`, `ABR`      | Abre un proyecto JSON (con confirmación si hay entidades).                     |
| `NUEVO`       | `NEW`, `N`              | Crea un proyecto nuevo (con confirmación si hay entidades).                    |
| `SNAP`        | `SN`, `SNA`             | Activa/desactiva modos de snap y cambia el tamaño de malla (número).           |
| `MALLA`       | `GRID`                  | Activa/desactiva malla y snap a malla.                                         |
| `VERMALLA`    | `VERGRID`               | Muestra/oculta la malla en pantalla.                                           |
| `CAPA`        | `CAPAS`, `LA`           | Gestor de capas: crear, cambiar, ON/OFF, color, bloqueo                        |
| `ZOOM`        | `ZOOM`, `Z`             | Gestor de zoom: + , -, Todo, T/EXT, 2 (o 0.5, etc..)
                                                    |
| `ORTHO`       | `ORT`, `F8`             | Activa/desactiva el forzado ortogonal |
---

## 📐 Entrada de coordenadas

Convención: **`,` separa X e Y** y **`.` es el separador decimal**.

| Formato               | Ejemplo     | Significado                                      |
| --------------------- | ----------- | ------------------------------------------------ |
| Absoluto              | `10,20`     | Punto (10, 20).                                  |
| Absoluto decimal      | `10.5,20.2` | Punto con decimales.                             |
| Separador alternativo | `10.5;20.2` | Equivalente (útil en algunos estados numéricos). |
| Relativo cartesiano   | `@5,3`      | Último punto + (5, 3).                           |
| Relativo polar        | `@100<45`   | Distancia 100, ángulo 45° desde el último punto. |
| Polar absoluto        | `100<30`    | Punto a distancia 100 y ángulo 30° del origen.   |

Los ángulos se miden en **grados**, con `0°` en el eje +X y sentido antihorario.

---

## 🖱️ Uso del ratón

| Acción                                    | Resultado                                              |
| ----------------------------------------- | ------------------------------------------------------ |
| Clic izquierdo sobre entidad              | Selecciona / deselecciona.                             |
| Arrastre izquierda → derecha              | **Ventana**: selecciona lo completamente contenido.    |
| Arrastre derecha → izquierda              | **Cruce**: selecciona lo que toca/cruza el rectángulo. |
| `Shift` + arrastre                        | Añade a la selección actual.                           |
| `Ctrl` + arrastre                         | Quita de la selección actual.                          |
| Clic izquierdo con comando pidiendo punto | Introduce el punto (con snap aplicado).                |
| Clic derecho                              | Equivale a `Enter` (terminar/cancelar).                |
| Arrastrar un grip azul                    | Edita la entidad (vértices, radios, ejes, extremos).   |

---

## 🟦 Grips (pinzamientos)

Al seleccionar entidades aparecen grips azules editables:

| Entidad              | Grips                                |
| -------------------- | ------------------------------------ |
| Línea                | Inicio y fin.                        |
| Polilínea / Polígono | Cada vértice.                        |
| Círculo              | Centro y radio.                      |
| Arco                 | Centro, punto inicial y punto final. |
| Elipse               | Centro, eje X y eje Y.               |

---

## 🧲 Snaps

Se configuran con el comando `SNAP` (o `MALLA` / `VERMALLA` para la rejilla):

| Modo           | Ajusta a                                               |
| -------------- | ------------------------------------------------------ |
| `GRID`         | Malla (rejilla visible + ajuste).                      |
| `PUNTO`        | Vértices y centros.                                    |
| `EXTREMO`      | Extremos de líneas, polilíneas, polígonos y arcos.     |
| `MEDIO`        | Puntos medios de segmentos y arcos.                    |
| `INTERSECCION` | Intersecciones entre segmentos lineales.               |
| `ORTO`         | Movimiento horizontal/vertical respecto al punto base. |

Prioridad: **snaps de objeto → ORTO → GRID**.

Dentro de `SNAP`, escribir un **número** cambia el tamaño de la malla.

---

## 💾 Proyectos (JSON)

Los proyectos se guardan en JSON con este formato:

```json
{
  "version": 1,
  "next_entity_id": 7,
  "entities": [
    {
      "id": 1,
      "kind": "line",
      "data": {
        "start": { "__type__": "Point", "x": 0.0, "y": 0.0 },
        "end":   { "__type__": "Point", "x": 100.0, "y": 0.0 }
      }
    }
  ]
}
```

- `GUARDAR`: guarda sobre el archivo actual o abre diálogo/ruta.
- `GUARDARCOMO`: fuerza diálogo o ruta nueva.
- `ABRIR`: carga un proyecto (reemplaza el actual, con confirmación).
- `NUEVO`: proyecto vacío (con confirmación).
- El título de la ventana muestra el archivo actual.

---

## 🧱 Modelo de entidades

Todas las figuras se guardan como objetos `Entity`:

```python
Entity(id, kind, data, selected)
```

Tipos (`kind`):

```textile
line, polyline, circle, arc, polygon, ellipse
```

Esto permite que **todos** los comandos (mover, copiar, rotar, escalar, simetría, borrar, selección, grips, guardar/abrir) funcionen de forma uniforme sobre cualquier entidad.

---

## 🏗️ Arquitectura

```bash
tkCAD/
├── pixi.toml           # Configuración del entorno y tareas
├── pyproject.toml      # Paquete Python (editable install)
├── README.md
│
├── src/
│   └── tkcad/
│       ├── __main__.py         # Entry point: python -m tkcad
│       ├── app.py              # CadApp: orquestador y modelo
│       │
│       ├── core/               # Núcleo (sin UI)
│       │   ├── command.py      # Command, CommandResult
│       │   ├── entity.py       # Entity
│       │   ├── manager.py      # CommandLineManager
│       │   ├── parser.py       # parse_point, parse_number
│       │   ├── point.py        # Point
│       │   ├── project.py      # ProjectIO (JSON)
│       │   ├── snapengine.py   # SnapEngine
│       │   └── types.py        # Alias de comandos, constantes
│       │
│       ├── geometry/           # Utilidades geométricas
│       │   ├── intersection.py # line_line_intersection
│       │   ├── projection.py   # projection_param
│       │   └── utils.py        # EPS
│       │
│       ├── commands/           # Un archivo por comando
│       │   ├── registry.py     # Registro central de comandos
│       │   ├── drawing/        # LINEA, POLILINEA, CIRCULO, ...
│       │   ├── modify/         # MOVER, COPIAR, ROTAR, ...
│       │   ├── file/           # GUARDAR, ABRIR, NUEVO
│       │   ├── view/           # SELECCIONAR, SNAP, MALLA
│       │   └── system/         # AYUDA, EXIT
│       │
│       └── ui/                 # Widgets Tkinter
│           ├── canvas.py       # CadCanvas
│           ├── console.py      # ConsoleWidget
│           └── grips.py        # GripManager
│
└── tests/                      # Suite de pytest
    ├── test_geometry.py
    ├── test_manager.py
    ├── test_parser.py
    ├── test_projectio.py
    └── test_snapengine.py
```

El núcleo (`core/`, `geometry/`, `commands/`) es **independiente de Tkinter** y completamente testeable con `pixi run test`.

## ➕ Añadir un comando nuevo

Añadir un comando nuevo requiere **dos pasos**:

### 1. Crear el archivo del comando

Crea, por ejemplo, `src/tkcad/commands/drawing/spline.py`:

```python
from ...core import Command, CommandResult, Point, parse_point


class SplineCommand(Command):
    name = "SPLINE"
    aliases = ("SPL",)

    def __init__(self):
        self.points = []

    def start(self, ctx):
        ctx.prompt("Primer punto de la spline:")

    def handle_input(self, ctx, text: str) -> CommandResult:
        text = text.strip()
        if not text:
            return self._finish(ctx)
        try:
            p = parse_point(text, self.points[-1] if self.points else None)
        except ValueError as ex:
            ctx.write(f"Punto no válido: {ex}")
            return CommandResult.RUNNING
        self.points.append(p)
        ctx.prompt("Siguiente punto [Enter=terminar]:")
        return CommandResult.RUNNING

    def _finish(self, ctx) -> CommandResult:
        if len(self.points) >= 2:
            ctx.add_polyline(self.points)  # o un método específico
        return CommandResult.FINISHED

    def expects_point(self) -> bool:
        return True

    def get_point_base(self):
        return self.points[-1] if self.points else None
```

### 2. Registrarlo en `src/tkcad/commands/registry.py`

Añade el import y súmalo a la lista `ALL_COMMANDS`:

```python
from .drawing.spline import SplineCommand

ALL_COMMANDS = [
    # ... comandos existentes ...
    SplineCommand,
]
```

**Listo.** `SPLINE` y su alias `SPL` aparecen automáticamente en el autocompletado y en `AYUDA`.

## 🧪 Testing

La suite de tests protege los módulos del núcleo:

```bash

```

Cubiertos actualmente:

- Parser de puntos (cartesianos, relativos, polares)
- Geometría (intersecciones, proyecciones)
- Motor de snaps (GRID, ENDPOINT, MIDPOINT, INTERSECTION, ORTHO)
- Gestor de comandos (registro, alias, autocompletado)
- ProjectIO (round-trip JSON, save/load)

## 📜 Licencia

MIT

```adoc
---

## Paso siguiente

1. Crea también la carpeta `docs/` y dentro deja un `screenshot.png` (puedes poner una captura de la app cuando quieras).
2. Añade al `.gitignore` si no lo tenías:

```gitignore
# Screenshots generadas
*.png
# ... pero no docs/screenshot.png
```

(o simplemente no ignores PNG si quieres incluirlo en el repo).

3. Ejecuta:

```bash
pixi run test    # por si acaso nada se rompió
git add .
git commit -m "docs: README completo con arquitectura y guía para añadir comandos"
```

----

## ⚠️ Limitaciones conocidas

- `RECORTAR` y `EXTENDER` solo funcionan entre `LINEA` y límite `LINEA`.
- El snap `INTERSECCION` solo calcula intersecciones entre segmentos lineales.
- No hay zoom ni pan todavía.
- No hay deshacer/rehacer.
- No hay marcadores visuales de snap.
- `ESCALAR` es uniforme y con factor positivo.
- Las elipses no participan en recortes ni intersecciones.

---

## 🔮 Próximas mejoras previstas

- Deshacer / rehacer.
- Zoom y pan.
- Marcadores visuales de snap y snaps adicionales (cuadrante, tangente, centro).
- Selección por polígono y selección cíclica.
- Añadir/eliminar vértices con grips.
- Recortar/extender con más tipos de entidades.
- Intersecciones con círculos, arcos y elipses.
- Exportación/importación DXF.
- Control de cambios sin guardar (`modified`) y confirmación al salir.
- Autoguardado.

---

*Proyecto en desarrollo — Bixcoot.*
