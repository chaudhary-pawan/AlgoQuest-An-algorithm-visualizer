# mst_visualizer.py
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


class MSTPage(QWidget):
    backToCategorySignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimum Spanning Tree (Prim / Kruskal)")
        self.setGeometry(100, 60, 1000, 700)

        self.G = nx.Graph()
        self.pos = {}
        self.steps = []  # for Prim: (edge_added_or_None, mst_edges_snapshot)
        self.step_ptr = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step_animation)

        self.setup_ui()
        self.default_edges = "0-1-4,0-2-3,1-2-2,1-3-5,2-3-4"
        self.load_and_show(self.default_edges)

    def setup_ui(self):
        main = QVBoxLayout()
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(10)

        title = QLabel("Minimum Spanning Tree Algorithms")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        controls = QHBoxLayout()
        self.algo_box = QComboBox()
        self.algo_box.addItems(["Prim", "Kruskal"])
        self.algo_box.setFixedWidth(140)
        controls.addWidget(self.algo_box)

        self.edge_input = QLineEdit()
        self.edge_input.setPlaceholderText("Edges e.g. 0-1-4,0-2-3 (u-v-w). Leave blank for example.")
        controls.addWidget(self.edge_input, 1)

        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("Start node for Prim (e.g. 0)")
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
        self.speed_slider.setValue(350)
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
                raise ValueError("Weight must be numeric.")
            try:
                uu = int(u); vv = int(v)
                u, v = uu, vv
            except:
                pass
            edges.append((u, v, w))
        return edges

    def build_graph(self, edges):
        self.G = nx.Graph()
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
        self.draw_graph(mst_edges=set(), highlight=None)
        self.result_label.setText("Graph loaded. Choose algorithm and start.")
        self.info.clear()

    def on_load_graph(self):
        txt = self.edge_input.text().strip()
        if not txt:
            txt = self.default_edges
        self.load_and_show(txt)

    # ---------------- algorithm prep ----------------
    def on_start(self):
        if self.timer.isActive():
            self.timer.stop()
        self.steps = []
        self.step_ptr = 0
        self.result_label.setText("")
        self.info.clear()

        algo = self.algo_box.currentText()
        if algo == "Prim":
            # need start node
            start_txt = self.start_input.text().strip()
            if start_txt == "":
                QMessageBox.warning(self, "Start node", "Please enter start node for Prim.")
                return
            try:
                start = int(start_txt)
            except:
                start = start_txt
            if start not in self.G.nodes:
                QMessageBox.warning(self, "Invalid start", "Start node not in graph.")
                return
            self.prepare_prim(start)
        else:
            self.prepare_kruskal()

        self.timer.start(self.speed_slider.value())

    def prepare_prim(self, start):
        visited = set([start])
        edges = []
        for v in self.G.neighbors(start):
            w = self.G[start][v].get("weight", 1.0)
            heapq.heappush(edges, (w, start, v))

        mst_edges = set()
        # record initial
        self.steps.append((None, set(mst_edges), list(edges)))
        while edges:
            w, u, v = heapq.heappop(edges)
            if v in visited:
                continue
            visited.add(v)
            mst_edges.add((u, v, w))
            # snapshot after adding edge
            self.steps.append(((u, v, w), set(mst_edges), list(edges)))
            for nbr in self.G.neighbors(v):
                if nbr not in visited:
                    ww = self.G[v][nbr].get("weight", 1.0)
                    heapq.heappush(edges, (ww, v, nbr))
        # final
        self.steps.append((None, set(mst_edges), []))

    def prepare_kruskal(self):
        # Kruskal: sort edges and pick if no cycle (using union-find)
        edges = sorted([(data['weight'], u, v) for u, v, data in self.G.edges(data=True)])
        parent = {}
        rank = {}

        def make_set(x):
            parent[x] = x
            rank[x] = 0

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(a, b):
            ra = find(a); rb = find(b)
            if ra == rb:
                return False
            if rank[ra] < rank[rb]:
                parent[ra] = rb
            elif rank[rb] < rank[ra]:
                parent[rb] = ra
            else:
                parent[rb] = ra
                rank[ra] += 1
            return True

        for n in self.G.nodes:
            make_set(n)

        mst_edges = set()
        # snapshot initial
        self.steps.append((None, set(mst_edges), list(edges)))
        for w, u, v in edges:
            # consider edge
            if union(u, v):
                mst_edges.add((u, v, w))
                self.steps.append(((u, v, w), set(mst_edges), list(edges)))
        self.steps.append((None, set(mst_edges), []))

    # ---------------- animation ----------------
    def step_animation(self):
        if self.step_ptr >= len(self.steps):
            self.timer.stop()
            self.show_explanation()
            return

        item, mst_snapshot, remaining = self.steps[self.step_ptr]
        self.draw_graph(mst_edges=mst_snapshot, highlight=item)
        self.step_ptr += 1

    def draw_graph(self, mst_edges=set(), highlight=None):
        self.ax.clear()
        # base nodes and edges
        base_edge_colors = []
        base_edges = list(self.G.edges(data=True))
        for u, v, d in base_edges:
            base_edge_colors.append("#bbbbbb")
        nx.draw_networkx_nodes(self.G, pos=self.pos, ax=self.ax, node_color="#7fb3ff", node_size=700)
        nx.draw_networkx_labels(self.G, pos=self.pos, ax=self.ax)
        nx.draw_networkx_edges(self.G, pos=self.pos, ax=self.ax, edge_color=base_edge_colors)
        edge_labels = nx.get_edge_attributes(self.G, "weight")
        nx.draw_networkx_edge_labels(self.G, pos=self.pos, edge_labels=edge_labels, ax=self.ax)

        # draw MST edges in green
        for (u, v, w) in mst_edges:
            if self.G.has_edge(u, v):
                nx.draw_networkx_edges(self.G, pos=self.pos, edgelist=[(u, v)], ax=self.ax,
                                       width=3.0, edge_color="#6fe07f")
        # highlight currently considered edge
        if isinstance(highlight, tuple) and len(highlight) == 3:
            u, v, w = highlight
            if self.G.has_edge(u, v):
                nx.draw_networkx_edges(self.G, pos=self.pos, edgelist=[(u, v)], ax=self.ax,
                                       width=4.0, edge_color="#ffa500")
        self.ax.set_axis_off()
        self.canvas.draw()

        if isinstance(highlight, tuple):
            self.result_label.setText(f"Considering edge: {highlight[0]} - {highlight[1]} (w={highlight[2]})")
        else:
            self.result_label.setText("Building MST" if mst_edges else "Ready")

    def show_explanation(self):
        algo = self.algo_box.currentText()
        mst_edges = self.steps[-1][1] if self.steps else set()
        total = sum([w for (_, _, w) in mst_edges]) if mst_edges else 0
        if algo == "Prim":
            expl = (
                "<b>Prim's Algorithm</b><br><br>"
                "Starts from a node and grows MST by adding the smallest edge connecting visited to unvisited nodes.<br>"
                "<b>Time Complexity:</b> O(E log V) with a priority queue.<br><br>"
                f"<b>MST total weight:</b> {total}"
            )
        else:
            expl = (
                "<b>Kruskal's Algorithm</b><br><br>"
                "Sorts edges and adds them if they don't form a cycle (using disjoint set / union-find).<br>"
                "<b>Time Complexity:</b> O(E log E).<br><br>"
                f"<b>MST total weight:</b> {total}"
            )
        self.info.setHtml(expl)
        self.result_label.setText("MST completed")

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
    w = MSTPage()
    w.show()
    sys.exit(app.exec_())
