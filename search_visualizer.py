from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QSlider, QComboBox, QLineEdit, QSizePolicy, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


class SearchingVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Searching Visualizer")
        self.setGeometry(100, 80, 1000, 700)

        # Internal state
        self.arr = []
        self.sorted_arr = []
        self.target = None
        self.steps = []          # list of (current_index, found_index, color_list)
        self.step_ptr = 0
        self.colors = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step_animation)

        # UI setup
        self.setup_ui()

    def setup_ui(self):
        main = QVBoxLayout()
        main.setContentsMargins(18, 18, 18, 18)
        main.setSpacing(12)

        title = QLabel("Searching Algorithm Visualizer")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        # Controls row: algorithm select, array input, target input
        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.algo_box = QComboBox()
        self.algo_box.addItems(["Linear Search", "Binary Search"])
        self.algo_box.setFixedWidth(180)
        controls.addWidget(self.algo_box)

        self.array_input = QLineEdit()
        self.array_input.setPlaceholderText("Enter array e.g. 1,2,3,4,5 or leave blank for default")
        controls.addWidget(self.array_input, 1)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Enter target")
        self.target_input.setFixedWidth(140)
        controls.addWidget(self.target_input)

        main.addLayout(controls)

        # Speed slider and buttons row
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        speed_label = QLabel("Speed:")
        speed_label.setFixedWidth(50)
        row2.addWidget(speed_label)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(100)   # fast
        self.speed_slider.setMaximum(1000)  # slow
        self.speed_slider.setValue(400)
        row2.addWidget(self.speed_slider, 1)

        self.start_btn = QPushButton("Start Search")
        self.start_btn.setFixedWidth(140)
        self.start_btn.clicked.connect(self.on_start)
        row2.addWidget(self.start_btn)

        self.back_btn = QPushButton("Back to Home")
        self.back_btn.setFixedWidth(140)
        self.back_btn.clicked.connect(self.on_back)
        row2.addWidget(self.back_btn)

        main.addLayout(row2)

        # Result label
        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.result_label.setAlignment(Qt.AlignCenter)
        main.addWidget(self.result_label)

        # Matplotlib figure (embedded)
        self.figure, self.ax = plt.subplots(figsize=(9, 3.8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main.addWidget(self.canvas)

        # Explanation text area
        self.explanation = QTextEdit()
        self.explanation.setReadOnly(True)
        self.explanation.setFixedHeight(220)
        self.explanation.setStyleSheet("background-color: #f7f7f7;")
        main.addWidget(self.explanation)

        self.setLayout(main)

        # Default array
        self.default_array = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33, 44, 55, 66, 77, 88, 99]
        self.show_static_array(self.default_array)

    # ---------------------------
    def parse_input(self):
        text = self.array_input.text().strip()
        if not text:
            arr = list(self.default_array)
        else:
            try:
                arr = [int(x.strip()) for x in text.split(",") if x.strip() != ""]
            except ValueError:
                raise ValueError("Array values must be integers separated by commas.")
        self.arr = arr
        self.sorted_arr = sorted(arr)
        return arr

    # ---------------------------
    def on_start(self):
        if self.timer.isActive():
            self.timer.stop()
        self.step_ptr = 0
        self.steps = []
        self.colors = []

        # parse array
        try:
            arr = self.parse_input()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
            return

        # parse target
        txt = self.target_input.text().strip()
        if txt == "":
            QMessageBox.warning(self, "Input Required", "Please enter a target value.")
            return
        try:
            self.target = int(txt)
        except ValueError:
            QMessageBox.warning(self, "Invalid Target", "Target must be an integer.")
            return

        algo = self.algo_box.currentText()
        if algo == "Linear Search":
            self.prepare_linear_steps(arr, self.target)
        else:
            self.prepare_binary_steps(self.sorted_arr, self.target)

        interval = self.speed_slider.value()
        self.timer.start(interval)

    # ---------------------------
    def prepare_linear_steps(self, arr, target):
        self.steps = []
        base_colors = ["#7fb3ff"] * len(arr)

        for i in range(len(arr)):
            colors_copy = list(base_colors)
            colors_copy[i] = "#ffa500"  # orange for current
            self.steps.append((i, -1, colors_copy))

            if arr[i] == target:
                colors_found = list(colors_copy)
                colors_found[i] = "#6fe07f"  # green for found
                self.steps.append((i, i, colors_found))
                break
        else:
            self.steps.append((-1, -1, list(base_colors)))

        self.visual_array = list(arr)
        self.result_label.setText("")
        self.explanation.clear()
        self.redraw_from_step(0)

    # ---------------------------
    def prepare_binary_steps(self, sorted_arr, target):
        arr = list(sorted_arr)
        self.visual_array = arr
        self.steps = []
        self.colors = ["#7fb3ff"] * len(arr)

        low = 0
        high = len(arr) - 1
        found = False

        while low <= high:
            mid = (low + high) // 2
            colors_copy = list(self.colors)
            colors_copy[mid] = "#ffa500"  # orange mid
            self.steps.append((mid, -1, colors_copy))

            if arr[mid] == target:
                colors_found = list(colors_copy)
                colors_found[mid] = "#6fe07f"  # green found
                self.steps.append((mid, mid, colors_found))
                found = True
                break
            elif arr[mid] < target:
                low = mid + 1
            else:
                high = mid - 1

        if not found:
            self.steps.append((-1, -1, list(self.colors)))

        self.result_label.setText("")
        self.explanation.clear()
        self.redraw_from_step(0)

    # ---------------------------
    def step_animation(self):
        if self.step_ptr >= len(self.steps):
            self.timer.stop()
            self.show_explanation_after_steps()
            return

        current, found, colors = self.steps[self.step_ptr]
        self.current_index = current
        self.result_index = found
        self.colors = colors
        self.redraw_from_step(self.step_ptr)
        self.step_ptr += 1

        if found != -1:
            self.timer.stop()
            self.show_explanation_after_steps()

    # ---------------------------
    def redraw_from_step(self, step_idx):
        self.ax = self.figure_axes()
        self.ax.clear()
        x_positions = range(len(self.visual_array))
        self.ax.bar(x_positions, self.visual_array, color=self.colors, edgecolor="black")
        for i, val in enumerate(self.visual_array):
            self.ax.text(i, val + max(self.visual_array) * 0.03, str(val),
                         ha="center", va="bottom", fontsize=8)
        self.ax.set_xticks([])
        self.ax.set_title("Visualization")
        self.canvas.draw()

        if hasattr(self, "result_index") and self.result_index != -1:
            idx = self.result_index
            self.result_label.setText(f"Target {self.target} found at index {idx}")
            self.result_label.setStyleSheet("color: blue; font-weight: bold;")
        else:
            self.result_label.setText("")

    # ---------------------------
    def show_explanation_after_steps(self):
        algo = self.algo_box.currentText()
        found_index = -1
        for _, fidx, _ in self.steps:
            if fidx != -1:
                found_index = fidx
                break

        if algo == "Linear Search":
            arr = self.arr if self.arr else self.default_array
            if found_index != -1:
                msg = f"The algorithm found the target {self.target} at index {found_index}."
                self.result_label.setText(f"Target {self.target} found at index {found_index}")
            else:
                msg = f"The target {self.target} was not found in the list."
                self.result_label.setText(msg)
                self.result_label.setStyleSheet("color: red; font-weight: bold;")

            explanation = (
                "<b>Algorithm Used:</b> Linear Search<br><br>"
                "Linear Search checks each element in the list sequentially until the target value is found or the list ends.<br><br>"
                "<b>Time Complexity:</b><br>"
                "• Best Case: O(1)<br>"
                "• Average Case: O(n/2)<br>"
                "• Worst Case: O(n)<br><br>"
                f"{msg}"
            )
            self.explanation.setHtml(explanation)

        else:  # Binary
            arr = self.visual_array
            if found_index != -1:
                msg = f"The algorithm found the target {self.target} at index {found_index} (in the sorted array)."
                self.result_label.setText(f"Target {self.target} found at index {found_index}")
            else:
                msg = f"The target {self.target} was not found in the sorted list."
                self.result_label.setText(msg)
                self.result_label.setStyleSheet("color: red; font-weight: bold;")

            explanation = (
                "<b>Algorithm Used:</b> Binary Search<br><br>"
                "Binary Search works on sorted arrays by repeatedly dividing the search interval in half.<br><br>"
                "<b>Time Complexity:</b><br>"
                "• Best Case: O(1)<br>"
                "• Average Case: O(log n)<br>"
                "• Worst Case: O(log n)<br><br>"
                f"{msg}"
            )
            self.explanation.setHtml(explanation)

    # ---------------------------
    def figure_axes(self):
        if not hasattr(self, "ax") or self.ax is None:
            self.ax = self.figure.add_subplot(111)
        return self.ax

    def show_static_array(self, arr):
        self.visual_array = arr
        self.colors = ["#7fb3ff"] * len(arr)
        self.figure_axes().clear()
        self.figure_axes().bar(range(len(arr)), arr, color=self.colors, edgecolor="black")
        self.figure_axes().set_title("Initial Array")
        self.canvas.draw()

    # ---------------------------
    def on_back(self):
        if self.timer.isActive():
            self.timer.stop()
        self.close()
        self.backToHomeSignal.emit()


# Standalone test
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = SearchingVisualizer()
    win.show()
    sys.exit(app.exec_())
