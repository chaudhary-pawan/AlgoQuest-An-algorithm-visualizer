from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from sorting_visualizer import SortingVisualizer
from search_visualizer import SearchingVisualizer   # ✅ Corrected import name
from graph_visualizer import GraphVisualizer
from dp_visualizer import DPVisualizer
from ml_visualizer import MLVisualizer
import sys


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlgoQUIST - Algorithm Visualizer Hub")
        self.setGeometry(300, 100, 600, 400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        title = QLabel("AlgoQUIST", self)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        subtitle = QLabel("Explore and Visualize Algorithms", self)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #34495e;")
        layout.addWidget(subtitle)

        # Buttons for each visualizer
        btn_sort = QPushButton("Sorting Visualizer", self)
        btn_sort.clicked.connect(self.open_sorting)
        layout.addWidget(btn_sort)

        btn_search = QPushButton("Searching Visualizer", self)
        btn_search.clicked.connect(self.open_searching)
        layout.addWidget(btn_search)

        btn_graph = QPushButton("Graph Visualizer", self)
        btn_graph.clicked.connect(self.open_graph)
        layout.addWidget(btn_graph)

        btn_dp = QPushButton("Dynamic Programming Visualizer", self)
        btn_dp.clicked.connect(self.open_dp)
        layout.addWidget(btn_dp)

        btn_ml = QPushButton("Machine Learning Visualizer", self)
        btn_ml.clicked.connect(self.open_ml)
        layout.addWidget(btn_ml)

        # Button Styling
        for btn in [btn_sort, btn_search, btn_graph, btn_dp, btn_ml]:
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    padding: 10px;
                    border-radius: 10px;
                    background-color: #ecf0f1;
                }
                QPushButton:hover {
                    background-color: #dcdde1;
                }
            """)

        self.setLayout(layout)

    # ----- Window Navigation Methods -----

    def open_sorting(self):
        self.hide()
        self.sort_window = SortingVisualizer()
        self.sort_window.backToHomeSignal.connect(self.show)
        self.sort_window.show()

    def open_searching(self):
        self.hide()
        self.search_window = SearchingVisualizer()  # ✅ Correct class name
        self.search_window.backToHomeSignal.connect(self.show)
        self.search_window.show()

    def open_graph(self):
        self.hide()
        self.graph_window = GraphVisualizer()
        self.graph_window.backToHomeSignal.connect(self.show)
        self.graph_window.show()

    def open_dp(self):
        self.hide()
        self.dp_window = DPVisualizer()
        self.dp_window.backToHomeSignal.connect(self.show)
        self.dp_window.show()

    def open_ml(self):
        self.hide()
        self.ml_window = MLVisualizer()
        self.ml_window.backToHomeSignal.connect(self.show)
        self.ml_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
