import sys
import numpy as np
import pandas as pd
import graphviz
from collections import deque

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# =========================================================
# ENTROPY
# =========================================================
class EntropyCalculator:
    @staticmethod
    def entropy(y):
        values, counts = np.unique(y, return_counts=True)
        probs = counts / counts.sum()
        return -np.sum(probs * np.log2(probs + 1e-9))


# =========================================================
# DECISION TREE SIMULATOR (STEP BASED)
# =========================================================
class DecisionTreeSimulator:

    def __init__(self):
        self.steps = deque()
        self.node_id = 0
        self.dot = graphviz.Digraph(format="png")
        self.dot.attr(rankdir="TB")

    def load_play_tennis(self):
        self.df_raw = pd.DataFrame({
            "Outlook": ["Sunny","Sunny","Overcast","Rain","Rain","Rain","Overcast",
                        "Sunny","Sunny","Rain","Sunny","Overcast","Overcast","Rain"],
            "Temperature": ["Hot","Hot","Hot","Mild","Cool","Cool","Cool",
                            "Hot","Cool","Mild","Mild","Hot","Cool","Mild"],
            "Humidity": ["High","High","High","High","Normal","Normal","Normal",
                         "High","Normal","Normal","Normal","High","Normal","High"],
            "Wind": ["Weak","Strong","Weak","Weak","Weak","Strong","Strong",
                     "Weak","Weak","Weak","Strong","Strong","Weak","Strong"],
            "Play": ["No","No","Yes","Yes","Yes","No","Yes",
                     "No","Yes","Yes","Yes","Yes","Yes","No"]
        })

        self.df = self.df_raw.copy()
        self.encodings = {}

        for col in self.df.columns:
            self.df[col] = self.df[col].astype("category")
            self.encodings[col] = dict(enumerate(self.df[col].cat.categories))
            self.df[col] = self.df[col].cat.codes

        self.features = ["Outlook", "Temperature", "Humidity", "Wind"]
        self.target = "Play"

    def prepare_steps(self):
        self.steps.clear()
        self.node_id = 0
        self.dot = graphviz.Digraph(format="png")
        self.dot.attr(rankdir="TB")

        X = self.df[self.features].values
        y = self.df[self.target].values

        stack = [(X, y, None, "Root")]

        while stack:
            X, y, parent, edge = stack.pop()

            entropy = EntropyCalculator.entropy(y)
            self.steps.append(("entropy", entropy, len(y)))

            if len(np.unique(y)) == 1:
                nid = self.new_node()
                self.steps.append(("leaf", nid, entropy, len(y), parent, edge))
                continue

            gains = {}
            for i, f in enumerate(self.features):
                g = self.information_gain(X, y, i, entropy)
                gains[f] = g
                self.steps.append(("gain", f, g))

            best = max(gains, key=gains.get)
            self.steps.append(("best", best, gains[best]))

            nid = self.new_node()
            self.steps.append(("node", nid, best, gains[best], entropy, parent, edge))

            idx = self.features.index(best)
            for v in np.unique(X[:, idx]):
                mask = X[:, idx] == v
                stack.append((X[mask], y[mask], nid, f"{best}={v}"))

    def information_gain(self, X, y, idx, parent_entropy):
        weighted = 0
        for v in np.unique(X[:, idx]):
            subset = y[X[:, idx] == v]
            weighted += (len(subset) / len(y)) * EntropyCalculator.entropy(subset)
        return parent_entropy - weighted

    def new_node(self):
        nid = f"N{self.node_id}"
        self.node_id += 1
        return nid

    def execute_step(self, step):
        t = step[0]

        if t == "node":
            _, nid, f, g, e, parent, edge = step
            label = f"{f}\nGain: {g:.3f}\nEntropy: {e:.3f}"
            self.dot.node(
                nid, label,
                style="filled",
                fillcolor="#1e2d37",
                fontcolor="#80fac0"
            )
            if parent:
                self.dot.edge(parent, nid, label=edge)

        elif t == "leaf":
            _, nid, e, s, parent, edge = step
            label = f"Leaf\nSamples:{s}\nEntropy:{e:.3f}"
            self.dot.node(
                nid, label,
                shape="box",
                style="filled",
                fillcolor="#80fac0"
            )
            if parent:
                self.dot.edge(parent, nid, label=edge)


# =========================================================
# DISTRIBUTION CHART
# =========================================================
class DistributionChart(FigureCanvas):
    def __init__(self):
        self.fig = Figure(facecolor="#0f2027")
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)

    def plot(self, series):
        self.ax.clear()
        series.value_counts().plot(
            kind="bar", ax=self.ax,
            color=["#1f77b4", "#ff7f0e"]
        )
        self.ax.set_title("Target Distribution", color="white")
        self.ax.set_xlabel("Play", color="white")
        self.ax.set_ylabel("Count", color="white")
        self.ax.tick_params(colors="white")
        self.ax.set_facecolor("#0f2027")
        self.fig.tight_layout()
        self.draw()


# =========================================================
# UI
# =========================================================
class DecisionTreeVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlgoQUEST – Decision Tree")
        self.resize(1400, 800)

        self.setStyleSheet("""
            QWidget { background-color:#0f2027; color:white; font-family:Segoe UI; }
            QLabel { color:white; }
            QTextEdit { background:#13232c; color:white; border:1px solid #80fac0; }
            QTableWidget { background:#13232c; color:white; gridline-color:#80fac0; }
            QHeaderView::section { background:#1e2d37; color:white; padding:6px; }
            QPushButton { background:#1e2d37; color:white; padding:8px; }
            QPushButton:hover { background:#80fac0; color:black; }
        """)

        self.sim = DecisionTreeSimulator()
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_step)

        self.init_ui()

    def init_ui(self):
        main = QHBoxLayout(self)

        # LEFT
        left = QVBoxLayout()

        title = QLabel("Decision Tree Simulator")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color:#80fac0;")
        left.addWidget(title)

        self.start_btn = QPushButton("Start Simulation")
        self.start_btn.clicked.connect(self.start)
        left.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        left.addWidget(self.pause_btn)

        self.back_btn = QPushButton("⬅ Back to ML Algorithms")
        self.back_btn.clicked.connect(self.go_back)
        left.addWidget(self.back_btn)

        left.addWidget(QLabel("Dataset Preview"))

        self.table = QTableWidget()
        self.table.setMinimumHeight(320)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.horizontalHeader().setStretchLastSection(True)
        left.addWidget(self.table)

        self.chart = DistributionChart()
        left.addWidget(self.chart)

        left.addWidget(QLabel("Feature Encoding"))
        self.encoding_box = QTextEdit()
        self.encoding_box.setReadOnly(True)
        self.encoding_box.setMinimumHeight(180)
        left.addWidget(self.encoding_box)

        # RIGHT
        right = QVBoxLayout()

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        right.addWidget(self.log, 2)

        self.image = QLabel("Decision Tree Visualization")
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setStyleSheet("border:2px solid #80fac0;")
        right.addWidget(self.image, 3)

        main.addLayout(left, 2)
        main.addLayout(right, 3)

    # -------------------------------
    def start(self):
        self.log.clear()
        self.sim.load_play_tennis()
        self.sim.prepare_steps()
        self.steps = iter(self.sim.steps)
        self.timer.start(800)

        self.load_table()
        self.chart.plot(self.sim.df_raw["Play"])
        self.show_encodings()

    def toggle_pause(self):
        if self.timer.isActive():
            self.timer.stop()
            self.pause_btn.setText("▶ Resume")
        else:
            self.timer.start(800)
            self.pause_btn.setText("⏸ Pause")

    def go_back(self):
        self.timer.stop()
        self.close()
        self.backToHomeSignal.emit()

    def next_step(self):
        try:
            step = next(self.steps)
        except StopIteration:
            self.timer.stop()
            self.sim.dot.render("decision_tree_final", cleanup=True)
            self.update_image()
            return

        if step[0] == "entropy":
            self.log.append(f"Entropy = {step[1]:.3f}, Samples = {step[2]}")
        elif step[0] == "gain":
            self.log.append(f"Gain({step[1]}) = {step[2]:.3f}")
        elif step[0] == "best":
            self.log.append(f"→ Best Feature: {step[1]}")
        else:
            self.sim.execute_step(step)
            self.sim.dot.render("decision_tree_final", cleanup=True)
            self.update_image()

    def load_table(self):
        df = self.sim.df_raw
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df)):
            for j in range(len(df.columns)):
                self.table.setItem(
                    i, j,
                    QTableWidgetItem(str(df.iloc[i, j]))
                )

    def show_encodings(self):
        text = ""
        for k, v in self.sim.encodings.items():
            text += f"{k}: {v}\n\n"
        self.encoding_box.setText(text)

    def update_image(self):
        pix = QPixmap("decision_tree_final.png")
        if not pix.isNull():
            self.image.setPixmap(
                pix.scaled(
                    self.image.width(),
                    self.image.height(),
                    Qt.KeepAspectRatio
                )
            )


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DecisionTreeVisualizer()
    w.show()
    sys.exit(app.exec_())
