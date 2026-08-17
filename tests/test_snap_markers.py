from tkcad.ui.snap_markers import SnapMarkerDrawer, SNAP_MARKER_KINDS


class FakeCanvas:
    def __init__(self):
        self.calls = []
        self._next = 1

    def _new(self, kind, args):
        self.calls.append((kind, args))
        self._next += 1
        return self._next

    def create_rectangle(self, *a, **k): return self._new("rect", a)
    def create_polygon(self, *a, **k): return self._new("poly", a)
    def create_oval(self, *a, **k): return self._new("oval", a)
    def create_line(self, *a, **k): return self._new("line", a)
    def delete(self, item): pass


def test_cada_snap_dibuja_al_menos_un_primitiva():
    for kind in SNAP_MARKER_KINDS:
        canvas = FakeCanvas()
        drawer = SnapMarkerDrawer(canvas)
        drawer.draw(10, 10, kind)
        assert len(canvas.calls) >= 1, f"{kind} no dibujó nada"


def test_clear_vacia_los_items():
    canvas = FakeCanvas()
    drawer = SnapMarkerDrawer(canvas)
    drawer.draw(10, 10, "ENDPOINT")
    assert len(drawer.items) == 1
    drawer.clear()
    assert drawer.items == []


def test_draw_reemplaza_el_marcador_anterior():
    canvas = FakeCanvas()
    drawer = SnapMarkerDrawer(canvas)
    drawer.draw(10, 10, "ENDPOINT")
    drawer.draw(20, 20, "CENTER")
    assert len(drawer.items) == 1  # solo queda el último