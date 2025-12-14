# graph_traversal.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QComboBox, QLineEdit, QSlider, QSizePolicy, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx
from collections import deque


class GraphTraversalPage(QWidget):
    backToCategorySignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Traversal Algorithms (BFS / DFS)")
        self.setGeometry(100, 60, 1000, 700)

        # internal
        self.G = nx.Graph()
        self.pos = {}
        self.steps = []         # list of (current_node_or_None, visited_set)
        self.step_ptr = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step_animation)

        # UI
        self.setup_ui()
        # default example graph (easy to read)
        self.default_edges = "0-1,0-2,1-3,1-4,2-5,2-6"
        self.load_and_show(self.default_edges)

    def setup_ui(self):
        main = QVBoxLayout()
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(10)

        title = QLabel("Traversal Algorithms")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        # controls row
        controls = QHBoxLayout()
        self.algo_box = QComboBox()
        self.algo_box.addItems(["BFS", "DFS"])
        self.algo_box.setFixedWidth(140)
        controls.addWidget(self.algo_box)

        self.edge_input = QLineEdit()
        self.edge_input.setPlaceholderText("Edges e.g. 0-1,0-2,1-3  (leave blank for example)")
        controls.addWidget(self.edge_input, 1)

        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("Start node (e.g. 0)")
        self.start_input.setFixedWidth(120)
        controls.addWidget(self.start_input)

        load_btn = QPushButton("Load Graph")
        load_btn.clicked.connect(self.on_load_graph)
        load_btn.setFixedWidth(110)
        controls.addWidget(load_btn)

        main.addLayout(controls)

        # speed + start/back
        row2 = QHBoxLayout()
        lbl_speed = QLabel("Speed:")
        lbl_speed.setFixedWidth(50)
        row2.addWidget(lbl_speed)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(800)
        self.speed_slider.setValue(350)
        row2.addWidget(self.speed_slider, 1)

        self.start_btn = QPushButton("Start Traversal")
        self.start_btn.clicked.connect(self.on_start)
        self.start_btn.setFixedWidth(140)
        row2.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.on_stop)
        self.stop_btn.setFixedWidth(90)
        row2.addWidget(self.stop_btn)

        self.back_btn = QPushButton("Back to Hub")
        self.back_btn.clicked.connect(self.on_back)
        self.back_btn.setFixedWidth(120)
        row2.addWidget(self.back_btn)

        main.addLayout(row2)

        # result label
        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.result_label.setAlignment(Qt.AlignCenter)
        main.addWidget(self.result_label)

        # matplotlib canvas
        self.figure, self.ax = plt.subplots(figsize=(9, 4))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main.addWidget(self.canvas)

        # explanation / visited order
        self.info = QTextEdit()
        self.info.setReadOnly(True)
        self.info.setFixedHeight(200)
        main.addWidget(self.info)

        self.setLayout(main)

    # ---------------- helpers ----------------
    def parse_edges(self, text):
        text = text.strip()
        if not text:
            text = self.default_edges
        parts = [p.strip() for p in text.split(",") if p.strip()]
        edges = []
        for p in parts:
            if "-" not in p:
                raise ValueError("Edges must be in format u-v (comma separated).")
            u, v = p.split("-", 1)
            u = u.strip(); v = v.strip()
            try:
                uu = int(u); vv = int(v)
                u, v = uu, vv
            except:
                pass
            edges.append((u, v))
        return edges

    def build_graph(self, edges):
        self.G = nx.Graph()
        self.G.add_edges_from(edges)
        if len(self.G.nodes) == 0:
            # add a single node example if nothing present
            self.G.add_node(0)
        try:
            self.pos = nx.spring_layout(self.G, seed=42)
        except:
            self.pos = nx.circular_layout(self.G)

    def load_and_show(self, edges_text):
        try:
            edges = self.parse_edges(edges_text)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid edges", str(e))
            return
        self.build_graph(edges)
        self.draw_graph(visited=set(), current=None)
        self.result_label.setText("Graph loaded. Pick algorithm and start node, then click Start Traversal.")
        self.info.clear()

    def on_load_graph(self):
        txt = self.edge_input.text().strip()
        if not txt:
            txt = self.default_edges
        self.load_and_show(txt)

    # ---------------- algorithm preparation ----------------
    def on_start(self):
        if self.timer.isActive():
            self.timer.stop()
        self.step_ptr = 0
        self.steps = []
        self.result_label.setText("")
        self.info.clear()

        if len(self.G.nodes) == 0:
            QMessageBox.warning(self, "No graph", "Load a graph first.")
            return

        start_txt = self.start_input.text().strip()
        if start_txt == "":
            QMessageBox.warning(self, "Start node required", "Please enter a start node.")
            return

        try:
            start_node = int(start_txt)
        except:
            start_node = start_txt

        if start_node not in self.G.nodes:
            QMessageBox.warning(self, "Invalid start", "Start node not found in the graph.")
            return

        algo = self.algo_box.currentText()
        if algo == "BFS":
            self.prepare_bfs(start_node)
        else:
            self.prepare_dfs(start_node)

        self.timer.start(self.speed_slider.value())

    def prepare_bfs(self, start):
        visited = set()
        q = deque([start])
        while q:
            u = q.popleft()
            if u in visited:
                continue
            visited.add(u)
            self.steps.append((u, set(visited)))
            for v in sorted(self.G.neighbors(u), key=lambda x: str(x)):
                if v not in visited:
                    q.append(v)
        self.steps.append((None, set(visited)))
        self.draw_graph(set(), None)

    def prepare_dfs(self, start):
        visited = set()
        stack = [start]
        while stack:
            u = stack.pop()
            if u in visited:
                continue
            visited.add(u)
            self.steps.append((u, set(visited)))
            for v in sorted(self.G.neighbors(u), key=lambda x: str(x), reverse=True):
                if v not in visited:
                    stack.append(v)
        self.steps.append((None, set(visited)))
        self.draw_graph(set(), None)

    # ---------------- animation ----------------
    def step_animation(self):
        if self.step_ptr >= len(self.steps):
            self.timer.stop()
            self.show_final_info()
            return

        current, visited_snapshot = self.steps[self.step_ptr]
        self.draw_graph(visited_snapshot, current)
        self.step_ptr += 1

    def draw_graph(self, visited, current):
        self.ax.clear()
        node_colors = []
        for n in self.G.nodes():
            if n == current:
                node_colors.append("#ffa500")   # orange
            elif n in visited:
                node_colors.append("#6fe07f")   # green
            else:
                node_colors.append("#7fb3ff")   # blue

        nx.draw_networkx_edges(self.G, pos=self.pos, ax=self.ax, edge_color="#999999")
        nx.draw_networkx_nodes(self.G, pos=self.pos, ax=self.ax, node_color=node_colors, node_size=800)
        nx.draw_networkx_labels(self.G, pos=self.pos, ax=self.ax, font_size=10, font_color="black")
        self.ax.set_axis_off()
        self.canvas.draw()

        if current is not None:
            self.result_label.setText(f"Visiting: {current}")
        else:
            self.result_label.setText("Traversal complete")

    def show_final_info(self):
        algo = self.algo_box.currentText()
        order = [cur for cur, vis in self.steps if cur is not None]
        if algo == "BFS":
            expl = (
                "<b>Algorithm:</b> Breadth-First Search (BFS)<br><br>"
                "BFS explores nodes level by level using a queue. Useful for shortest path in unweighted graphs.<br><br>"
                "<b>Time Complexity:</b> O(V + E)<br>"
                f"<b>Visited Order:</b> {', '.join(map(str, order))}"
            )
        else:
            expl = (
                "<b>Algorithm:</b> Depth-First Search (DFS)<br><br>"
                "DFS explores nodes by going deep first (stack/recursion).<br><br>"
                "<b>Time Complexity:</b> O(V + E)<br>"
                f"<b>Visited Order:</b> {', '.join(map(str, order))}"
            )
        self.info.setHtml(expl)

    # ---------------- controls ----------------
    def on_stop(self):
        if self.timer.isActive():
            self.timer.stop()
            self.result_label.setText("Animation stopped")

    def on_back(self):
        if self.timer.isActive():
            self.timer.stop()
        self.close()
        self.backToCategorySignal.emit()


# standalone test
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = GraphTraversalPage()
    w.show()
    sys.exit(app.exec_())
