# shortest_path.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QComboBox, QLineEdit, QSlider, QSizePolicy, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx
import heapq
import math


class ShortestPathPage(QWidget):
    backToCategorySignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shortest Path Algorithms")
        self.setGeometry(100, 60, 1000, 700)

        self.G = nx.DiGraph()  # allow directed weights too
        self.pos = {}
        self.steps = []  # for Dijkstra: list of (current_node_or_None, distances_snapshot)
        self.step_ptr = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step_animation)

        self.setup_ui()
        self.default_edges = "0-1-4,0-2-2,1-3-5,2-3-8,2-4-10,3-4-2"
        self.load_and_show(self.default_edges)

    def setup_ui(self):
        main = QVBoxLayout()
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(10)

        title = QLabel("Shortest Path Algorithms")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        controls = QHBoxLayout()
        self.algo_box = QComboBox()
        self.algo_box.addItems(["Dijkstra", "Bellman-Ford"])
        self.algo_box.setFixedWidth(160)
        controls.addWidget(self.algo_box)

        self.edge_input = QLineEdit()
        self.edge_input.setPlaceholderText("Edges e.g. 0-1-4,0-2-2 (u-v-w). Leave blank for example.")
        controls.addWidget(self.edge_input, 1)

        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("Source node (e.g. 0)")
        self.start_input.setFixedWidth(120)
        controls.addWidget(self.start_input)

        load_btn = QPushButton("Load Graph")
        load_btn.clicked.connect(self.on_load_graph)
        load_btn.setFixedWidth(110)
        controls.addWidget(load_btn)

        main.addLayout(controls)

        row2 = QHBoxLayout()
        lbl_speed = QLabel("Speed:")
        lbl_speed.setFixedWidth(50)
        row2.addWidget(lbl_speed)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(800)
        self.speed_slider.setValue(300)
        row2.addWidget(self.speed_slider, 1)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.on_start)
        self.start_btn.setFixedWidth(120)
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

        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.result_label.setAlignment(Qt.AlignCenter)
        main.addWidget(self.result_label)

        self.figure, self.ax = plt.subplots(figsize=(9, 4))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main.addWidget(self.canvas)

        self.info = QTextEdit()
        self.info.setReadOnly(True)
        self.info.setFixedHeight(220)
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
                raise ValueError("Edges must be in format u-v-w (comma separated).")
            items = [it.strip() for it in p.split("-")]
            if len(items) < 2:
                raise ValueError("Invalid edge format.")
            u, v = items[0], items[1]
            try:
                w = float(items[2]) if len(items) >= 3 else 1.0
            except:
                raise ValueError("Edge weight must be numeric.")
            try:
                uu = int(u); vv = int(v)
                u, v = uu, vv
            except:
                pass
            edges.append((u, v, w))
        return edges

    def build_graph(self, edges):
        self.G = nx.DiGraph()
        for u, v, w in edges:
            self.G.add_edge(u, v, weight=w)
        if len(self.G.nodes) == 0:
            self.G.add_node(0)
        try:
            self.pos = nx.spring_layout(self.G, seed=42)
        except:
            self.pos = nx.circular_layout(self.G)

    def load_and_show(self, edges_text):
        try:
            edges = self.parse_edges(edges_text)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid input", str(e))
            return
        self.build_graph(edges)
        self.draw_graph(distances=None, current=None)
        self.result_label.setText("Graph loaded. Choose algorithm and source, then Start.")
        self.info.clear()

    def on_load_graph(self):
        txt = self.edge_input.text().strip()
        if not txt:
            txt = self.default_edges
        self.load_and_show(txt)

    # -------------- algorithm prep --------------
    def on_start(self):
        if self.timer.isActive():
            self.timer.stop()
        self.steps = []
        self.step_ptr = 0
        self.result_label.setText("")
        self.info.clear()

        if len(self.G.nodes) == 0:
            QMessageBox.warning(self, "No graph", "Load a graph first.")
            return

        start_txt = self.start_input.text().strip()
        if start_txt == "":
            QMessageBox.warning(self, "Source required", "Please enter a source node.")
            return

        try:
            source = int(start_txt)
        except:
            source = start_txt

        if source not in self.G.nodes:
            QMessageBox.warning(self, "Invalid source", "Source node not found.")
            return

        algo = self.algo_box.currentText()
        if algo == "Dijkstra":
            self.prepare_dijkstra(source)
        else:
            self.prepare_bellman_ford(source)

        self.timer.start(self.speed_slider.value())

    def prepare_dijkstra(self, source):
        dist = {n: math.inf for n in self.G.nodes}
        dist[source] = 0
        visited = set()
        pq = [(0, source)]
        # record step snapshots: (current_node_or_None, dict(distances))
        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            # snapshot before relaxing neighbors (shows current node)
            self.steps.append((u, dict(dist)))
            for v in self.G.successors(u):
                w = self.G[u][v].get("weight", 1.0)
                if dist[v] > dist[u] + w:
                    dist[v] = dist[u] + w
                    heapq.heappush(pq, (dist[v], v))
        self.steps.append((None, dict(dist)))
        # initial draw
        self.draw_graph(distances={n: (0 if n==source else math.inf) for n in self.G.nodes}, current=None)

    def prepare_bellman_ford(self, source):
        # basic Bellman-Ford snapshots by rounds (not fully animated per-edge)
        nodes = list(self.G.nodes)
        dist = {n: math.inf for n in nodes}
        dist[source] = 0
        self.steps.append((None, dict(dist)))
        for i in range(len(nodes) - 1):
            updated = False
            for u, v, data in self.G.edges(data=True):
                w = data.get("weight", 1.0)
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    updated = True
            self.steps.append((f"round_{i+1}", dict(dist)))
            if not updated:
                break
        self.steps.append((None, dict(dist)))

    # -------------- animation --------------
    def step_animation(self):
        if self.step_ptr >= len(self.steps):
            self.timer.stop()
            self.show_explanation()
            return

        cur, dist_snapshot = self.steps[self.step_ptr]
        self.draw_graph(distances=dist_snapshot, current=cur)
        self.step_ptr += 1

    def draw_graph(self, distances=None, current=None):
        self.ax.clear()
        node_colors = []
        for n in self.G.nodes():
            if n == current:
                node_colors.append("#ffa500")
            else:
                node_colors.append("#7fb3ff")
        nx.draw_networkx_edges(self.G, pos=self.pos, ax=self.ax, edge_color="#888888")
        nx.draw_networkx_nodes(self.G, pos=self.pos, ax=self.ax, node_color=node_colors, node_size=700)
        nx.draw_networkx_labels(self.G, pos=self.pos, ax=self.ax, font_size=9)
        edge_labels = nx.get_edge_attributes(self.G, "weight")
        nx.draw_networkx_edge_labels(self.G, pos=self.pos, edge_labels=edge_labels, ax=self.ax)
        if distances:
            for n, d in distances.items():
                label = "∞" if d == math.inf else str(int(d))
                x, y = self.pos[n]
                self.ax.text(x, y + 0.08, f"d={label}", fontsize=9, ha="center", color="darkred")
        self.ax.set_axis_off()
        self.canvas.draw()

        if isinstance(current, str) and current.startswith("round_"):
            self.result_label.setText(f"Bellman-Ford: {current}")
        elif current is None:
            self.result_label.setText("Completed step / final distances")
        else:
            self.result_label.setText(f"Processing: {current}")

    def show_explanation(self):
        algo = self.algo_box.currentText()
        final = self.steps[-1][1] if self.steps else {}
        dist_summary = ", ".join([f"{n}: {('∞' if d==math.inf else int(d))}" for n, d in final.items()])
        if algo == "Dijkstra":
            expl = (
                "<b>Dijkstra's Algorithm</b><br><br>"
                "Finds shortest path from a single source in graphs with non-negative weights.<br>"
                "<b>Time Complexity:</b> O(E log V) with a priority queue.<br><br>"
                f"<b>Final distances:</b> {dist_summary}"
            )
        else:
            expl = (
                "<b>Bellman-Ford Algorithm</b><br><br>"
                "Handles negative edge weights; relaxes edges V-1 times.<br>"
                "<b>Time Complexity:</b> O(VE).<br><br>"
                f"<b>Final distances:</b> {dist_summary}"
            )
        self.info.setHtml(expl)
        self.result_label.setText("Algorithm completed")

    # ---------------- controls ----------------
    def on_stop(self):
        if self.timer.isActive():
            self.timer.stop()
            self.result_label.setText("Stopped")

    def on_back(self):
        if self.timer.isActive():
            self.timer.stop()
        self.close()
        self.backToCategorySignal.emit()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = ShortestPathPage()
    w.show()
    sys.exit(app.exec_())
