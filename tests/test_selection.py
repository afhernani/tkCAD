import pytest
from tkcad.core import Document, Point


def test_window_selecciona_entidad_completamente_dentro():
    """Window: solo entidades 100% dentro del rectángulo."""
    doc = Document()
    
    # Línea completamente dentro del rectángulo (10,10)-(20,20)
    doc.add_line(Point(12, 12), Point(18, 18))  # id 1
    
    # Línea que sale del rectángulo
    doc.add_line(Point(15, 15), Point(25, 25))  # id 2
    
    # Línea completamente fuera
    doc.add_line(Point(30, 30), Point(40, 40))  # id 3
    
    # Seleccionar con window en (10,10)-(20,20)
    count = doc.select_by_rectangle(10, 10, 20, 20, mode="window", action="replace")
    
    assert count == 1
    assert doc.get_entity_by_id(1).selected is True
    assert doc.get_entity_by_id(2).selected is False
    assert doc.get_entity_by_id(3).selected is False


def test_crossing_selecciona_entidad_que_toca():
    """Crossing: entidades que tocan el rectángulo."""
    doc = Document()
    
    # Línea completamente dentro
    doc.add_line(Point(12, 12), Point(18, 18))  # id 1
    
    # Línea que sale del rectángulo
    doc.add_line(Point(15, 15), Point(25, 25))  # id 2
    
    # Línea completamente fuera
    doc.add_line(Point(30, 30), Point(40, 40))  # id 3
    
    # Seleccionar con crossing en (10,10)-(20,20)
    count = doc.select_by_rectangle(10, 10, 20, 20, mode="crossing", action="replace")
    
    assert count == 2
    assert doc.get_entity_by_id(1).selected is True
    assert doc.get_entity_by_id(2).selected is True   # toca el rectángulo
    assert doc.get_entity_by_id(3).selected is False


def test_window_con_circulo():
    """Círculo completamente dentro."""
    doc = Document()
    
    # Círculo con centro en (15,15) y radio 3 → bbox (12,12)-(18,18)
    doc.add_circle(Point(15, 15), 3.0)  # id 1
    
    # Círculo que sale del rectángulo
    doc.add_circle(Point(20, 20), 5.0)  # id 2 → bbox (15,15)-(25,25)
    
    count = doc.select_by_rectangle(10, 10, 20, 20, mode="window", action="replace")
    
    assert count == 1
    assert doc.get_entity_by_id(1).selected is True
    assert doc.get_entity_by_id(2).selected is False


def test_action_add_no_deselecciona():
    """Action 'add' no quita entidades ya seleccionadas."""
    doc = Document()
    
    doc.add_line(Point(5, 5), Point(8, 8))    # id 1
    doc.add_line(Point(12, 12), Point(18, 18))  # id 2
    
    # Seleccionar primero la línea 1
    doc.toggle_selection(1)
    assert doc.get_entity_by_id(1).selected is True
    
    # Añadir la línea 2 con window
    count = doc.select_by_rectangle(10, 10, 20, 20, mode="window", action="add")
    
    assert count == 1
    assert doc.get_entity_by_id(1).selected is True   # sigue seleccionada
    assert doc.get_entity_by_id(2).selected is True   # nueva selección


def test_action_remove_quita_de_seleccion():
    """Action 'remove' quita entidades de la selección actual."""
    doc = Document()
    
    doc.add_line(Point(12, 12), Point(18, 18))  # id 1
    doc.add_line(Point(22, 22), Point(28, 28))  # id 2
    
    # Seleccionar ambas
    doc.select_all()
    assert doc.selection_count() == 2
    
    # Quitar la línea 1 con window
    count = doc.select_by_rectangle(10, 10, 20, 20, mode="window", action="remove")
    
    assert count == 1
    assert doc.get_entity_by_id(1).selected is False
    assert doc.get_entity_by_id(2).selected is True


def test_action_replace_limpia_y_selecciona():
    """Action 'replace' limpia la selección y selecciona las nuevas."""
    doc = Document()
    
    doc.add_line(Point(5, 5), Point(8, 8))      # id 1
    doc.add_line(Point(12, 12), Point(18, 18))  # id 2
    
    # Seleccionar la línea 1
    doc.toggle_selection(1)
    assert doc.get_entity_by_id(1).selected is True
    
    # Replace con window que solo incluye la línea 2
    count = doc.select_by_rectangle(10, 10, 20, 20, mode="window", action="replace")
    
    assert count == 1
    assert doc.get_entity_by_id(1).selected is False  # deseleccionada
    assert doc.get_entity_by_id(2).selected is True   # nueva selección


def test_window_con_polilinea():
    """Polilínea con múltiples segmentos."""
    doc = Document()
    
    # Polilínea completamente dentro de (10,10)-(30,30)
    doc.add_entity("polyline", {
        "points": [Point(12, 12), Point(20, 15), Point(28, 28)]
    })  # id 1
    
    # Polilínea que sale del rectángulo
    doc.add_entity("polyline", {
        "points": [Point(15, 15), Point(25, 25), Point(35, 35)]
    })  # id 2
    
    count = doc.select_by_rectangle(10, 10, 30, 30, mode="window", action="replace")
    
    assert count == 1
    assert doc.get_entity_by_id(1).selected is True
    assert doc.get_entity_by_id(2).selected is False


def test_window_sin_entidades():
    """Rectángulo que no contiene ninguna entidad."""
    doc = Document()
    
    doc.add_line(Point(50, 50), Point(60, 60))  # id 1
    
    count = doc.select_by_rectangle(10, 10, 20, 20, mode="window", action="replace")
    
    assert count == 0
    assert doc.selection_count() == 0