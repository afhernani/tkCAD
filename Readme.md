# tkCAD — Editor CAD 2D en Python y Tkinter

tkCAD es un editor de dibujo tipo CAD 2D construido con **Python** y **Tkinter**, con una ventana de comandos estilo CAD, entrada de puntos por teclado y ratón, snaps, selección por ventana, grips de edición y proyectos guardables en JSON.

---

## ✨ Características principales

- **Ventana de comandos** integrada con historial, autocompletado (`Tab`) y ayuda.
- **Comandos de dibujo**: línea, polilínea, círculo, arco, polígono y elipse.
- **Comandos de edición**: mover, copiar, borrar, rotar, escalar, simetría, recortar y extender.
- **Sistema de selección**: por ID, por tipo, todo/nada/último, por ventana (window/crossing) y por clic.
- **Grips (pinzamientos)** azules para editar vértices, radios, ejes y extremos de arco con el ratón.
- **Snaps**: malla (grid), punto, extremo, punto medio, intersección y modo ortogonal.
- **Entrada de puntos** por teclado (absolutos, relativos, polares) y por ratón con snap aplicado.
- **Proyectos** guardables y cargables en formato **JSON**.
- **Modelo de entidades unificado** con IDs y estado de selección.

---

## 📦 Requisitos

- Python 3.8 o superior.
- Tkinter (incluido con Python en Windows y macOS; en Linux: `sudo apt install python3-tk`).
- Sin dependencias de terceros.

---

## 🚀 Ejecución

```bash
python app.py
```

---

## 🗂️ Estructura del proyecto

```textile
tkCAD/
├── app.py          # Ventana principal, consola, gestor de comandos, LINEA, POLILINEA, AYUDA, EXIT
├── core.py         # Base común: Point, Entity, Command, CommandResult, parsers, alias y tipos
├── geometria.py    # Utilidades: intersección recta-recta, proyecciones, EPS
├── circulo.py      # CIRCULO
├── arco.py         # ARCO
├── poligono.py     # POLIGONO
├── elipse.py       # ELIPSE
├── mover.py        # MOVER
├── copiar.py       # COPIAR
├── borrar.py       # BORRAR
├── rotar.py        # ROTAR
├── escalar.py      # ESCALAR
├── simetria.py     # SIMETRIA
├── recortar.py     # RECORTAR
├── extender.py     # EXTENDER
├── seleccion.py    # SELECCIONAR y LISTAR
├── guardar.py      # GUARDAR y GUARDARCOMO
├── abrir.py        # ABRIR
├── nuevo.py        # NUEVO
├── snap.py         # SNAP, MALLA y VERMALLA
└── Readme.md
```

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

## 📝 Ejemplo de uso básico

```tex
LINEA
0,0
@100<0
Enter

CIRCULO
50,50
25

SELECCIONAR
TODO

MOVER
0,0
@50,25

GUARDAR
plano.json
```

---

## Estado actual del proyecto a 15/08/2026

Con esta extracción, `app.py` se ha reducido ~200 líneas y el motor de snaps ahora es:

- **Testeable en aislamiento** (sin abrir Tkinter)
- **Reutilizable** (podrías usarlo en otro contexto)
- **Independiente** (no conoce la UI ni el canvas)

La estructura actual es muy limpia:

```tex
src/tkcad/
├── core/
│   ├── point.py
│   ├── entity.py
│   ├── command.py
│   ├── parser.py
│   ├── types.py
│   ├── manager.py          ✅ CommandLineManager
│   └── snapengine.py       ✅ SnapEngine (nuevo)
│
├── geometry/
│   ├── intersection.py
│   ├── projection.py
│   └── utils.py
│
├── commands/
│   ├── drawing/
│   ├── modify/
│   ├── file/
│   ├── view/
│   └── system/
│
├── ui/
│   ├── console.py
│   └── canvas.py
│
└── app.py                  (mucho más ligero)
```

## Agrupacion de grips la arquitectura.

```bash
src/tkcad/
├── core/          → point, entity, command, parser, types, manager, snapengine
├── geometry/      → intersection, projection, utils
├── commands/      → drawing, modify, file, view, system + registry
├── ui/            → console, canvas, grips
└── app.py         → orquestador + modelo
```

`app.py` ahora concentra básicamente el **modelo** (entidades, transformaciones, selección) y la orquestación.

---



---------

*Proyecto en desarrollo — Bixcoot.*
