from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QMessageBox, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush, QPen, QIcon
import sys
import os


COL_NEON_DEFAULT = "#80fac0"
COL_DARK_FRAME = "rgba(30, 45, 55, 200)"

GRADIENT_COLOR_0 = QColor(15, 32, 39)
GRADIENT_COLOR_1 = QColor(20, 40, 50)
GRADIENT_COLOR_2 = QColor(30, 60, 70)


class GraphVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graph Algorithms - Hub - AlgoQUEST")
        self.setGeometry(120, 80, 1000, 700)
        self._open_window = None

        self.setStyleSheet(self._get_style_sheet())
        self.init_ui()

    # ---------- background ----------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, GRADIENT_COLOR_0)
        grad.setColorAt(0.5, GRADIENT_COLOR_1)
        grad.setColorAt(1.0, GRADIENT_COLOR_2)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawRect(self.rect())

        pen = QPen(QColor(80, 250, 220, 20))
        pen.setWidth(2)
        p.setPen(pen)
        step = 40
        for x in range(0, w, step):
            for y in range(0, h, step):
                p.drawPoint(x, y)

    # ---------- stylesheet ----------
    def _get_style_sheet(self):
        return f"""
        QWidget {{
            background: transparent;
            color: #dbeaf2;
            font-family: "Segoe UI", "Arial";
        }}

        QLabel#title_label {{
            color: {COL_NEON_DEFAULT};
            font-size: 34px;     /* larger title */
            font-weight: 900;
        }}

        QLabel#subtitle_label {{
            color: #aabdc9;
            font-size: 20px;     /* larger subtitle */
        }}

        QPushButton.category_btn {{
            background-color: {COL_DARK_FRAME};
            border: 2px solid {COL_NEON_DEFAULT};
            border-radius: 14px;
            color: #dbeaf2;
            font-weight: bold;
            font-size: 14px;
            padding: 16px;
            min-width: 230px;
            min-height: 115px;
            max-width: 260px;
            max-height: 130px;
            text-align: center;
            icon-size: 40px;
        }}
        QPushButton.category_btn:hover {{
            background-color: rgba(40, 60, 70, 200);
            border-color: #a0fcd0;
        }}
        QPushButton.category_btn:pressed {{
            background-color: rgba(20, 30, 40, 200);
        }}

        QPushButton#back_button {{
            background-color: rgba(255,255,255,0.04);
            border-radius: 8px;
            border: 1px solid #80fac0;
            padding: 6px 14px;
            font-size: 13px;
            color: #80fac0;
        }}
        QPushButton#back_button:hover {{
            background-color: rgba(80,250,220,0.15);
        }}
        """

    # ---------- helpers ----------
    def _get_icon_path(self, icon_name):
        base_path = os.path.dirname(__file__)
        return os.path.join(base_path, "icons", icon_name)

    # ---------- UI ----------
    def init_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(50, 30, 50, 40)
        main.setSpacing(20)

        # top bar with back button
        top_bar = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("back_button")
        back_btn.setIcon(QIcon(self._get_icon_path("home_icon.png")))
        back_btn.clicked.connect(self.go_back_home)
        top_bar.addWidget(back_btn, 0, Qt.AlignLeft)
        top_bar.addStretch(1)
        main.addLayout(top_bar)

        # title + subtitle block
        title_block = QVBoxLayout()
        title_block.setSpacing(4)

        title = QLabel("Graph Algorithm Visualizer")
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignCenter)
        title_block.addWidget(title)

        subtitle = QLabel("Choose a category to explore algorithms")
        subtitle.setObjectName("subtitle_label")
        subtitle.setAlignment(Qt.AlignCenter)
        title_block.addWidget(subtitle)

        main.addLayout(title_block)

        # center grid for 4 buttons (2x2)
        center_row = QHBoxLayout()
        center_row.addStretch(1)

        grid = QGridLayout()
        grid.setHorizontalSpacing(30)
        grid.setVerticalSpacing(25)

        btn_traversal = QPushButton("Traversal\n(BFS, DFS)")
        btn_traversal.setProperty("class", "category_btn")
        btn_traversal.setIcon(QIcon(self._get_icon_path("traversal_icon.png")))
        btn_traversal.clicked.connect(self.open_traversal)

        btn_shortest = QPushButton("Shortest Path\n(Dijkstra, Bellman-Ford)")
        btn_shortest.setProperty("class", "category_btn")
        btn_shortest.setIcon(QIcon(self._get_icon_path("shortest_path_icon.png")))
        btn_shortest.clicked.connect(self.open_shortest)

        btn_mst = QPushButton("Minimum Spanning Tree\n(Prim, Kruskal)")
        btn_mst.setProperty("class", "category_btn")
        btn_mst.setIcon(QIcon(self._get_icon_path("mst_icon.png")))
        btn_mst.clicked.connect(self.open_mst)

        btn_dag = QPushButton("Topological Ordering\n(Topological Sort, Kahn)")
        btn_dag.setProperty("class", "category_btn")
        btn_dag.setIcon(QIcon(self._get_icon_path("dag_icon.png")))
        btn_dag.clicked.connect(self.open_dag)

        grid.addWidget(btn_traversal, 0, 0)
        grid.addWidget(btn_shortest, 0, 1)
        grid.addWidget(btn_mst, 1, 0)
        grid.addWidget(btn_dag, 1, 1)

        center_row.addLayout(grid)
        center_row.addStretch(1)

        main.addSpacing(10)
        main.addLayout(center_row)
        main.addStretch(1)

        self.setLayout(main)

    # ---------- dynamic import ----------
    def import_and_open(self, module_name: str, class_name: str):
        try:
            module = __import__(module_name)
            cls = getattr(module, class_name)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Module not available",
                f"Cannot open {module_name}.{class_name}.\n\nError: {e}",
            )
            return

        try:
            self._open_window = cls()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error opening page",
                f"Failed to create {class_name} from {module_name}.\n\nError: {e}",
            )
            return

        if hasattr(self._open_window, "backToCategorySignal"):
            self._open_window.backToCategorySignal.connect(self.show)
        elif hasattr(self._open_window, "backToHomeSignal"):
            self._open_window.backToHomeSignal.connect(self.show)
        else:
            self._open_window.destroyed.connect(self.show)

        self.hide()
        self._open_window.show()

    # ---------- handlers ----------
    def open_traversal(self):
        self.import_and_open("graph_traversal", "GraphTraversalPage")

    def open_shortest(self):
        self.import_and_open("shortest_path", "ShortestPathPage")

    def open_mst(self):
        self.import_and_open("mst_visualizer", "MSTPage")

    def open_dag(self):
        self.import_and_open("dag_visualizer", "DAGPage")

    def go_back_home(self):
        self.close()
        self.backToHomeSignal.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = GraphVisualizer()
    w.show()
    sys.exit(app.exec_())
