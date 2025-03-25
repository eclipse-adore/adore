import sys
import math
import requests
from PyQt5 import QtWidgets, QtGui, QtCore
from pyproj import Proj, transform
import re

# r2sr_file = "./hamburg_m2.r2sr"
# r2sl_file = "./hamburg_m2.r2sl"

r2sr_file = "./de_bs_borders_wfs.r2sr"
r2sl_file = "./de_bs_borders_wfs.r2sl"

# UTM to lat/lon conversion utility
def utm_to_latlon(easting, northing, zone_number, northern_hemisphere=True):
    proj_utm = Proj(proj='utm', zone=zone_number, ellps='WGS84', south=not northern_hemisphere)
    proj_latlon = Proj(proj='latlong', datum='WGS84')
    lon, lat = transform(proj_utm, proj_latlon, easting, northing)
    return lat, lon


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
        self.setZValue(1)  # Keep vertices above lines

    def set_selected(self, selected):
        """Change color based on selection state"""
        self.selected = selected
        self.setBrush(QtGui.QBrush(QtCore.Qt.green if selected else QtCore.Qt.blue))

    def mousePressEvent(self, event):
        """Handle vertex selection"""
        self.scene().parent().select_vertex(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Update line coordinates when vertex is moved"""
        super().mouseMoveEvent(event)
        self.line_data["coords"][self.index] = (self.x(), self.y())
        self.scene().update_lines()

    def shape(self):
        """Defines precise clickable area"""
        path = QtGui.QPainterPath()
        adjusted_radius = self.radius / self.scene().views()[0].current_scale
        path.addEllipse(-adjusted_radius, -adjusted_radius, 2 * adjusted_radius, 2 * adjusted_radius)
        return path

    def contains(self, point):
        """Refines clicking precision by scaling clickable area"""
        adjusted_radius = self.radius / self.scene().views()[0].current_scale
        return QtCore.QPointF(0, 0).distanceToPoint(point) <= adjusted_radius

    def paint(self, painter, option, widget):
        """Adjust radius and pen width based on current view scale"""
        view = self.scene().views()[0]
        scale_factor = 1 / view.current_scale
        adjusted_radius = self.radius * scale_factor

        # Set the pen with adjusted width
        pen = QtGui.QPen(QtCore.Qt.black, 1 * scale_factor)  # Scale outline width
        painter.setPen(pen)

        # Draw the ellipse with adjusted size
        rect = QtCore.QRectF(-adjusted_radius, -adjusted_radius, 2 * adjusted_radius, 2 * adjusted_radius)
        painter.setBrush(self.brush())
        painter.drawEllipse(rect)


class LineItem(QtWidgets.QGraphicsLineItem):
    def __init__(self, start_item, end_item, color=QtCore.Qt.red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_item = start_item
        self.end_item = end_item
        self.color = color
        self.selected = False  # Keep track of selection state
        self.update_position()
        self.setZValue(0)  # Keep lines below vertices
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
        """Update the line's visual appearance based on selection state."""
        self.selected = selected
        self.color = QtCore.Qt.green if selected else QtCore.Qt.red
        self.update()

    def mousePressEvent(self, event):
        """Handle line selection."""
        self.scene().parent().select_line_by_item(self)
        super().mousePressEvent(event)


class LineEditorApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_headers = {}
        self.setWindowTitle("R2S Editor")
        self.setGeometry(100, 100, 1200, 800)

        self.lines = {"reference": [], "border": []}
        self.selected_line = None
        self.selected_vertex = None
        self.used_ids = set()

        self.setup_ui()
        self.load_lines()
        self.canvas.update_scene_rect_with_padding()

    def select_line_by_item(self, line_item):
        """Select the line corresponding to the clicked LineItem and update the list."""
        for line_type, lines in self.lines.items():
            for line in lines:
                # Match the line data by comparing start and end coordinates
                if (line_item.start_item.line_data == line and 
                    line_item.end_item.line_data == line):
                    self.selected_line = line

                    # Find and select the corresponding item in the list
                    for i in range(self.line_list.count()):
                        item = self.line_list.item(i)
                        if item.data(QtCore.Qt.UserRole) == line:
                            self.line_list.setCurrentItem(item)
                            self.line_list.scrollToItem(item, QtWidgets.QAbstractItemView.PositionAtCenter)
                            break

                    self.update_selected_line()
                    self.update_buttons()
                    return

    def setup_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QHBoxLayout(central_widget)

        self.canvas = CanvasView()
        self.scene = GraphicsScene()
        self.scene.setParent(self)
        self.canvas.setScene(self.scene)
        self.canvas.setRenderHint(QtGui.QPainter.Antialiasing)
        layout.addWidget(self.canvas, stretch=3)

        control_panel = QtWidgets.QWidget()
        control_layout = QtWidgets.QVBoxLayout(control_panel)

        self.line_list = QtWidgets.QListWidget()
        self.line_list.itemClicked.connect(self.select_line)
        control_layout.addWidget(self.line_list)

        new_reference_btn = QtWidgets.QPushButton("New Reference Line")
        new_reference_btn.clicked.connect(lambda: self.add_new_line("reference"))
        control_layout.addWidget(new_reference_btn)

        new_border_btn = QtWidgets.QPushButton("New Border Line")
        new_border_btn.clicked.connect(lambda: self.add_new_line("border"))
        control_layout.addWidget(new_border_btn)

        self.add_vertex_start_btn = QtWidgets.QPushButton("Add Vertex to Start")
        self.add_vertex_start_btn.clicked.connect(lambda: self.add_vertex("start"))
        control_layout.addWidget(self.add_vertex_start_btn)

        self.add_vertex_end_btn = QtWidgets.QPushButton("Add Vertex to End")
        self.add_vertex_end_btn.clicked.connect(lambda: self.add_vertex("end"))
        control_layout.addWidget(self.add_vertex_end_btn)

        self.delete_vertex_btn = QtWidgets.QPushButton("Delete Vertex")
        self.delete_vertex_btn.clicked.connect(self.delete_selected_vertex)
        control_layout.addWidget(self.delete_vertex_btn)

        save_btn = QtWidgets.QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        control_layout.addWidget(save_btn)

        layout.addWidget(control_panel, stretch=1)

    def select_vertex(self, vertex):
        """Handle vertex selection and UI updates, with safety check for deleted objects"""
        # Deselect previously selected vertex if it's still valid
        if self.selected_vertex is not None:
            try:
                self.selected_vertex.set_selected(False)
            except RuntimeError:
                # Handle the case where the VertexItem has been deleted
                self.selected_vertex = None

        # Select the new vertex
        self.selected_vertex = vertex
        if self.selected_vertex is not None:
            self.selected_vertex.set_selected(True)
        self.update_buttons()

    def select_line(self, item):
        """Handle line selection and ensure it directly references `self.lines`"""
        selected_line_data = item.data(QtCore.Qt.UserRole)
        for line in self.lines[selected_line_data["type"]]:
            if line["id"] == selected_line_data["id"]:
                self.selected_line = line
                break
        self.selected_vertex = None  # Deselect any previously selected vertex
        self.update_selected_line()
        self.update_buttons()

    def update_buttons(self):
        """Enable or disable buttons based on current selection"""
        has_selected_line = self.selected_line is not None
        has_selected_vertex = self.selected_vertex is not None
        self.add_vertex_start_btn.setEnabled(has_selected_line)
        self.add_vertex_end_btn.setEnabled(has_selected_line)
        self.delete_vertex_btn.setEnabled(has_selected_vertex)

    def add_new_line(self, line_type):
        line_id = self.get_unique_id()
        line_data = {"id": line_id, "coords": [], "type": line_type}
        self.lines[line_type].append(line_data)
        item = QtWidgets.QListWidgetItem(f"{line_type.capitalize()} - {line_id}")
        item.setData(QtCore.Qt.UserRole, line_data)
        self.line_list.addItem(item)

    def add_vertex(self, position):
        print("add vertex")
        """Add a vertex to start or end of the selected line"""
        if self.selected_line:
            view_center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
            if position == "start":
                self.selected_line["coords"].insert(0, (view_center.x(), view_center.y()))
            else:
                self.selected_line["coords"].append((view_center.x(), view_center.y()))
            self.update_selected_line()
        else:
            print("cant create vertex, no selected line")

    def delete_selected_vertex(self):
        """Delete the currently selected vertex"""
        if self.selected_vertex and self.selected_line:
            self.selected_line["coords"].pop(self.selected_vertex.index)
            self.selected_vertex = None  # Clear the selected vertex
            self.update_selected_line()
            self.update_buttons()

    def update_selected_line(self):
        """Refresh display of selected line and vertices."""
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
        """Load lines from files"""
        self.load_file(r2sr_file, "reference")
        self.load_file(r2sl_file, "border")
        self.populate_line_list()

    def load_file(self, file_path, line_type):
        with open(file_path, 'r') as file:
            header = file.readline().strip()  # Capture the header
            self.file_headers[line_type] = header

            for line in file:
                try:
                    line_data = self.parse_line_with_full_data(line)
                    line_data["type"] = line_type  # Track if it's reference or border
                    self.lines[line_type].append(line_data)
                    self.used_ids.add(line_data["id"])
                except ValueError:
                    print(f"Failed to parse line: {line}")
        self.update_selected_line()

    def parse_line_with_full_data(self, line):
        """Parse line data with ID, LINESTRING, and other columns"""
        match = re.match(r'^(\d+),"(LINESTRING \([^)]+\))",(.*)$', line.strip())
        if not match:
            raise ValueError("Line format not recognized")
        
        line_id = int(match.group(1))
        geometry = match.group(2)
        remaining_columns = match.group(3).split(',')
        coord_text = re.search(r'LINESTRING \((.*?)\)', geometry).group(1)
        coord_pairs = coord_text.split(',')
        coords = [(float(x), float(y)) for x, y in (pair.strip().split() for pair in coord_pairs)]
        columns = [str(line_id), f'"{geometry}"'] + [col.strip() for col in remaining_columns]

        return {
            "id": line_id,
            "coords": coords,
            "columns": columns
        }

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
        self.save_file(r2sr_file, "reference")
        self.save_file(r2sl_file, "border")

    def save_file(self, file_path, line_type):
        with open(file_path, 'w') as file:
            file.write(self.file_headers[line_type] + "\n")
            for line_data in self.lines[line_type]:
                coords_text = ','.join(f"{x} {y}" for x, y in line_data["coords"])
                line_data["columns"][1] = f'"LINESTRING ({coords_text})"'
                file.write(",".join(line_data["columns"]) + "\n")


class GraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self):
        super().__init__()

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
        self.background_tile = None  # Holds the background map image
        self.setTransform(QtGui.QTransform().scale(1, -1))

    def wheelEvent(self, event):
        zoom_in_factor = 1.04
        zoom_out_factor = 1 / zoom_in_factor
        zoom_factor = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
        self.current_scale *= zoom_factor
        self.scale(zoom_factor, zoom_factor)

    def fetch_wms_image(self, bbox, width=800, height=600):
        """Fetch map image from WMS server using adjusted bounding box order."""
        
        # Attempt switching BBOX order if server expects different interpretation
        # This switches BBOX format to minLat, minLon, maxLat, maxLon
        bbox_str = ",".join(f"{coord:.6f}" for coord in bbox)

        print(bbox_str)
        
        wms_url = (
            f"https://ows.terrestris.de/osm/service?"
            f"SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&BBOX={bbox_str}"
            f"&SRS=EPSG:4326&WIDTH={width}&HEIGHT={height}&LAYERS=OSM-WMS&STYLES=&FORMAT=image/png"
        )

        print(wms_url)
        
        response = requests.get(wms_url)
        if response.status_code == 200:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(response.content)
            return pixmap
        else:
            print(f"Failed to fetch WMS image: {response.status_code}, {response.content}")
            return None


    def update_scene_rect_with_padding(self, padding=100, utm_zone=32):
        """Set the scene rectangle with padding around items and fetch background image."""
        scene_rect = self.scene().itemsBoundingRect()
        scene_rect.adjust(-padding, -padding, padding, padding)
        self.setSceneRect(scene_rect)

        # Convert UTM corners to lat/lon for WMS bounding box
        # top_left_utm = (scene_rect.left(), scene_rect.top())
        # bottom_right_utm = (scene_rect.right(), scene_rect.bottom())
        
        # top_left_latlon = utm_to_latlon(top_left_utm[0], top_left_utm[1], utm_zone)
        # bottom_right_latlon = utm_to_latlon(bottom_right_utm[0], bottom_right_utm[1], utm_zone)
        
        # # Define the bounding box for the WMS request
        # bbox = [top_left_latlon[0], top_left_latlon[1],bottom_right_latlon[0], bottom_right_latlon[1] ]

        # # Fetch WMS image
        # background_pixmap = self.fetch_wms_image(bbox, width=self.width(), height=self.height())
        # if background_pixmap:
        #     if self.background_tile:
        #         self.scene().removeItem(self.background_tile)  # Remove old background
        #     self.background_tile = QtWidgets.QGraphicsPixmapItem(background_pixmap)
        #     self.background_tile.setZValue(-1)  # Ensure it is behind other items
        #     self.scene().addItem(self.background_tile)
        #     self.background_tile.setPos(scene_rect.topLeft())

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = LineEditorApp()
    window.show()
    sys.exit(app.exec_())
