# ml_ann_visualizer.py
# Simple ANN visualizer (3-layer: input(2) -> hidden -> output(1))
# PyQt5 + matplotlib + numpy
# Save as ml_ann_visualizer.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSpinBox, QSlider, QSizePolicy, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
import random, math

random.seed(0)
np.random.seed(0)


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def dsigmoid(x):
    s = sigmoid(x)
    return s * (1 - s)


def relu(x):
    return np.maximum(0, x)


def drelu(x):
    return (x > 0).astype(float)


class ANNVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ANN Visualizer (3-layer)")
        self.setGeometry(120, 60, 1100, 760)

        # dataset: list of (x1,x2,label)
        self.data = []
        self._init_demo_data()

        # network architecture
        self.input_dim = 2
        self.hidden_units = 4
        self.activation_name = "ReLU"  # or "Sigmoid"

        # parameters
        self.W1 = None  # shape (hidden_units, input_dim)
        self.b1 = None  # shape (hidden_units,)
        self.W2 = None  # shape (1, hidden_units)
        self.b2 = None  # scalar

        # training state
        self.learning_rate = 0.05
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._timer_step)
        self.steps = []  # functions to perform steps (SGD updates)
        self.step_ptr = 0
        self.loss_history = []

        # visualization mapping
        self.node_positions = {}  # dict layer->list of (x,y)
        self.node_radius = 0.25

        # UI
        self._build_ui()
        self._init_model()
        self._draw_full()

    # ---------------- UI ----------------
    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("ANN Visualizer — Simple 3-layer network")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # controls row
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Hidden units:"))
        self.hidden_spin = QSpinBox(); self.hidden_spin.setMinimum(1); self.hidden_spin.setMaximum(12)
        self.hidden_spin.setValue(self.hidden_units); self.hidden_spin.valueChanged.connect(self._on_hidden_change)
        ctrl.addWidget(self.hidden_spin)

        ctrl.addWidget(QLabel("Activation:"))
        self.act_box = QComboBox(); self.act_box.addItems(["ReLU", "Sigmoid"])
        self.act_box.currentTextChanged.connect(self._on_activation_change)
        ctrl.addWidget(self.act_box)

        ctrl.addWidget(QLabel("LR:"))
        self.lr_slider = QSlider(Qt.Horizontal); self.lr_slider.setMinimum(1); self.lr_slider.setMaximum(500)
        self.lr_slider.setValue(50); self.lr_slider.valueChanged.connect(self._on_lr_change)
        ctrl.addWidget(self.lr_slider)
        self.lr_label = QLabel("0.050"); self.lr_label.setFixedWidth(60); ctrl.addWidget(self.lr_label)

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

        self.back_btn = QPushButton("Back to ML Visualizer")
        self.back_btn.clicked.connect(self._on_back)
        ctrl.addWidget(self.back_btn)

        layout.addLayout(ctrl)

        # plotting area + info panel
        body = QHBoxLayout()

        # figure: left network plot, right loss curve & info
        self.figure = plt.figure(figsize=(10, 6))
        gs = self.figure.add_gridspec(2, 3)
        self.ax_net = self.figure.add_subplot(gs[:, 0:2])
        self.ax_loss = self.figure.add_subplot(gs[0, 2])
        self.ax_dummy = self.figure.add_subplot(gs[1, 2])  # reserved for extra info or legend

        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        body.addWidget(self.canvas, 3)

        right = QVBoxLayout()
        right.addWidget(QLabel("Node / Weight Info"))
        self.info = QTextEdit(); self.info.setReadOnly(True); self.info.setFixedWidth(320)
        right.addWidget(self.info)
        body.addLayout(right, 1)

        layout.addLayout(body)
        self.setLayout(layout)

        # connect click events on the network axes
        self.canvas.mpl_connect("button_press_event", self._on_click)

        # init mappings
        self._on_lr_change(self.lr_slider.value())

    # ---------------- data & model init ----------------
    def _init_demo_data(self):
        # two class blobs
        a = np.random.normal(loc=[-2.0, -1.0], scale=0.9, size=(80, 2))
        b = np.random.normal(loc=[2.0, 1.5], scale=0.9, size=(80, 2))
        pts = np.vstack([a, b])
        labels = np.array([0] * len(a) + [1] * len(b))
        self.data = [(float(x), float(y), int(lbl)) for (x, y), lbl in zip(pts, labels)]

    def _init_model(self):
        h = int(self.hidden_units)
        # small random init
        self.W1 = np.random.normal(scale=0.5, size=(h, self.input_dim))
        self.b1 = np.zeros(h)
        self.W2 = np.random.normal(scale=0.5, size=(1, h)).flatten()  # shape (h,)
        self.b2 = 0.0
        self.loss_history = []
        self._compute_node_positions()

    # ---------------- handlers ----------------
    def _on_hidden_change(self, v):
        self.hidden_units = int(v)
        self._init_model()
        self._draw_full()

    def _on_activation_change(self, t):
        self.activation_name = t
        self._draw_full()

    def _on_lr_change(self, v):
        # map 1..500 -> 1e-4..0.5 roughly (exponential)
        lr = 10 ** (-4 + (v / 500.0) * 2.7)  # ~1e-4 to ~0.5
        self.learning_rate = float(lr)
        self.lr_label.setText(f"{self.learning_rate:.3f}")

    def _on_start(self):
        # prepare SGD steps (one sample per step) for a number of epochs
        self.step_ptr = 0
        self.steps = []
        X, Y = self._dataset_arrays()
        n = X.shape[0]
        epochs = 25
        order = list(range(n))
        for e in range(epochs):
            random.shuffle(order)
            for i in order:
                def make_step(i=i):
                    def fn():
                        self._sgd_update(i)
                    return fn
                self.steps.append(make_step())
        self.info_append(f"Prepared {len(self.steps)} SGD steps (epochs={epochs}).")
        # compute initial forward for visualization
        self._forward_all_and_record_loss()
        self._draw_full()

    def _on_step(self):
        if not self.steps:
            self._on_start()
            return
        if self.step_ptr < len(self.steps):
            self.steps[self.step_ptr]()
            self.step_ptr += 1
            # after update, compute loss and update visuals
            self._forward_all_and_record_loss()
            self._draw_full()

    def _on_run(self):
        if not self.steps:
            self._on_start()
        interval = 60  # ms per step
        self.timer.start(interval)

    def _on_stop(self):
        if self.timer.isActive():
            self.timer.stop()

    def _on_back(self):
        if self.timer.isActive():
            self.timer.stop()
        self.close()
        self.backToHomeSignal.emit()

    def _timer_step(self):
        if self.step_ptr < len(self.steps):
            self.steps[self.step_ptr]()
            self.step_ptr += 1
            self._forward_all_and_record_loss()
            self._draw_full()
        else:
            self.timer.stop()
            self.info_append("Run finished.")

    # ---------------- dataset helpers ----------------
    def _dataset_arrays(self):
        if not self.data:
            return np.zeros((0, 2)), np.zeros((0,))
        arr = np.array(self.data)
        X = arr[:, :2].astype(float)
        Y = arr[:, 2].astype(float)
        return X, Y

    # ---------------- forward & sgd ----------------
    def _forward(self, x):
        """
        x: shape (2,)
        returns: dict with z1,a1,z2,a2 (scalars/vectors)
        """
        z1 = self.W1.dot(x) + self.b1     # (h,)
        if self.activation_name == "ReLU":
            a1 = relu(z1)
        else:
            a1 = sigmoid(z1)
        z2 = float(np.dot(self.W2, a1) + self.b2)
        a2 = sigmoid(z2)
        return {"z1": z1, "a1": a1, "z2": z2, "a2": a2}

    def _forward_all_and_record_loss(self):
        X, Y = self._dataset_arrays()
        if X.shape[0] == 0:
            return
        preds = []
        for x in X:
            out = self._forward(x)
            preds.append(out["a2"])
        preds = np.array(preds)
        # binary cross-entropy loss
        eps = 1e-9
        loss = -np.mean(Y * np.log(preds + eps) + (1 - Y) * np.log(1 - preds + eps))
        self.loss_history.append(loss)
        self.info_append(f"Step {self.step_ptr}: loss={loss:.4f}")

    def _sgd_update(self, idx):
        # perform SGD update on sample idx
        X, Y = self._dataset_arrays()
        x = X[idx]
        y = Y[idx]
        # forward
        z1 = self.W1.dot(x) + self.b1      # (h,)
        if self.activation_name == "ReLU":
            a1 = relu(z1)
            dz1_act = drelu(z1)
        else:
            a1 = sigmoid(z1)
            dz1_act = dsigmoid(z1)
        z2 = float(np.dot(self.W2, a1) + self.b2)
        a2 = sigmoid(z2)
        # compute gradients for BCE with sigmoid output
        # dL/da2 = -(y/a2) + ((1-y)/(1-a2))  but with cross-entropy + sigmoid, gradient simplifies:
        dloss_da2 = (a2 - y)  # derivative for BCE with sigmoid
        # gradients for W2 and b2
        dW2 = dloss_da2 * a1      # shape (h,)
        db2 = dloss_da2
        # backprop to hidden
        delta1 = (dloss_da2 * self.W2) * dz1_act   # shape (h,)
        dW1 = np.outer(delta1, x)                  # shape (h, input_dim)
        db1 = delta1
        # update params (SGD)
        lr = self.learning_rate
        self.W2 -= lr * dW2
        self.b2 -= lr * db2
        self.W1 -= lr * dW1
        self.b1 -= lr * db1

    # ---------------- visualization helpers ----------------
    def _compute_node_positions(self):
        # positions for input(2), hidden(h), output(1)
        left_x = 0.2; middle_x = 0.55; right_x = 0.9
        # input nodes (2) spaced vertically
        n_in = self.input_dim
        n_h = self.hidden_units
        in_ys = np.linspace(0.7, 0.3, n_in)
        hid_ys = np.linspace(0.9, 0.1, n_h)
        out_ys = [0.5]
        self.node_positions = {
            "input": [(left_x, float(y)) for y in in_ys],
            "hidden": [(middle_x, float(y)) for y in hid_ys],
            "output": [(right_x, out_ys[0])]
        }

    def _draw_full(self):
        self._compute_node_positions()
        self.ax_net.clear()
        # draw edges with weight thickness and color sign
        # get latest activations for color intensity
        X, Y = self._dataset_arrays()
        # if dataset non-empty, compute avg activations for coloring nodes (or default zeros)
        if X.shape[0] > 0:
            avg_a1 = np.zeros(self.hidden_units)
            avg_a2 = 0.0
            for x in X[: min(len(X), 40)]:  # sample subset for speed
                fwd = self._forward(x)
                avg_a1 += fwd["a1"]
                avg_a2 += fwd["a2"]
            avg_a1 /= min(len(X), 40)
            avg_a2 /= min(len(X), 40)
        else:
            avg_a1 = np.zeros(self.hidden_units)
            avg_a2 = 0.0

        # draw input to hidden edges
        for j, (hx, hy) in enumerate(self.node_positions["hidden"]):
            for i, (ix, iy) in enumerate(self.node_positions["input"]):
                w = float(self.W1[j, i])
                linewidth = 0.5 + min(6.0, abs(w) * 2.5)
                color = "#2ca02c" if w >= 0 else "#d62728"
                self.ax_net.plot([ix, hx], [iy, hy], linewidth=linewidth, color=color, alpha=0.9, zorder=1)

        # draw hidden to output edges
        ox, oy = self.node_positions["output"][0]
        for j, (hx, hy) in enumerate(self.node_positions["hidden"]):
            w = float(self.W2[j])
            linewidth = 0.5 + min(6.0, abs(w) * 2.5)
            color = "#2ca02c" if w >= 0 else "#d62728"
            self.ax_net.plot([hx, ox], [hy, oy], linewidth=linewidth, color=color, alpha=0.9, zorder=1)

        # draw nodes: input, hidden, output — node color intensity by activation magnitude
        # Input node activations depend on sample; we'll color them neutral
        for i, (ix, iy) in enumerate(self.node_positions["input"]):
            self._draw_node(ix, iy, label=f"x{i}", facecolor="#aec7e8", edgecolor="k")

        # hidden nodes: use avg_a1 for intensity
        for j, (hx, hy) in enumerate(self.node_positions["hidden"]):
            act = float(avg_a1[j]) if j < len(avg_a1) else 0.0
            color = self._activation_color(act)
            self._draw_node(hx, hy, radius=self.node_radius * 1.1, label=f"h{j}", facecolor=color, edgecolor="k")

        # output node
        out_color = self._activation_color(float(avg_a2))
        self._draw_node(ox, oy, radius=self.node_radius * 1.2, label="y", facecolor=out_color, edgecolor="k")

        # draw dataset points on background (colored by label)
        if X.shape[0] > 0:
            pts = np.array(self.data)
            xs = pts[:, 0]; ys = pts[:, 1]; labs = pts[:, 2].astype(int)
            for cls in [0, 1]:
                mask = labs == cls
                if mask.any():
                    col = "#1f77b4" if cls == 0 else "#ff7f0e"
                    self.ax_net.scatter(xs[mask], ys[mask], c=col, s=18, edgecolors="k", zorder=0, alpha=0.8)

        self.ax_net.set_title("Network visualization: node color = activation, edge thickness = |weight| (green=+ , red=-)")
        self.ax_net.set_xlim(0, 1)
        self.ax_net.set_ylim(0, 1)
        self.ax_net.axis("off")

        # draw loss curve
        self.ax_loss.clear()
        if self.loss_history:
            self.ax_loss.plot(self.loss_history, color="#2ca02c")
            self.ax_loss.set_title("Loss (BCE) over steps")
            self.ax_loss.set_xlabel("Step")
            self.ax_loss.set_ylabel("Loss")
        else:
            self.ax_loss.text(0.5, 0.5, "No loss history", ha="center", va="center")
            self.ax_loss.set_title("Loss (BCE)")

        # dummy ax show weights summary
        self.ax_dummy.clear()
        self.ax_dummy.axis("off")
        info_lines = [
            f"Hidden units: {self.hidden_units}",
            f"Activation: {self.activation_name}",
            f"LR: {self.learning_rate:.4f}",
            f"Step ptr: {self.step_ptr}",
            f"W1 shape: {self.W1.shape}",
            f"W2 shape: {self.W2.shape}",
        ]
        self.ax_dummy.text(0.02, 0.95, "\n".join(info_lines), fontsize=9, va="top")
        self.figure.tight_layout()
        self.canvas.draw()

    def _draw_node(self, x, y, radius=None, label="", facecolor="#ffffff", edgecolor="k"):
        if radius is None:
            radius = self.node_radius
        circle = plt.Circle((x, y), radius, facecolor=facecolor, edgecolor=edgecolor, zorder=5)
        self.ax_net.add_patch(circle)
        self.ax_net.text(x, y, label, ha="center", va="center", fontsize=9, zorder=6)

    def _activation_color(self, a):
        # map activation (0..1 approx) to color scale from light gray to bright green
        a_clip = float(np.clip(a, 0.0, 1.0))
        # color as interpolation between white and green
        r = 1.0 - 0.6 * a_clip
        g = 1.0
        b = 1.0 - 0.6 * a_clip
        return (r, g, b)

    # ---------------- click handling ----------------
    def _on_click(self, event):
        # if click inside network axes, determine node nearest and show its info
        if event.inaxes != self.ax_net:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        # detect if click near a node
        clicked = self._find_clicked_node(x, y)
        if clicked is not None:
            layer, idx = clicked
            self._show_node_info(layer, idx)
            return
        # otherwise, treat as dataset add/remove: left-click add point with label toggle by shift
        if event.button == 1:
            label = 1 if event.key == "shift" else 0
            self.data.append((float(x), float(y), int(label)))
            self.info_append(f"Added point ({x:.2f},{y:.2f}) label={label}")
            self._draw_full()
        elif event.button == 3:
            idx = self._nearest_point_index(x, y, tol=0.05)
            if idx is not None:
                px, py, pl = self.data.pop(idx)
                self.info_append(f"Removed point ({px:.2f},{py:.2f}) label={pl}")
                self._draw_full()

    def _find_clicked_node(self, x, y):
        # check input, hidden, output nodes for proximity
        for i, (nx, ny) in enumerate(self.node_positions["input"]):
            if math.hypot(nx - x, ny - y) <= self.node_radius + 0.03:
                return ("input", i)
        for j, (nx, ny) in enumerate(self.node_positions["hidden"]):
            if math.hypot(nx - x, ny - y) <= self.node_radius + 0.03:
                return ("hidden", j)
        ox, oy = self.node_positions["output"][0]
        if math.hypot(ox - x, oy - y) <= self.node_radius + 0.04:
            return ("output", 0)
        return None

    def _show_node_info(self, layer, idx):
        # produce text showing weights entering this node and bias and current activation (if computable)
        text_lines = []
        if layer == "input":
            text_lines.append(f"Input node x{idx}")
            text_lines.append("No incoming weights (input features).")
        elif layer == "hidden":
            text_lines.append(f"Hidden node h{idx}")
            # incoming weights from inputs
            w_in = self.W1[idx, :]
            b = float(self.b1[idx])
            text_lines.append(f"Bias: {b:.4f}")
            text_lines.append("Incoming weights:")
            for i, w in enumerate(w_in):
                text_lines.append(f"  w_in[{i}] = {w:.4f}")
            # compute current activation on dataset average
            X, Y = self._dataset_arrays()
            if X.shape[0] > 0:
                vals = []
                for x in X[: min(40, X.shape[0])]:
                    z = float(np.dot(self.W1[idx, :], x) + b)
                    vals.append(z)
                avg_z = float(np.mean(vals))
                if self.activation_name == "ReLU":
                    a = float(np.mean(np.maximum(0, vals)))
                else:
                    a = float(np.mean(sigmoid(np.array(vals))))
                text_lines.append(f"Avg pre-activation z (sampled): {avg_z:.4f}")
                text_lines.append(f"Avg activation a (sampled): {a:.4f}")
        else:  # output
            text_lines.append("Output node y")
            text_lines.append(f"Bias: {self.b2:.4f}")
            text_lines.append("Incoming weights from hidden:")
            for j, w in enumerate(self.W2):
                text_lines.append(f"  w_h[{j}] = {w:.4f}")
            # show current avg output
            X, Y = self._dataset_arrays()
            if X.shape[0] > 0:
                outs = [self._forward(x)["a2"] for x in X[: min(40, X.shape[0])]]
                text_lines.append(f"Avg output (sampled): {float(np.mean(outs)):.4f}")
        self.info.setPlainText("\n".join(text_lines))

    def _nearest_point_index(self, x, y, tol=0.05):
        if not self.data:
            return None
        pts = np.array([(p[0], p[1]) for p in self.data])
        # map data coordinates to network axis coordinates? Here we encode dataset in same 0..1 axis as net
        # We used data coordinates directly when plotting points, so find nearest in data space
        d = np.hypot(pts[:, 0] - x, pts[:, 1] - y)
        m = d.min()
        return int(d.argmin()) if m <= tol else None

    # ---------------- utility ----------------
    def info_append(self, txt):
        prev = self.info.toPlainText()
        new = prev + ("\n" if prev else "") + txt
        self.info.setPlainText(new)
        self.info.verticalScrollBar().setValue(self.info.verticalScrollBar().maximum())

    # ---------------- standalone test ----------------
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = ANNVisualizer()
    w.show()
    sys.exit(app.exec_())
