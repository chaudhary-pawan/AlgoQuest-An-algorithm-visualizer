# ml_decision_tree_visualizer.py
# Decision Tree Visualizer (axis-aligned splits only)
# Lightweight educational tool: greedy splits, BFS order, shows split lines and node info.
#
# Usage:
# - Left-click on the left plot to add a point. Use the label dropdown to choose class (0 or 1).
# - Right-click near a point to delete it.
# - Choose impurity metric (Gini / Entropy).
# - Start -> prepares split steps; Step -> apply next split; Run -> animate splits.
# - Back button emits backToHomeSignal.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSizePolicy, QTextEdit, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
import math
import random

random.seed(1)
np.random.seed(1)


def gini_impurity(labels):
    if len(labels) == 0:
        return 0.0
    p = np.bincount(labels, minlength=2).astype(float)
    p = p / p.sum()
    return 1.0 - np.sum(p * p)


def entropy_impurity(labels):
    if len(labels) == 0:
        return 0.0
    p = np.bincount(labels, minlength=2).astype(float)
    p = p / p.sum()
    eps = 1e-12
    p = np.clip(p, eps, 1.0)
    return -np.sum(p * np.log2(p))


class DecisionTreeVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Decision Tree Visualizer")
        self.setGeometry(120, 80, 1100, 700)

        # data: list of (x, y, label)
        self.data = []
        self._init_demo_data()

        # tree structure (nodes); will be built progressively
        # node = dict: { 'id', 'indices', 'depth', 'bbox':(xmin,xmax,ymin,ymax), 'split':(feat,thresh), 'left', 'right', 'impurity' }
        self.nodes = {}
        self.node_id_counter = 0
        self.root_id = None

        # steps: list of node_ids to split next (BFS queue produced by prepare)
        self.steps = []
        self.step_ptr = 0

        # UI & plotting
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._timer_step)
        self.speed = 6

        self.metric = "Gini"
        self.max_depth = 6
        self.min_samples_split = 2

        self._build_ui()
        self._draw()

    # ------------- UI -------------
    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Graphical Decision Tree Visualizer — Topological view of splits")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        ctrl.addWidget(QLabel("Impurity:"))
        self.metric_box = QComboBox()
        self.metric_box.addItems(["Gini", "Entropy"])
        self.metric_box.currentTextChanged.connect(self._on_metric_change)
        ctrl.addWidget(self.metric_box)

        ctrl.addWidget(QLabel("Max Depth:"))
        self.max_depth_spin = QSpinBox()
        self.max_depth_spin.setMinimum(1); self.max_depth_spin.setMaximum(8); self.max_depth_spin.setValue(4)
        self.max_depth_spin.valueChanged.connect(self._on_max_depth_change)
        ctrl.addWidget(self.max_depth_spin)

        ctrl.addWidget(QLabel("Min Samples Split:"))
        self.min_split_spin = QSpinBox()
        self.min_split_spin.setMinimum(2); self.min_split_spin.setMaximum(50); self.min_split_spin.setValue(4)
        self.min_split_spin.valueChanged.connect(self._on_min_split_change)
        ctrl.addWidget(self.min_split_spin)

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

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._on_reset)
        ctrl.addWidget(self.reset_btn)

        self.back_btn = QPushButton("Back to ML Visualizer")
        self.back_btn.clicked.connect(self._on_back)
        ctrl.addWidget(self.back_btn)

        layout.addLayout(ctrl)

        # canvas + info panel
        body = QHBoxLayout()
        self.figure, self.ax = plt.subplots(figsize=(9, 6))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.mpl_connect("button_press_event", self._on_mouse_click)
        body.addWidget(self.canvas, 3)

        right = QVBoxLayout()
        right.addWidget(QLabel("Node info / logs"))
        self.info = QTextEdit()
        self.info.setReadOnly(True)
        right.addWidget(self.info)
        body.addLayout(right, 1)

        layout.addLayout(body)
        self.setLayout(layout)

    # ------------- demo data -------------
    def _init_demo_data(self):
        # two Gaussian blobs with overlap
        c1 = np.random.normal(loc=[-2.0, 0.0], scale=1.1, size=(80, 2))
        c2 = np.random.normal(loc=[3.0, 2.0], scale=1.2, size=(80, 2))
        labels = np.array([0] * len(c1) + [1] * len(c2))
        pts = np.vstack([c1, c2])
        self.data = [(float(x), float(y), int(lbl)) for (x, y), lbl in zip(pts, labels)]

    # ------------- helpers -------------
    def _on_metric_change(self, v):
        self.metric = v

    def _on_max_depth_change(self, v):
        self.max_depth = int(v)

    def _on_min_split_change(self, v):
        self.min_samples_split = int(v)

    def _on_back(self):
        self._stop_timer()
        self.close()
        self.backToHomeSignal.emit()

    # ------------- mouse interaction -------------
    def _on_mouse_click(self, event):
        # left click: add point with class selected by metric_box (toggle label via Ctrl)
        if event.inaxes != self.ax:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        if event.button == 1:
            # left click add as class 0 or 1 depending on modifier: default class 0 when no shift, class 1 if shift pressed
            label = 1 if event.key == "shift" else 0
            self.data.append((float(x), float(y), int(label)))
            self._draw()
            self._log(f"Added point ({x:.2f},{y:.2f}) label={label}.")
        elif event.button == 3:
            # right click delete nearest if close
            idx = self._nearest_point_index(x, y, tol=0.4)
            if idx is not None:
                px, py, pl = self.data.pop(idx)
                self._draw()
                self._log(f"Removed point ({px:.2f},{py:.2f}) label={pl}.")

    def _nearest_point_index(self, x, y, tol=0.4):
        if not self.data:
            return None
        pts = np.array([(p[0], p[1]) for p in self.data])
        d = np.hypot(pts[:, 0] - x, pts[:, 1] - y)
        m = d.min()
        return int(d.argmin()) if m <= tol else None

    # ------------- tree utilities -------------
    def _clear_tree(self):
        self.nodes = {}
        self.node_id_counter = 0
        self.root_id = None
        self.steps = []
        self.step_ptr = 0

    def _new_node(self, indices, depth, bbox):
        nid = self.node_id_counter
        self.node_id_counter += 1
        node = {
            "id": nid,
            "indices": np.array(indices, dtype=int),
            "depth": depth,
            "bbox": bbox,
            "split": None,
            "left": None,
            "right": None,
            "impurity": None
        }
        self.nodes[nid] = node
        return nid

    def _compute_best_split(self, indices):
        # returns (best_feat, best_thresh, best_gain, best_left_idx, best_right_idx, impurity_node)
        if len(indices) <= self.min_samples_split:
            return None

        X = np.array([(self.data[i][0], self.data[i][1]) for i in indices])
        Y = np.array([self.data[i][2] for i in indices], dtype=int)
        if self.metric == "Gini":
            impurity_fn = gini_impurity
        else:
            impurity_fn = entropy_impurity

        parent_impurity = impurity_fn(Y)
        best = None
        n = len(indices)

        # try splits on feature 0 and 1
        for feat in [0, 1]:
            vals = X[:, feat]
            # candidate thresholds = midpoints between sorted unique values
            uniq = np.unique(np.sort(vals))
            if uniq.size <= 1:
                continue
            thresh_candidates = 0.5 * (uniq[:-1] + uniq[1:])
            for t in thresh_candidates:
                left_mask = vals <= t
                right_mask = vals > t
                left_idx = np.array(indices)[left_mask].astype(int)
                right_idx = np.array(indices)[right_mask].astype(int)
                if left_idx.size == 0 or right_idx.size == 0:
                    continue
                left_imp = impurity_fn(np.array([self.data[i][2] for i in left_idx]))
                right_imp = impurity_fn(np.array([self.data[i][2] for i in right_idx]))
                w = float(left_idx.size) / n
                weighted_impurity = w * left_imp + (1.0 - w) * right_imp
                gain = parent_impurity - weighted_impurity
                # choose maximum gain (or minimal impurity)
                if best is None or gain > best[2]:
                    best = (feat, float(t), float(gain), left_idx, right_idx, float(parent_impurity))
        return best

    # ------------- prepare / execute steps -------------
    def _on_start(self):
        # build initial root node and prepare BFS order splits (but do not apply them until Step)
        self._stop_timer()
        self._clear_tree()
        if not self.data:
            self._log("No data available.")
            return
        all_idx = list(range(len(self.data)))
        # overall bbox
        xs = [p[0] for p in self.data]; ys = [p[1] for p in self.data]
        bbox = (min(xs) - 0.5, max(xs) + 0.5, min(ys) - 0.5, max(ys) + 0.5)
        root = self._new_node(all_idx, depth=0, bbox=bbox)
        self.root_id = root

        # BFS prepare: we compute best splits on-demand and record a queue of node ids to split
        queue = [root]
        steps = []
        while queue:
            nid = queue.pop(0)
            node = self.nodes[nid]
            if node["depth"] >= self.max_depth:
                continue
            if node["indices"].size < self.min_samples_split:
                continue
            best = self._compute_best_split(node["indices"])
            if best is None:
                continue
            feat, thresh, gain, left_idx, right_idx, impurity_node = best
            # create child nodes (but do not commit splits yet) and append a step that will commit the split
            # compute child bbox from parent's bbox depending on feat and thresh
            xmin, xmax, ymin, ymax = node["bbox"]
            if feat == 0:
                left_bbox = (xmin, thresh, ymin, ymax)
                right_bbox = (thresh, xmax, ymin, ymax)
            else:
                left_bbox = (xmin, xmax, ymin, thresh)
                right_bbox = (xmin, xmax, thresh, ymax)
            left_nid = self.node_id_counter
            right_nid = self.node_id_counter + 1

            # prepare step data
            step_data = {
                "nid": nid,
                "feat": feat,
                "thresh": thresh,
                "gain": gain,
                "left_idx": left_idx,
                "right_idx": right_idx,
                "left_bbox": left_bbox,
                "right_bbox": right_bbox,
                "impurity": impurity_node,
                "depth": node["depth"]
            }
            steps.append(step_data)
            # still enqueue child placeholders for BFS further splitting (use indices)
            # but we don't actually create nodes yet (they will be created when step applied)
            # To estimate further splits, simply add placeholders indexes with depth+1
            queue.append(("placeholder", left_idx, node["depth"] + 1))
            queue.append(("placeholder", right_idx, node["depth"] + 1))
        # store steps
        self.steps = steps
        self.step_ptr = 0
        self._log(f"Prepared {len(self.steps)} split steps (greedy BFS order).")
        self._draw()

    def _apply_next_step(self):
        if self.step_ptr >= len(self.steps):
            self._log("No more steps.")
            return
        s = self.steps[self.step_ptr]
        nid = s["nid"]
        if nid not in self.nodes:
            self._log("Parent node missing; cannot apply step.")
            self.step_ptr += 1
            return
        node = self.nodes[nid]
        # create left & right nodes and commit split
        left_nid = self._new_node(s["left_idx"], node["depth"] + 1, s["left_bbox"])
        right_nid = self._new_node(s["right_idx"], node["depth"] + 1, s["right_bbox"])
        node["split"] = (s["feat"], s["thresh"])
        node["left"] = left_nid
        node["right"] = right_nid
        node["impurity"] = s["impurity"]
        self._log(f"Split node {nid} at depth {node['depth']} on feature {s['feat']} <= {s['thresh']:.3f} (gain={s['gain']:.4f})")
        self.step_ptr += 1
        self._draw()

    def _on_step(self):
        self._stop_timer()
        self._apply_next_step()

    def _on_run(self):
        if not self.steps:
            self._on_start()
        if not self.steps:
            return
        interval = int(1000 / max(1, self.speed))
        self.timer.start(interval)

    def _on_stop(self):
        self._stop_timer()

    def _stop_timer(self):
        if self.timer.isActive():
            self.timer.stop()

    def _timer_step(self):
        if self.step_ptr < len(self.steps):
            self._apply_next_step()
        else:
            self._stop_timer()

    def _on_reset(self):
        self._stop_timer()
        self._clear_tree()
        self._draw()
        self._log("Tree reset.")

    # ------------- drawing --------------
    def _draw(self):
        self.ax.clear()
        if not self.data:
            self.ax.text(0.5, 0.5, "No data", ha="center")
            self.canvas.draw()
            return
        pts = np.array([(x, y) for x, y, _ in self.data])
        labels = np.array([l for _, _, l in self.data])
        # color map
        colors = np.array(["#1f77b4", "#ff7f0e"])
        for cls in [0, 1]:
            mask = labels == cls
            if mask.any():
                self.ax.scatter(pts[mask, 0], pts[mask, 1], color=colors[cls], edgecolor="k", s=36, zorder=3, label=f"class {cls}")
        # draw splits recursively
        self._draw_splits(self.root_id)
        self.ax.set_title("Data space with axis-aligned splits")
        self.ax.legend(loc="upper left")
        self.ax.grid(True)
        # show node info on right pane
        self._render_info_text()
        self.figure.tight_layout()
        self.canvas.draw()

    def _draw_splits(self, node_id):
        # draw split for node if present (line across node bbox)
        if node_id is None or node_id not in self.nodes:
            return
        node = self.nodes[node_id]
        # draw bounding box lightly
        xmin, xmax, ymin, ymax = node["bbox"]
        self.ax.add_patch(plt.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, fill=False, edgecolor="#cccccc", linewidth=0.5, zorder=1))
        if node["split"] is not None:
            feat, thresh = node["split"]
            # line across node bbox
            if feat == 0:
                # vertical line at thresh across ymin..ymax
                self.ax.plot([thresh, thresh], [ymin, ymax], color="black", linestyle="--", linewidth=1.6, zorder=4)
            else:
                # horizontal line
                self.ax.plot([xmin, xmax], [thresh, thresh], color="black", linestyle="--", linewidth=1.6, zorder=4)
            # draw children recursively
            self._draw_splits(node["left"])
            self._draw_splits(node["right"])

    # ------------- info rendering -------------
    def _render_info_text(self):
        lines = []
        lines.append(f"Data points: {len(self.data)}")
        lines.append(f"Metric: {self.metric} | MaxDepth: {self.max_depth} | MinSplit: {self.min_samples_split}")
        lines.append(f"Prepared steps: {len(self.steps)} | Applied: {self.step_ptr}")
        lines.append("")
        lines.append("Nodes:")
        for nid in sorted(self.nodes.keys()):
            n = self.nodes[nid]
            s = f"ID {nid}: depth={n['depth']} n={len(n['indices'])}"
            if n["split"] is not None:
                s += f"  split=(f{n['split'][0]} <= {n['split'][1]:.3f})"
            lines.append(s)
        self.info.setPlainText("\n".join(lines))

    def _log(self, msg):
        prev = self.info.toPlainText()
        new = prev + ("\n" if prev else "") + msg
        self.info.setPlainText(new)
        # scroll to end
        self.info.verticalScrollBar().setValue(self.info.verticalScrollBar().maximum())

    # ------------- standalone test -------------
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = DecisionTreeVisualizer()
    w.show()
    sys.exit(app.exec_())
