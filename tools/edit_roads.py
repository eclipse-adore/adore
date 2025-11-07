import sys
import math
import requests
from PyQt5 import QtWidgets, QtGui, QtCore
from pyproj import Proj, transform
import re
import os

class VertexItem(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, x, y, line_data, index, radius=5, *args, **kwargs):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius, *args, **kwargs)
        self.setPos(x, y)
        self.line_data = line_data
        self.index = index
        self.radius = radius
        self.selected = False
        self.setBrush(QtGui.QBrush(QtCore.Qt.blue))
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(1)

    def set_selected(self, selected):
        self.selected = selected
        self.setBrush(QtGui.QBrush(QtCore.Qt.green if selected else QtCore.Qt.blue))

    def mousePressEvent(self, event):
        self.scene().parent().select_vertex(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.line_data["coords"][self.index] = (self.x(), self.y())
        self.scene().update_lines()

    def shape(self):
        path = QtGui.QPainterPath()
        adjusted_radius = self.radius / self.scene().views()[0].current_scale
        path.addEllipse(-adjusted_radius, -adjusted_radius, 2 * adjusted_radius, 2 * adjusted_radius)
        return path

    def contains(self, point):
        adjusted_radius = self.radius / self.scene().views()[0].current_scale
        return QtCore.QPointF(0, 0).distanceToPoint(point) <= adjusted_radius

    def paint(self, painter, option, widget):
        view = self.scene().views()[0]
        scale_factor = 1 / view.current_scale
        adjusted_radius = self.radius * scale_factor
        pen = QtGui.QPen(QtCore.Qt.black, 1 * scale_factor)
        painter.setPen(pen)
        rect = QtCore.QRectF(-adjusted_radius, -adjusted_radius, 2 * adjusted_radius, 2 * adjusted_radius)
        painter.setBrush(self.brush())
        painter.drawEllipse(rect)

class LineItem(QtWidgets.QGraphicsLineItem):
    def __init__(self, start_item, end_item, color=QtCore.Qt.red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_item = start_item
        self.end_item = end_item
        self.color = color
        self.selected = False
        self.update_position()
        self.setZValue(0)
        self.setAcceptHoverEvents(True)

    def update_position(self):
        self.setLine(QtCore.QLineF(self.start_item.pos(), self.end_item.pos()))

    def paint(self, painter, option, widget):
        view = self.scene().views()[0]
        scale_factor = 1 / view.current_scale
        pen = QtGui.QPen(self.color, 2 * scale_factor)
        painter.setPen(pen)
        painter.drawLine(self.line())

    def set_selected(self, selected):
        self.selected = selected
        self.color = QtCore.Qt.green if selected else QtCore.Qt.red
        self.update()

    def mousePressEvent(self, event):
        self.scene().parent().select_line_by_item(self)
        super().mousePressEvent(event)

class GraphicsScene(QtWidgets.QGraphicsScene):
    def update_lines(self):
        for item in self.items():
            if isinstance(item, LineItem):
                item.update_position()

class CanvasView(QtWidgets.QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.current_scale = 1.0
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setTransform(QtGui.QTransform().scale(1, -1))

    def wheelEvent(self, event):
        zoom_in_factor = 1.04
        zoom_out_factor = 1 / zoom_in_factor
        zoom_factor = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
        self.current_scale *= zoom_factor
        self.scale(zoom_factor, zoom_factor)

    def update_scene_rect_with_padding(self, padding=100):
        scene_rect = self.scene().itemsBoundingRect()
        scene_rect.adjust(-padding, -padding, padding, padding)
        self.setSceneRect(scene_rect)

class LineEditorApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_headers = {}
        self.lines = {"reference": [], "border": []}
        self.selected_line = None
        self.selected_vertex = None
        self.used_ids = set()
        self.setWindowTitle("R2S Editor")
        self.setGeometry(100, 100, 1200, 800)

        if not self.select_files():
            QtWidgets.QMessageBox.critical(self, "Error", "You must select an .r2sr or .r2sl file.")
            sys.exit(1)

        self.setup_ui()
        self.load_lines()
        self.canvas.update_scene_rect_with_padding()

    def select_files(self):
        dialog = QtWidgets.QFileDialog(self, "Select R2S Reference or Border file")
        dialog.setNameFilter("R2S files (*.r2sr *.r2sl)")
        if dialog.exec_():
            selected_file = dialog.selectedFiles()[0]
            base = os.path.splitext(selected_file)[0]
            self.r2sr_file = base + ".r2sr"
            self.r2sl_file = base + ".r2sl"
            return True
        return False

    def setup_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QHBoxLayout(central_widget)

        self.canvas = CanvasView()
        self.scene = GraphicsScene()
        self.scene.setParent(self)
        self.canvas.setScene(self.scene)
        layout.addWidget(self.canvas, stretch=3)

        control_panel = QtWidgets.QWidget()
        control_layout = QtWidgets.QVBoxLayout(control_panel)

        self.line_list = QtWidgets.QListWidget()
        self.line_list.itemClicked.connect(self.select_line)
        control_layout.addWidget(self.line_list)

        buttons = [
            ("New Reference Line", lambda: self.add_new_line("reference")),
            ("New Border Line", lambda: self.add_new_line("border")),
            ("Add Vertex to Start", lambda: self.add_vertex("start")),
            ("Add Vertex to End", lambda: self.add_vertex("end")),
            ("Delete Vertex", self.delete_selected_vertex),
            ("Save Changes", self.save_changes)
        ]
        for label, func in buttons:
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(func)
            control_layout.addWidget(btn)

        layout.addWidget(control_panel, stretch=1)

    def select_vertex(self, vertex):
        if self.selected_vertex is not None:
            try:
                self.selected_vertex.set_selected(False)
            except RuntimeError:
                self.selected_vertex = None
        self.selected_vertex = vertex
        if self.selected_vertex is not None:
            self.selected_vertex.set_selected(True)

    def select_line_by_item(self, line_item):
        for line_type, lines in self.lines.items():
            for line in lines:
                if (line_item.start_item.line_data == line and line_item.end_item.line_data == line):
                    self.selected_line = line
                    for i in range(self.line_list.count()):
                        item = self.line_list.item(i)
                        if item.data(QtCore.Qt.UserRole) == line:
                            self.line_list.setCurrentItem(item)
                            self.line_list.scrollToItem(item)
                            break
                    self.update_selected_line()
                    return

    def select_line(self, item):
        selected_line_data = item.data(QtCore.Qt.UserRole)
        for line in self.lines[selected_line_data["type"]]:
            if line["id"] == selected_line_data["id"]:
                self.selected_line = line
                break
        self.selected_vertex = None
        self.update_selected_line()

    def add_new_line(self, line_type):
        line_id = self.get_unique_id()
        line_data = {"id": line_id, "coords": [], "type": line_type, "columns": [str(line_id), ""]}
        self.lines[line_type].append(line_data)
        item = QtWidgets.QListWidgetItem(f"{line_type.capitalize()} - {line_id}")
        item.setData(QtCore.Qt.UserRole, line_data)
        self.line_list.addItem(item)

    def add_vertex(self, position):
        if self.selected_line:
            view_center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
            if position == "start":
                self.selected_line["coords"].insert(0, (view_center.x(), view_center.y()))
            else:
                self.selected_line["coords"].append((view_center.x(), view_center.y()))
            self.update_selected_line()

    def delete_selected_vertex(self):
        if self.selected_vertex and self.selected_line:
            self.selected_line["coords"].pop(self.selected_vertex.index)
            self.selected_vertex = None
            self.update_selected_line()

    def update_selected_line(self):
        self.scene.clear()
        for line_type, lines in self.lines.items():
            for line in lines:
                if len(line["coords"]) > 1:
                    prev_vertex = None
                    for index, coord in enumerate(line["coords"]):
                        vertex = VertexItem(*coord, line, index)
                        self.scene.addItem(vertex)
                        if prev_vertex:
                            color = QtCore.Qt.green if line == self.selected_line else QtCore.Qt.red
                            line_item = LineItem(prev_vertex, vertex, color)
                            line_item.set_selected(line == self.selected_line)
                            self.scene.addItem(line_item)
                        prev_vertex = vertex

    def load_lines(self):
        self.load_file(self.r2sr_file, "reference")
        self.load_file(self.r2sl_file, "border")
        self.populate_line_list()

    def load_file(self, file_path, line_type):
        with open(file_path, 'r') as file:
            header = file.readline().strip()
            self.file_headers[line_type] = header
            for line in file:
                try:
                    line_data = self.parse_line_with_full_data(line)
                    line_data["type"] = line_type
                    self.lines[line_type].append(line_data)
                    self.used_ids.add(line_data["id"])
                except ValueError:
                    print(f"Failed to parse line: {line}")
        self.update_selected_line()

    def parse_line_with_full_data(self, line):
        match = re.match(r'^(\d+),\"(LINESTRING \([^)]+\))\",(.*)$', line.strip())
        if not match:
            raise ValueError("Line format not recognized")
        line_id = int(match.group(1))
        geometry = match.group(2)
        remaining_columns = match.group(3).split(',')
        coord_text = re.search(r'LINESTRING \((.*?)\)', geometry).group(1)
        coord_pairs = coord_text.split(',')
        coords = [(float(x), float(y)) for x, y in (pair.strip().split() for pair in coord_pairs)]
        columns = [str(line_id), f'"{geometry}"'] + [col.strip() for col in remaining_columns]
        return {"id": line_id, "coords": coords, "columns": columns}

    def populate_line_list(self):
        self.line_list.clear()
        for line_type, lines in self.lines.items():
            for line in lines:
                item = QtWidgets.QListWidgetItem(f"{line_type.capitalize()} - {line['id']}")
                item.setData(QtCore.Qt.UserRole, line)
                self.line_list.addItem(item)

    def get_unique_id(self):
        new_id = 1
        while new_id in self.used_ids:
            new_id += 1
        self.used_ids.add(new_id)
        return new_id

    def save_changes(self):
        self.save_file(self.r2sr_file, "reference")
        self.save_file(self.r2sl_file, "border")

    def save_file(self, file_path, line_type):
        with open(file_path, 'w') as file:
            file.write(self.file_headers[line_type] + "\n")
            for line_data in self.lines[line_type]:
                coords_text = ','.join(f"{x} {y}" for x, y in line_data["coords"])
                line_data["columns"][1] = f'"LINESTRING ({coords_text})"'
                file.write(",".join(line_data["columns"]) + "\n")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = LineEditorApp()
    window.show()
    sys.exit(app.exec_())
