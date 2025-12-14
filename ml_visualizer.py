# ml_visualizer.py
# Machine Learning Visualizer Hub — links to 5 ML visualizers
# Buttons: Regression, K-Means, Decision Tree, Naive Bayes, ANN
# Each visualizer module is optional; hub handles missing modules gracefully.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# Try imports for each visualizer module. If file not present or import fails,
# the corresponding variable will be None and hub will show a warning when clicked.
try:
    from ml_regression_visualizer import RegressionVisualizer
except Exception:
    RegressionVisualizer = None

try:
    from ml_kmeans_visualizer import KMeansVisualizer
except Exception:
    KMeansVisualizer = None

try:
    from ml_decision_tree_visualizer import DecisionTreeVisualizer
except Exception:
    DecisionTreeVisualizer = None

try:
    from ml_naive_bayes_visualizer import NaiveBayesVisualizer
except Exception:
    NaiveBayesVisualizer = None

try:
    from ml_ann_visualizer import ANNVisualizer
except Exception:
    ANNVisualizer = None


class MLVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Machine Learning Visualizer Hub")
        self.setGeometry(220, 120, 1000, 540)
        self.child_window = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(18)
        layout.setContentsMargins(28, 18, 28, 18)

        title = QLabel("Machine Learning Visualizers")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Open a visualizer page (files may be added later).")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Spacer to push the buttons a bit lower (gives breathing room)
        layout.addSpacerItem(QSpacerItem(20, 18, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Two-column layout for buttons: left column and right column.
        # Buttons are styled for dark theme (light text on dark button).
        grid = QHBoxLayout()
        grid.setSpacing(24)

        col1 = QVBoxLayout()
        col1.setSpacing(14)
        col2 = QVBoxLayout()
        col2.setSpacing(14)

        # Create buttons
        btn_reg = QPushButton("1. Regression (Linear / Polynomial)")
        btn_reg.clicked.connect(self.open_regression)
        btn_reg.setFixedHeight(52)

        btn_km = QPushButton("2. K-Means Clustering")
        btn_km.clicked.connect(self.open_kmeans)
        btn_km.setFixedHeight(52)

        btn_dt = QPushButton("3. Decision Tree")
        btn_dt.clicked.connect(self.open_decision_tree)
        btn_dt.setFixedHeight(52)

        btn_nb = QPushButton("4. Naive Bayes")
        btn_nb.clicked.connect(self.open_naive_bayes)
        btn_nb.setFixedHeight(52)

        btn_ann = QPushButton("5. Small ANN (3-layer)")
        btn_ann.clicked.connect(self.open_ann)
        btn_ann.setFixedHeight(52)

        # Add to columns (balanced)
        col1.addWidget(btn_reg)
        col1.addWidget(btn_km)

        col2.addWidget(btn_dt)
        col2.addWidget(btn_nb)
        col2.addWidget(btn_ann)

        # center the columns horizontally by adding stretch left/right
        grid.addStretch(1)
        grid.addLayout(col1, 2)
        grid.addSpacing(12)  # small gap between columns
        grid.addLayout(col2, 2)
        grid.addStretch(1)

        layout.addLayout(grid)

        layout.addStretch(1)  # push footer to bottom

        # Back to main dashboard
        back_btn = QPushButton("Back to Home")
        back_btn.setFixedHeight(40)
        back_btn.clicked.connect(self._go_back)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)

        # Styling for buttons compatible with dark neon theme:
        # - dark gradient background
        # - light text color so labels remain visible
        # - hover effect slightly brighter
        common_btn_style = """
            QPushButton {
                color: #eaf6ff;                          /* light text */
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                           stop:0 rgba(32,36,44,240),
                                           stop:1 rgba(44,28,60,240));
                border: 1px solid rgba(255,255,255,0.04);
                border-radius: 8px;
                padding-left: 14px;
                padding-right: 14px;
                font-size: 13px;
                text-align: left;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                           stop:0 rgba(44,48,56,255),
                                           stop:1 rgba(64,36,84,255));
            }
            QPushButton:pressed {
                padding-top: 1px;
                padding-bottom: 1px;
            }
        """

        # smaller, subtle style for back button (center)
        back_btn_style = """
            QPushButton {
                color: #cfe7f6;
                background-color: rgba(255,255,255,0.06);
                border-radius: 8px;
                padding-left: 18px;
                padding-right: 18px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.09);
            }
        """

        for w in (btn_reg, btn_km, btn_dt, btn_nb, btn_ann):
            w.setStyleSheet(common_btn_style)
            w.setCursor(Qt.PointingHandCursor)

        back_btn.setStyleSheet(back_btn_style)
        back_btn.setCursor(Qt.PointingHandCursor)

        self.setLayout(layout)

    # --- Openers for each visualizer (graceful fallback if missing) ---
    def _open_child(self, VisualizerClass, name):
        """Common handler to open a child visualizer safely."""
        if VisualizerClass is None:
            QMessageBox.warning(self, "Module missing",
                                f"{name} visualizer not found.\nCreate the file and class and reopen the hub.")
            return

        try:
            child = VisualizerClass()
        except Exception as e:
            QMessageBox.critical(self, "Error launching visualizer",
                                 f"Failed to create {name} visualizer:\n{e}")
            return

        # hide hub and show child; connect back signal if present
        self.hide()
        self.child_window = child
        if hasattr(child, "backToHomeSignal"):
            child.backToHomeSignal.connect(self.show)
        else:
            # fallback: when child destroyed, show hub again
            child.destroyed.connect(self.show)
        child.show()

    def open_regression(self):
        self._open_child(RegressionVisualizer, "Regression")

    def open_kmeans(self):
        self._open_child(KMeansVisualizer, "K-Means")

    def open_decision_tree(self):
        self._open_child(DecisionTreeVisualizer, "Decision Tree")

    def open_naive_bayes(self):
        self._open_child(NaiveBayesVisualizer, "Naive Bayes")

    def open_ann(self):
        self._open_child(ANNVisualizer, "ANN (3-layer)")

    # --- Back handler ---
    def _go_back(self):
        # close this hub and emit back signal for main window to show
        self.close()
        self.backToHomeSignal.emit()


# Standalone test
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = MLVisualizer()
    w.show()
    sys.exit(app.exec_())
