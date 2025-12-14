# ml_regression_visualizer.py
# Interactive Linear & Polynomial Regression Visualizer (PyQt5 + matplotlib)
# - Left-click add / drag points, right-click remove
# - Batch vs Stochastic GD, learning-rate slider
# - Degree selector for polynomial regression
# - Cost curve and model fit plot
# - Back to ML Visualizer (backToHomeSignal)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QSpinBox, QSlider, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
import random, math

random.seed(42)
np.random.seed(42)


class RegressionVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Regression Visualizer")
        self.setGeometry(120, 60, 1100, 700)

        # state
        self.points = []            # list of (x,y)
        self.degree = 1
        self.params = None
        self.learning_rate = 0.01
        self.mode = "Batch"         # "Batch" or "Stochastic"
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._timer_step)
        self.steps = []             # list of functions to execute for animation
        self.step_ptr = 0
        self.cost_history = []
        self._dragging_idx = None
        self._dragging = False

        # build UI + init
        self._build_ui()
        self._init_demo_points()
        self._init_model()
        self._draw_all(initial=True)

    # ---------------- UI ----------------
    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Regression Visualizer — Linear & Polynomial")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # controls row
        controls = QHBoxLayout()
        controls.setSpacing(8)

        controls.addWidget(QLabel("Mode:"))
        self.mode_box = QComboBox()
        self.mode_box.addItems(["Batch", "Stochastic"])
        self.mode_box.currentTextChanged.connect(self._on_mode_change)
        controls.addWidget(self.mode_box)

        controls.addWidget(QLabel("Degree:"))
        self.degree_spin = QSpinBox()
        self.degree_spin.setMinimum(1); self.degree_spin.setMaximum(6); self.degree_spin.setValue(1)
        self.degree_spin.valueChanged.connect(self._on_degree_change)
        controls.addWidget(self.degree_spin)

        controls.addWidget(QLabel("LR:"))
        self.lr_slider = QSlider(Qt.Horizontal)
        self.lr_slider.setMinimum(1); self.lr_slider.setMaximum(1000); self.lr_slider.setValue(10)
        self.lr_slider.valueChanged.connect(self._on_lr_change)
        controls.addWidget(self.lr_slider)
        self.lr_label = QLabel("0.010")
        self.lr_label.setFixedWidth(60)
        controls.addWidget(self.lr_label)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self._on_start)
        controls.addWidget(self.start_btn)

        self.step_btn = QPushButton("Step")
        self.step_btn.clicked.connect(self._on_step)
        controls.addWidget(self.step_btn)

        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._on_run)
        controls.addWidget(self.run_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._on_stop)
        controls.addWidget(self.stop_btn)

        controls.addWidget(QLabel("Steps/sec:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1); self.speed_slider.setMaximum(60); self.speed_slider.setValue(20)
        controls.addWidget(self.speed_slider)

        self.back_btn = QPushButton("Back to ML Visualizer")
        self.back_btn.clicked.connect(self._on_back)
        controls.addWidget(self.back_btn)

        layout.addLayout(controls)

        # Matplotlib figure with 2 subplots
        self.figure, (self.ax_data, self.ax_cost) = plt.subplots(1, 2, figsize=(11, 5))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas)

        footer = QLabel("Left-click add / drag points. Right-click remove. Dragging triggers instant re-learn.")
        footer.setAlignment(Qt.AlignLeft)
        layout.addWidget(footer)

        self.setLayout(layout)

        # connect mpl events
        self.canvas.mpl_connect("button_press_event", self._on_mouse_press)
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self.canvas.mpl_connect("button_release_event", self._on_mouse_release)

        # initialize LR display
        self._on_lr_change(self.lr_slider.value())

    # ---------------- initial data & model ----------------
    def _init_demo_points(self):
        # a non-linear-ish demo so polynomial shows benefit sometimes
        xs = np.linspace(-6, 6, 12)
        ys = 1.6 * xs - 0.5 + np.random.normal(scale=2.0, size=xs.shape)
        self.points = [(float(x), float(y)) for x, y in zip(xs, ys)]

    def _init_model(self):
        d = max(1, self.degree)
        self.params = np.random.normal(scale=0.1, size=(d + 1,))
        self.cost_history = []

    # ---------------- UI callbacks ----------------
    def _on_mode_change(self, v):
        self.mode = v

    def _on_degree_change(self, v):
        self.degree = int(v)
        self._init_model()
        self._draw_all()

    def _on_lr_change(self, v):
        # map slider (1..1000) to lr 1e-4 .. 1
        # use exponential mapping for good range
        normalized = (v - 1) / 999.0
        lr = 10 ** (-4 + 4 * normalized)  # 1e-4 .. 1e0
        self.learning_rate = float(lr)
        self.lr_label.setText(f"{self.learning_rate:.3f}")

    def _on_start(self):
        # prepare steps and reset
        self.step_ptr = 0
        self.cost_history = []
        self._prepare_steps()
        self._draw_all(initial=True)

    def _on_step(self):
        if not self.steps:
            self._on_start()
            return
        if self.step_ptr < len(self.steps):
            fn = self.steps[self.step_ptr]
            fn()
            self.step_ptr += 1
            self._draw_all()
        else:
            # done
            pass

    def _on_run(self):
        if not self.steps:
            self._on_start()
        fps = max(1, self.speed_slider.value())
        interval = int(1000 / fps)
        self.timer.start(interval)

    def _on_stop(self):
        if self.timer.isActive():
            self.timer.stop()

    def _on_back(self):
        if self.timer.isActive():
            self.timer.stop()
        self.close()
        self.backToHomeSignal.emit()

    # ---------------- mouse events ----------------
    def _on_mouse_press(self, event):
        if event.inaxes != self.ax_data:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        if event.button == 1:  # left click -> add or start dragging
            idx = self._nearest_point_index(x, y, tol=0.35)
            if idx is None:
                self.points.append((float(x), float(y)))
                # auto update visualization slightly
                self._quick_retrain(steps=6)
                self._draw_all()
            else:
                self._dragging_idx = idx
                self._dragging = True
        elif event.button == 3:  # right click -> remove nearest
            idx = self._nearest_point_index(x, y, tol=0.35)
            if idx is not None:
                self.points.pop(idx)
                self._draw_all()

    def _on_mouse_move(self, event):
        if not self._dragging:
            return
        if event.inaxes != self.ax_data:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        if self._dragging_idx is not None and 0 <= self._dragging_idx < len(self.points):
            self.points[self._dragging_idx] = (float(x), float(y))
            # show moving point live
            self._draw_all()

    def _on_mouse_release(self, event):
        if self._dragging:
            # perform small retrain to update model quickly
            self._quick_retrain(steps=10)
        self._dragging_idx = None
        self._dragging = False

    def _nearest_point_index(self, x, y, tol=0.3):
        if not self.points:
            return None
        dists = [math.hypot(px - x, py - y) for px, py in self.points]
        m = min(dists)
        return dists.index(m) if m <= tol else None

    # ---------------- prepare steps for GD ----------------
    def _prepare_steps(self):
        # Build design matrix and target vector
        X, Y = self._design_matrix_targets()
        n = X.shape[0]
        lr = self.learning_rate
        steps = []
        if self.mode == "Batch":
            max_iters = 300
            for _ in range(max_iters):
                def make_batch():
                    def fn():
                        nonlocal X, Y, lr, n
                        preds = X.dot(self.params)
                        err = preds - Y
                        grad = (2.0 / n) * X.T.dot(err)
                        self.params = self.params - lr * grad
                        self.cost_history.append(float((err ** 2).mean()))
                    return fn
                steps.append(make_batch())
        else:  # Stochastic
            epochs = 30
            idxs = list(range(n))
            for _ in range(epochs):
                random.shuffle(idxs)
                for i in idxs:
                    def make_sgd(i=i):
                        def fn():
                            nonlocal X, Y, lr
                            xi = X[i:i+1, :]
                            yi = Y[i]
                            pred = float(xi.dot(self.params))
                            err = pred - yi
                            grad = 2.0 * xi.T * err
                            self.params = self.params - lr * grad.flatten()
                            # append full MSE for bookkeeping
                            preds = X.dot(self.params)
                            self.cost_history.append(float(((preds - Y) ** 2).mean()))
                        return fn
                    steps.append(make_sgd())
        self.steps = steps
        self.step_ptr = 0

    def _quick_retrain(self, steps=5):
        # small immediate updates using batch GD for responsiveness
        X, Y = self._design_matrix_targets()
        n = X.shape[0]
        lr = self.learning_rate
        for _ in range(steps):
            preds = X.dot(self.params)
            err = preds - Y
            grad = (2.0 / n) * X.T.dot(err)
            self.params = self.params - lr * grad
            self.cost_history.append(float((err ** 2).mean()))
        self._draw_all()

    def _design_matrix_targets(self):
        if not self.points:
            pts = [(-3.0, -6.0), (0.0, 0.0), (3.0, 6.0)]
        else:
            pts = self.points
        xs = np.array([p[0] for p in pts], dtype=float)
        ys = np.array([p[1] for p in pts], dtype=float)
        X = np.vander(xs, N=self.degree + 1, increasing=True)  # columns [1, x, x^2 ...]
        return X, ys

    # ---------------- drawing ----------------
    def _draw_all(self, initial=False):
        self.ax_data.clear(); self.ax_cost.clear()

        # points
        if self.points:
            pts = np.array(self.points)
            self.ax_data.scatter(pts[:, 0], pts[:, 1], color="#1f77b4", s=50, zorder=3)
            for i, (px, py) in enumerate(self.points):
                self.ax_data.text(px, py, f"{i}", fontsize=8, verticalalignment="bottom")
            x_min, x_max = pts[:, 0].min() - 1, pts[:, 0].max() + 1
        else:
            x_min, x_max = -6, 6

        # model line / curve
        if self.params is not None:
            Xplot = np.linspace(x_min, x_max, 400)
            preds_plot = np.vander(Xplot, N=len(self.params), increasing=True).dot(self.params)
            self.ax_data.plot(Xplot, preds_plot, color="#ff7f0e", linewidth=2, label="Model")

        self.ax_data.set_title("Data & Model Fit — click to add, drag to move, right-click to delete")
        self.ax_data.grid(True)

        # cost plot
        if self.cost_history:
            self.ax_cost.plot(self.cost_history, color="#2ca02c")
            self.ax_cost.set_title("Cost (MSE)")
            self.ax_cost.set_xlabel("Step")
            self.ax_cost.set_ylabel("MSE")
            self.ax_cost.text(0.98, 0.95, f"Cost={self.cost_history[-1]:.4f}", transform=self.ax_cost.transAxes, ha="right")
        else:
            self.ax_cost.set_title("Cost (MSE)")
            self.ax_cost.text(0.5, 0.5, "No cost computed", transform=self.ax_cost.transAxes, ha="center", va="center")

        self.figure.tight_layout()
        self.canvas.draw()

    # ---------------- timer loop ----------------
    def _timer_step(self):
        if self.step_ptr < len(self.steps):
            fn = self.steps[self.step_ptr]
            fn()
            self.step_ptr += 1
            self._draw_all()
        else:
            self.timer.stop()

    # ---------------- standalone test ----------------
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = RegressionVisualizer()
    w.show()
    sys.exit(app.exec_())
