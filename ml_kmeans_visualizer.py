# ml_kmeans_visualizer.py
# Interactive K-Means visualizer (PyQt5 + matplotlib + numpy)
# Features:
# - choose k
# - add points by clicking, remove by right-click
# - drag points and drag centroids manually
# - Start/Step/Run/Stop controls
# - centroids move step-by-step; points recolor on assignment
# - exposes backToHomeSignal for integration

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QSlider, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
import math
import random

random.seed(42)
np.random.seed(42)


class KMeansVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("K-Means Visualizer")
        self.setGeometry(120, 60, 1000, 700)

        # state
        self.points = np.empty((0, 2), dtype=float)   # (N,2)
        self.k = 3
        self.centroids = np.empty((0, 2), dtype=float)  # (k,2)
        self.assignments = np.empty((0,), dtype=int)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._timer_step)
        self.steps = []    # list of callables for iterative animation
        self.step_ptr = 0
        self.speed = 20

        # interaction state
        self._dragging_point = None   # index of dragging point
        self._dragging_centroid = None  # index of centroid dragging

        # UI & canvas
        self._build_ui()
        self._init_demo_data()
        self._init_centroids()
        self._draw()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("K-Means Clustering Visualizer")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("k:"))
        self.k_spin = QSpinBox()
        self.k_spin.setMinimum(1)
        self.k_spin.setMaximum(8)
        self.k_spin.setValue(self.k)
        self.k_spin.valueChanged.connect(self._on_k_change)
        ctrl.addWidget(self.k_spin)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self._on_start)
        ctrl.addWidget(self.start_btn)

        self.step_btn = QPushButton("Step")
        self.step_btn.clicked.connect(self._on_step)
        ctrl.addWidget(self.step_btn)

        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._on_run)
        ctrl.addWidget(self.run_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._on_stop)
        ctrl.addWidget(self.stop_btn)

        ctrl.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(60)
        self.speed_slider.setValue(self.speed)
        self.speed_slider.valueChanged.connect(self._on_speed_change)
        ctrl.addWidget(self.speed_slider)

        self.back_btn = QPushButton("Back to Home")
        self.back_btn.clicked.connect(self._on_back)
        ctrl.addWidget(self.back_btn)

        layout.addLayout(ctrl)

        # matplotlib canvas
        self.figure, self.ax = plt.subplots(figsize=(9, 5))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # connect mouse events
        self.canvas.mpl_connect("button_press_event", self._on_mouse_press)
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self.canvas.mpl_connect("button_release_event", self._on_mouse_release)

    # ---------------- init/demo data ----------------
    def _init_demo_data(self):
        # three cluster demo
        pts = []
        centers = [(-4, -2), (3, -1), (1, 4)]
        for c in centers:
            x = np.random.normal(loc=c[0], scale=0.9, size=(35,))
            y = np.random.normal(loc=c[1], scale=0.9, size=(35,))
            pts.append(np.stack([x, y], axis=1))
        pts = np.vstack(pts)
        np.random.shuffle(pts)
        self.points = pts
        self.assignments = np.zeros(len(self.points), dtype=int)

    def _init_centroids(self):
        # initialize centroids by sampling points (if available) else random
        k = int(self.k_spin.value())
        self.k = k
        if len(self.points) >= k:
            idx = np.random.choice(len(self.points), size=k, replace=False)
            self.centroids = self.points[idx].astype(float)
        else:
            # random in plot range
            self.centroids = np.random.uniform(-6, 6, size=(k, 2))
        self.assignments = np.zeros(len(self.points), dtype=int)

    # ---------------- UI callbacks ----------------
    def _on_k_change(self, v):
        self.k = int(v)
        self._init_centroids()
        self._draw()

    def _on_speed_change(self, v):
        self.speed = int(v)

    def _on_start(self):
        # prepare steps: we will create a sequence of (assign -> update) repeated
        self.steps = []
        iters = 12
        for it in range(iters):
            self.steps.append(self._make_assign_step(it))
            self.steps.append(self._make_update_step(it))
        # final: one extra assign to recolor final clusters
        self.steps.append(self._make_assign_step(iters))
        self.step_ptr = 0
        self._draw()

    def _on_step(self):
        if not self.steps:
            self._on_start()
            return
        if self.step_ptr < len(self.steps):
            fn = self.steps[self.step_ptr]
            fn()
            self.step_ptr += 1
            self._draw()

    def _on_run(self):
        if not self.steps:
            self._on_start()
        interval = max(10, int(1000 / max(1, self.speed)))
        self.timer.start(interval)

    def _on_stop(self):
        if self.timer.isActive():
            self.timer.stop()

    def _on_back(self):
        if self.timer.isActive():
            self.timer.stop()
        self.close()
        self.backToHomeSignal.emit()

    # ---------------- steps: assignment & update ----------------
    def _make_assign_step(self, it):
        def fn():
            if len(self.points) == 0 or len(self.centroids) == 0:
                return
            # compute distances and assign
            dists = np.linalg.norm(self.points[:, None, :] - self.centroids[None, :, :], axis=2)  # (N,k)
            self.assignments = np.argmin(dists, axis=1)
        return fn

    def _make_update_step(self, it):
        def fn():
            if len(self.points) == 0 or len(self.centroids) == 0:
                return
            newc = np.zeros_like(self.centroids)
            for ci in range(self.k):
                mask = (self.assignments == ci)
                if mask.any():
                    newc[ci] = self.points[mask].mean(axis=0)
                else:
                    # leave centroid unchanged if no points assigned
                    newc[ci] = self.centroids[ci]
            # move centroids smoothly: we animate moving centroids halfway to new position to show movement
            self.centroids = (self.centroids + newc) / 2.0
        return fn

    # ---------------- timer step ----------------
    def _timer_step(self):
        if self.step_ptr < len(self.steps):
            fn = self.steps[self.step_ptr]
            fn()
            self.step_ptr += 1
            self._draw()
        else:
            self.timer.stop()

    # ---------------- mouse interaction ----------------
    def _on_mouse_press(self, event):
        if event.inaxes != self.ax:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        # left-click: either start dragging if near a centroid or point, else add point
        if event.button == 1:
            # check centroid proximity
            cidx = self._nearest_centroid_index(x, y, tol=0.5)
            if cidx is not None:
                self._dragging_centroid = cidx
                return
            # check point proximity
            pidx = self._nearest_point_index(x, y, tol=0.35)
            if pidx is not None:
                self._dragging_point = pidx
                return
            # otherwise add point
            self._add_point(x, y)
            self._draw()
        # right-click: remove nearest point if any
        elif event.button == 3:
            pidx = self._nearest_point_index(x, y, tol=0.35)
            if pidx is not None:
                self._remove_point(pidx)
                self._draw()

    def _on_mouse_move(self, event):
        if event.inaxes != self.ax:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        if self._dragging_point is not None:
            self.points[self._dragging_point] = [x, y]
            self._draw()
        elif self._dragging_centroid is not None:
            # move centroid directly
            self.centroids[self._dragging_centroid] = [x, y]
            self._draw()

    def _on_mouse_release(self, event):
        # stop dragging; after moving points or centroid, optionally recompute assignments
        drag_happened = (self._dragging_point is not None) or (self._dragging_centroid is not None)
        self._dragging_point = None
        self._dragging_centroid = None
        if drag_happened:
            # run one assignment step so colors update immediately
            if len(self.points) > 0 and len(self.centroids) > 0:
                self.assignments = np.argmin(np.linalg.norm(self.points[:, None, :] - self.centroids[None, :, :], axis=2), axis=1)
                self._draw()

    # ---------------- point/centroid helpers ----------------
    def _add_point(self, x, y):
        pt = np.array([[float(x), float(y)]])
        if self.points.size == 0:
            self.points = pt
        else:
            self.points = np.vstack([self.points, pt])
        self.assignments = np.zeros(len(self.points), dtype=int)

    def _remove_point(self, idx):
        if 0 <= idx < len(self.points):
            self.points = np.delete(self.points, idx, axis=0)
            self.assignments = np.zeros(len(self.points), dtype=int)

    def _nearest_point_index(self, x, y, tol=0.3):
        if len(self.points) == 0:
            return None
        dists = np.hypot(self.points[:, 0] - x, self.points[:, 1] - y)
        m = dists.min()
        return int(dists.argmin()) if m <= tol else None

    def _nearest_centroid_index(self, x, y, tol=0.6):
        if len(self.centroids) == 0:
            return None
        dists = np.hypot(self.centroids[:, 0] - x, self.centroids[:, 1] - y)
        m = dists.min()
        return int(dists.argmin()) if m <= tol else None

    # ---------------- drawing ----------------
    def _draw(self):
        self.ax.clear()
        # axis limits and grid
        all_x = np.concatenate([self.points[:, 0] if len(self.points) else np.array([]),
                                self.centroids[:, 0] if len(self.centroids) else np.array([])])
        all_y = np.concatenate([self.points[:, 1] if len(self.points) else np.array([]),
                                self.centroids[:, 1] if len(self.centroids) else np.array([])])
        if all_x.size:
            xmin, xmax = all_x.min() - 1, all_x.max() + 1
            ymin, ymax = all_y.min() - 1, all_y.max() + 1
        else:
            xmin, xmax, ymin, ymax = -8, 8, -6, 6
        self.ax.set_xlim(xmin, xmax); self.ax.set_ylim(ymin, ymax)
        self.ax.set_title("K-Means: left-click add/drag points, left-click centroid to drag, right-click remove point")
        self.ax.grid(True)

        # draw points colored by assignment if assignments available
        if len(self.points) > 0 and len(self.centroids) > 0:
            colors = plt.cm.get_cmap("tab10")(range(self.k))
            # ensure assignments length
            if len(self.assignments) != len(self.points):
                self.assignments = np.zeros(len(self.points), dtype=int)
            for ci in range(self.k):
                mask = (self.assignments == ci)
                if mask.any():
                    pts_ci = self.points[mask]
                    self.ax.scatter(pts_ci[:, 0], pts_ci[:, 1], s=28, color=colors[ci], edgecolor="k", zorder=2)
            # any unassigned points (if k changed) show gray
            if len(self.assignments) < len(self.points):
                self.ax.scatter(self.points[:, 0], self.points[:, 1], s=24, color="#888888")
        else:
            # draw unassigned points in blue
            if len(self.points) > 0:
                self.ax.scatter(self.points[:, 0], self.points[:, 1], s=26, color="#1f77b4", zorder=2)

        # draw centroids as X's (bigger)
        if len(self.centroids) > 0:
            colors = plt.cm.get_cmap("tab10")(range(self.k))
            for ci, c in enumerate(self.centroids):
                self.ax.scatter(c[0], c[1], marker="X", s=160, color=colors[ci], edgecolor="k", zorder=5)
                # label centroid index
                self.ax.text(c[0], c[1], f" C{ci}", fontsize=9, verticalalignment="bottom", fontweight="bold")

        self.figure.tight_layout()
        self.canvas.draw()

# Standalone test
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = KMeansVisualizer()
    w.show()
    sys.exit(app.exec_())
