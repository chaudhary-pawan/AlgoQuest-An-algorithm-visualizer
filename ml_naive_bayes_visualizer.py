# ml_naive_bayes_visualizer.py
# Simple interactive Gaussian Naive Bayes visualizer (2 continuous features)
#
# - Left-click on plot to add point with selected class (0/1)
# - Right-click near a point to remove it
# - Click "Train" to compute class priors, means, stds
# - Click on the plot (middle/right) or enter coordinates and press 'Predict' to see posterior probabilities
# - Shows per-class histograms with Gaussian PDFs overlayed
#
# Exposes class: NaiveBayesVisualizer
# Emits: backToHomeSignal when back button pressed

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
import math
import random

random.seed(1)
np.random.seed(1)


def gaussian_pdf(x, mu, sigma):
    eps = 1e-9
    sigma = max(sigma, eps)
    coef = 1.0 / (math.sqrt(2 * math.pi) * sigma)
    exp = math.exp(-0.5 * ((x - mu) / sigma) ** 2)
    return coef * exp


class NaiveBayesVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Naive Bayes Visualizer")
        self.setGeometry(140, 80, 1100, 700)

        # data: list of (x, y, label)
        self.data = []
        self._init_demo_data()

        # model params (for each class 0/1): prior, mean (2-d), std (2-d)
        self.model = {
            0: {"prior": 0.5, "mu": np.array([0.0, 0.0]), "sigma": np.array([1.0, 1.0])},
            1: {"prior": 0.5, "mu": np.array([1.0, 1.0]), "sigma": np.array([1.0, 1.0])}
        }
        self.trained = False

        # build UI
        self._build_ui()
        self._draw_all()

    # ---------------- UI ----------------
    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Naive Bayes Visualizer (Gaussian, 2 features)")
        title.setFont(QFont("Arial", 15, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        self.class_select = QComboBox()
        self.class_select.addItems(["Class 0", "Class 1"])
        ctrl.addWidget(QLabel("Add point as:"))
        ctrl.addWidget(self.class_select)

        self.train_btn = QPushButton("Train")
        self.train_btn.clicked.connect(self._train)
        ctrl.addWidget(self.train_btn)

        self.predict_btn = QPushButton("Predict Point")
        self.predict_btn.clicked.connect(self._predict_from_inputs)
        ctrl.addWidget(self.predict_btn)

        ctrl.addWidget(QLabel("x:"))
        self.x_input = QLineEdit(); self.x_input.setFixedWidth(80)
        ctrl.addWidget(self.x_input)
        ctrl.addWidget(QLabel("y:"))
        self.y_input = QLineEdit(); self.y_input.setFixedWidth(80)
        ctrl.addWidget(self.y_input)

        self.back_btn = QPushButton("Back to ML Visualizer")
        self.back_btn.clicked.connect(self._on_back)
        ctrl.addWidget(self.back_btn)

        layout.addLayout(ctrl)

        # plotting area: left main scatter, right two histograms stacked
        self.figure = plt.figure(figsize=(10, 5))
        # grid: left big axes, right top hist x, right bottom hist y
        gs = self.figure.add_gridspec(2, 3)
        self.ax_scatter = self.figure.add_subplot(gs[:, 0:2])
        self.ax_hist_x = self.figure.add_subplot(gs[0, 2])
        self.ax_hist_y = self.figure.add_subplot(gs[1, 2])

        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas)

        # info label for priors and prediction
        self.info_label = QLabel("")
        self.info_label.setFont(QFont("Arial", 11))
        layout.addWidget(self.info_label)

        self.setLayout(layout)

        # mpl events
        self.canvas.mpl_connect("button_press_event", self._on_click)

    # ---------------- demo data ----------------
    def _init_demo_data(self):
        # class 0 around (-2,0), class 1 around (3,2)
        c0 = np.random.normal(loc=[-2.0, 0.0], scale=0.9, size=(70, 2))
        c1 = np.random.normal(loc=[3.0, 2.0], scale=1.1, size=(70, 2))
        pts = np.vstack([c0, c1])
        labels = np.array([0] * len(c0) + [1] * len(c1))
        self.data = [(float(x), float(y), int(lbl)) for (x, y), lbl in zip(pts, labels)]

    # ---------------- drawing ----------------
    def _draw_all(self, highlight_point=None, posterior=None):
        self.ax_scatter.clear()
        self.ax_hist_x.clear()
        self.ax_hist_y.clear()

        if not self.data:
            self.ax_scatter.text(0.5, 0.5, "No data", ha="center")
            self.canvas.draw()
            return

        pts = np.array([(x, y) for x, y, _ in self.data])
        labels = np.array([l for _, _, l in self.data])

        colors = np.array(["#1f77b4", "#ff7f0e"])
        for cls in [0, 1]:
            mask = labels == cls
            if mask.any():
                self.ax_scatter.scatter(pts[mask, 0], pts[mask, 1], color=colors[cls], edgecolor="k", s=36, label=f"class {cls}")

        self.ax_scatter.set_title("Data scatter (click to add/remove points). Left-click to add with selected class; right-click to remove nearest.")
        self.ax_scatter.grid(True)
        self.ax_scatter.legend(loc="upper left")

        # plot model means if trained
        if self.trained:
            for cls in [0, 1]:
                mu = self.model[cls]["mu"]
                sigma = self.model[cls]["sigma"]
                # mark mean
                self.ax_scatter.scatter([mu[0]], [mu[1]], marker="X", s=120, color=colors[cls], edgecolor="k", zorder=5)
                self.ax_scatter.text(mu[0], mu[1], f" mu{cls}", fontsize=9, verticalalignment="bottom")

            # draw class-conditional ellipse approx using stds
            for cls in [0, 1]:
                mu = self.model[cls]["mu"]
                sigma = self.model[cls]["sigma"]
                # simple rectangle representing +/- 1 std
                rect_x = [mu[0] - sigma[0], mu[0] + sigma[0], mu[0] + sigma[0], mu[0] - sigma[0], mu[0] - sigma[0]]
                rect_y = [mu[1] - sigma[1], mu[1] - sigma[1], mu[1] + sigma[1], mu[1] + sigma[1], mu[1] - sigma[1]]
                self.ax_scatter.plot(rect_x, rect_y, color=colors[cls], linestyle=":", linewidth=1.4, alpha=0.9)

        # histograms for each feature with gaussian pdf overlay
        all_x = pts[:, 0]
        all_y = pts[:, 1]
        # histogram bins
        bins_x = 20
        bins_y = 20

        # plot per class hist and pdfs on ax_hist_x
        for cls in [0, 1]:
            mask = labels == cls
            if mask.any():
                data_x = pts[mask, 0]
                self.ax_hist_x.hist(data_x, bins=bins_x, alpha=0.4, color=colors[cls], density=True, label=f"class {cls}")

        if self.trained:
            # overlay gaussian pdf on x
            xs = np.linspace(all_x.min() - 1, all_x.max() + 1, 200)
            for cls in [0, 1]:
                mu = self.model[cls]["mu"][0]
                sigma = self.model[cls]["sigma"][0]
                pdf_vals = [gaussian_pdf(xx, mu, sigma) for xx in xs]
                self.ax_hist_x.plot(xs, pdf_vals, color=colors[cls])

        self.ax_hist_x.set_title("Feature x distribution")

        # y histogram
        for cls in [0, 1]:
            mask = labels == cls
            if mask.any():
                data_y = pts[mask, 1]
                self.ax_hist_y.hist(data_y, bins=bins_y, alpha=0.4, color=colors[cls], density=True, label=f"class {cls}")

        if self.trained:
            ys = np.linspace(all_y.min() - 1, all_y.max() + 1, 200)
            for cls in [0, 1]:
                mu = self.model[cls]["mu"][1]
                sigma = self.model[cls]["sigma"][1]
                pdf_vals = [gaussian_pdf(yy, mu, sigma) for yy in ys]
                self.ax_hist_y.plot(ys, pdf_vals, color=colors[cls])

        self.ax_hist_y.set_title("Feature y distribution")

        # update info label
        info_lines = []
        pri0 = self.model[0]["prior"]
        pri1 = self.model[1]["prior"]
        info_lines.append(f"P(class0)={pri0:.3f}  P(class1)={pri1:.3f}")
        if self.trained:
            for cls in [0, 1]:
                mu = self.model[cls]["mu"]
                sigma = self.model[cls]["sigma"]
                info_lines.append(f"class {cls}: mu=({mu[0]:.2f},{mu[1]:.2f})  sigma=({sigma[0]:.2f},{sigma[1]:.2f})")
        self.info_label_set("\n".join(info_lines))

        # if highlight point and posterior provided, show annotation
        if highlight_point is not None:
            hx, hy = highlight_point
            self.ax_scatter.scatter([hx], [hy], s=140, facecolors='none', edgecolors='k', linewidths=2, zorder=6)
            if posterior is not None:
                text = f"P(class0)={posterior[0]:.3f}\nP(class1)={posterior[1]:.3f}\nPred: {np.argmax(posterior)}"
                self.ax_scatter.text(hx, hy, text, fontsize=10, bbox=dict(facecolor='white', alpha=0.7), zorder=7)

        self.figure.tight_layout()
        self.canvas.draw()

    def info_label_set(self, txt):
        # small right-side multiline info label under canvas
        self.info_label.setText(txt)

    # ---------------- events ----------------
    def _on_click(self, event):
        # Add or remove points via click on scatter axes
        if event.inaxes != self.ax_scatter:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        if event.button == 1:  # left -> add with selected class
            cls = 0 if self.class_select.currentIndex() == 0 else 1
            self.data.append((float(x), float(y), cls))
            # after adding, update visuals (do not auto-train unless user clicks Train)
            self._draw_all()
        elif event.button == 3:  # right -> remove nearest if close
            idx = self._nearest_point_index(x, y, tol=0.4)
            if idx is not None:
                self.data.pop(idx)
                self._draw_all()

    def _nearest_point_index(self, x, y, tol=0.4):
        if not self.data:
            return None
        pts = np.array([(p[0], p[1]) for p in self.data])
        d = np.hypot(pts[:, 0] - x, pts[:, 1] - y)
        m = d.min()
        return int(d.argmin()) if m <= tol else None

    # ---------------- training / prediction ----------------
    def _train(self):
        if not self.data:
            QMessageBox.warning(self, "No data", "Add some data before training.")
            return
        arr = np.array(self.data)
        X = arr[:, :2].astype(float)
        Y = arr[:, 2].astype(int)
        classes = np.unique(Y)
        # compute priors and Gaussian stats
        for cls in [0, 1]:
            mask = Y == cls
            if mask.sum() == 0:
                # no points of that class, set defaults
                self.model[cls]["prior"] = 1e-6
                self.model[cls]["mu"] = np.array([0.0, 0.0])
                self.model[cls]["sigma"] = np.array([1.0, 1.0])
            else:
                self.model[cls]["prior"] = float(mask.sum()) / float(len(Y))
                xm = X[mask].mean(axis=0)
                xs = X[mask].std(axis=0, ddof=0)
                # avoid zero sigma
                xs = np.where(xs < 1e-6, 1.0, xs)
                self.model[cls]["mu"] = xm
                self.model[cls]["sigma"] = xs
        self.trained = True
        self._draw_all()
        QMessageBox.information(self, "Trained", "Gaussian Naive Bayes trained on current data.")

    def _predict_from_inputs(self):
        # take x,y from textboxes; if blank show warning
        tx = self.x_input.text().strip()
        ty = self.y_input.text().strip()
        if tx == "" or ty == "":
            QMessageBox.warning(self, "Input required", "Enter x and y coordinates or click on the plot.")
            return
        try:
            x = float(tx); y = float(ty)
        except ValueError:
            QMessageBox.warning(self, "Invalid", "Coordinates must be numeric.")
            return
        posterior = self._posterior(np.array([x, y]))
        self._draw_all(highlight_point=(x, y), posterior=posterior)

    def _posterior(self, xy):
        # returns normalized posterior P(class=k | xy) for k=0,1
        if not self.trained:
            # fallback simple equal priors and estimate objects
            self._train()
        post = []
        for cls in [0, 1]:
            prior = max(self.model[cls]["prior"], 1e-9)
            mu = self.model[cls]["mu"]
            sigma = self.model[cls]["sigma"]
            # assume independence between features
            p_x = gaussian_pdf(xy[0], mu[0], sigma[0])
            p_y = gaussian_pdf(xy[1], mu[1], sigma[1])
            likelihood = p_x * p_y
            post.append(prior * likelihood)
        s = sum(post)
        if s <= 0:
            # avoid zero normalization
            post = [0.5, 0.5]
        else:
            post = [p / s for p in post]
        return post

    def _on_back(self):
        self.close()
        self.backToHomeSignal.emit()


# ---------------- standalone test ----------------
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = NaiveBayesVisualizer()
    w.show()
    sys.exit(app.exec_())
