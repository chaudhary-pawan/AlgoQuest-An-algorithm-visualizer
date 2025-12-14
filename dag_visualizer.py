# dag_visualizer.py
# DFS-based Topological Sort visualizer (finish-time ordering)
# Uses PyQt5 + matplotlib + networkx
# Emits backToCategorySignal to return to Graph Hub

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QLineEdit, QSlider, QSizePolicy, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx


class DAGPage(QWidget):
    backToCategorySignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Topological Ordering (DFS Topological Sort)")
        self.setGeometry(100, 60, 1000, 700)

        self.G = nx.DiGraph()
        self.pos = {}
        self.steps = []          # list of (action, node, visited_set, finished_list)
        self.step_ptr = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step_animation)

        self.setup_ui()
        self.default_edges = "5-2,5-0,4-0,4-1,2-3,3-1"
        self.load_and_show(self.default_edges)

    def setup_ui(self):
        main = QVBoxLayout()
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(10)

        title = QLabel("Topological Ordering — DFS Topological Sort")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        controls = QHBoxLayout()
        self.edge_input = QLineEdit()
        self.edge_input.setPlaceholderText("Directed edges (u-v) comma separated. Example: 5-2,5-0,4-0")
        controls.addWidget(self.edge_input, 1)

        load_btn = QPushButton("Load DAG")
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
        self.speed_slider.setMaximum(1000)
        self.speed_slider.setValue(400)
        row2.addWidget(self.speed_slider, 1)

        self.start_btn = QPushButton("Start Topological Sort")
        self.start_btn.clicked.connect(self.on_start)
        self.start_btn.setFixedWidth(180)
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
        self.result_label.setAlignment(Qt.AlignCenter)
        main.addWidget(self.result_label)

        # Matplotlib canvas (embedded)
        self.figure, self.ax = plt.subplots(figsize=(9, 4))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main.addWidget(self.canvas)

        # Explanation / ordering text
        self.info = QTextEdit()
        self.info.setReadOnly(True)
        self.info.setFixedHeight(220)
        main.addWidget(self.info)

        self.setLayout(main)

    # ---------------- parsing & graph building ----------------
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
        self.G = nx.DiGraph()
        self.G.add_edges_from(edges)
        if len(self.G.nodes) == 0:
            self.G.add_node(0)
        try:
            self.pos = nx.spring_layout(self.G, seed=42)
        except Exception:
            self.pos = nx.circular_layout(self.G)

    def load_and_show(self, edges_text):
        try:
            edges = self.parse_edges(edges_text)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid edges", str(e))
            return
        self.build_graph(edges)
        # draw with consistent signature: current, visited, finished
        self.draw_graph(current=None, visited=set(), finished=set())
        self.result_label.setText("DAG loaded. Click Start to run DFS topological sort.")
        self.info.clear()

    def on_load_graph(self):
        txt = self.edge_input.text().strip()
        if not txt:
            txt = self.default_edges
        self.load_and_show(txt)

    # ---------------- DFS topological sort preparation ----------------
    def on_start(self):
        if self.timer.isActive():
            self.timer.stop()
        self.steps = []
        self.step_ptr = 0
        self.result_label.setText("")
        self.info.clear()

        # check for cycles first (quick detection)
        if not nx.is_directed_acyclic_graph(self.G):
            QMessageBox.warning(self, "Not a DAG", "The graph contains a cycle. Topological ordering is not possible.")
            return

        # Prepare DFS-based topological order and record steps
        visited = set()
        finished_stack = []
        for node in list(self.G.nodes()):
            if node not in visited:
                self._dfs_record(node, visited, finished_stack)
        # final snapshot to show completed ordering (reversed finished stack)
        self.steps.append(("final", None, set(visited), list(reversed(finished_stack))))
        self.timer.start(self.speed_slider.value())

    def _dfs_record(self, start, visited, finished_stack):
        def dfs(u):
            visited.add(u)
            # record enter
            self.steps.append(("enter", u, set(visited), list(finished_stack)))
            for v in sorted(self.G.successors(u), key=lambda x: str(x)):
                if v not in visited:
                    dfs(v)
            # finished (post-order)
            finished_stack.append(u)
            self.steps.append(("exit", u, set(visited), list(finished_stack)))
        dfs(start)

    # ---------------- animation step ----------------
    def step_animation(self):
        if self.step_ptr >= len(self.steps):
            self.timer.stop()
            self.show_explanation_final()
            return

        action, node, visited_snapshot, finished_list = self.steps[self.step_ptr]
        if action == "enter":
            self.draw_graph(current=node, visited=visited_snapshot, finished=set(finished_list))
            self.result_label.setText(f"Discovered: {node}")
        elif action == "exit":
            self.draw_graph(current=None, visited=visited_snapshot, finished=set(finished_list))
            self.result_label.setText(f"Finished: {node}")
        elif action == "final":
            self.draw_graph(current=None, visited=visited_snapshot if visited_snapshot is not None else set(self.G.nodes()),
                            finished=set(finished_list if finished_list is not None else []))
            self.result_label.setText("Topological ordering complete")
        else:
            self.draw_graph(current=None, visited=visited_snapshot or set(), finished=set(finished_list or []))

        self.step_ptr += 1

    # ---------------- drawing ----------------
    def draw_graph(self, current=None, visited=None, finished=None):
        if visited is None:
            visited = set()
        if finished is None:
            finished = set()

        self.ax.clear()
        node_colors = []
        for n in self.G.nodes():
            if n == current:
                node_colors.append("#ffa500")     # current (orange)
            elif n in finished:
                node_colors.append("#6fe07f")     # finished (green)
            elif n in visited:
                node_colors.append("#7fb3ff")     # visited but not finished (blue)
            else:
                node_colors.append("#dddddd")     # unvisited (grey)
        nx.draw_networkx_edges(self.G, pos=self.pos, ax=self.ax, edge_color="#888888", arrows=True)
        nx.draw_networkx_nodes(self.G, pos=self.pos, ax=self.ax, node_color=node_colors, node_size=700)
        nx.draw_networkx_labels(self.G, pos=self.pos, ax=self.ax, font_size=10)
        self.ax.set_axis_off()
        self.canvas.draw()

    def show_explanation_final(self):
        # find final snapshot
        last = None
        for step in reversed(self.steps):
            if step[0] == "final":
                last = step
                break
        if last:
            _, _, _, finished_list = last
            topo_order = finished_list or []
            expl = (
                "<b>Topological Sort (DFS-based)</b><br><br>"
                "This uses DFS finishing times: when a node's DFS call finishes, "
                "we append it to a list; reversing that list gives a valid topological order.<br><br>"
                "<b>Time Complexity:</b> O(V + E).<br><br>"
                f"<b>Topological Order:</b> {', '.join(map(str, topo_order))}"
            )
        else:
            expl = (
                "<b>Topological Sort (DFS-based)</b><br><br>"
                "No ordering produced."
            )
        self.info.setHtml(expl)

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


# Standalone test
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = DAGPage()
    w.show()
    sys.exit(app.exec_())
