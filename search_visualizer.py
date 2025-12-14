from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QSlider, QComboBox, QLineEdit, QSizePolicy,
    QMessageBox, QTextEdit, QFrame, QSplitter, QGraphicsView, QGraphicsScene
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush, QPen
import random
import sys


# --- ALGOQUEST COLOR PALETTE ---
COL_NEON_DEFAULT = "#80fac0"      # Neon Cyan/Green (Default bar)
COL_HIGHLIGHT_CURRENT = "#ffd600" # Yellow/Gold (Current index / midpoint)
COL_HIGHLIGHT_SWAP = "#ff5050"    # Neon Red (failed / not found)
COL_HIGHLIGHT_FOUND = "#6fe07f"   # Neon Green (Found)

# Gradient Colors (Matching Sorting Visualizer's paintEvent)
GRADIENT_COLOR_0 = QColor(15, 32, 39)
GRADIENT_COLOR_1 = QColor(20, 40, 50)
GRADIENT_COLOR_2 = QColor(30, 60, 70)

COL_DARK_FRAME = "rgba(30, 45, 55, 200)"  # Control Deck Background


# --- ALGORITHM CONTENT AND STYLING DETAILS ---
SEARCH_ALGORITHM_DETAILS = {
    "Linear Search": {
        "Theory": """
                    <h3>Linear Search: Sequential Check</h3>
                    <p>Linear Search checks every element in the array sequentially, one by one, until the target value is found or the end of the list is reached. It works on both sorted and unsorted lists.</p>
                    <h4>Complexity Analysis:</h4>
                    <ul>
                    <li><b>Best Case (Target at index 0):</b> O(1).</li>
                    <li><b>Average Case:</b> O(n/2), simplified to O(n).</li>
                    <li><b>Worst Case (Target not found / at end):</b> O(n). Must check every element.</li>
                    </ul>
                    """,
        "PseudoCode": "procedure linearSearch(A, target)\n  for i = 0 to length(A) - 1 do\n    if A[i] == target then\n      return i\n    end if\n  end for\n  return NOT_FOUND\nend procedure",
        "Color_Default": COL_NEON_DEFAULT,
        "Color_Current": COL_HIGHLIGHT_SWAP,
        "Color_Found": COL_HIGHLIGHT_FOUND,
        "Requires_Sorted": False
    },
    "Binary Search": {
        "Theory": """
                    <h3>Binary Search: Divide and Conquer</h3>
                    <p>Binary Search is an extremely fast search method that absolutely requires the input array to be sorted. The visualization first sorts the input data and then applies the binary search process, as the algorithm relies on the ordered property of the array to eliminate half of the search space in every step. </p>
                    <h4>Complexity Analysis:</h4>
                    <ul>
                    <li><b>Best Case (Target at midpoint):</b> O(1).</li>
                    <li><b>Average/Worst Case:</b> O(log n). The search space is halved in each step.</li>
                    <li><b>Requirement:</b> Array MUST be sorted.</li>
                    </ul>
                    """,
        "PseudoCode": "procedure binarySearch(A, target)\n  low = 0\n  high = length(A) - 1\n  while low <= high do\n    mid = (low + high) / 2\n    if A[mid] == target then\n      return mid\n    else if A[mid] < target then\n      low = mid + 1\n    else\n      high = mid - 1\n    end if\n  end while\n  return NOT_FOUND\nend procedure",
        "Color_Default": COL_NEON_DEFAULT,
        "Color_Current": COL_HIGHLIGHT_CURRENT,
        "Color_Found": COL_HIGHLIGHT_FOUND,
        "Requires_Sorted": True
    }
}


class SearchingVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Searching Visualizer - AlgoQUEST")
        self.resize(1300, 850)

        # Internal state
        self.arr = []
        self.sorted_arr = []
        self.target = None
        self.steps = []
        self.step_ptr = 0
        self.current_colors = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step_animation)
        self.is_running = False

        # visualization indices
        self.current_index = -1
        self.result_index = -1

        # graphics view for bars (like sorting visualizer)
        self.scene = None
        self.view = None
        self.visual_array = []

        # UI setup
        self.setStyleSheet(self._get_style_sheet())
        self.setup_ui()

        # Default setup
        self.default_array = [random.randint(10, 99) for _ in range(15)]
        self.array_input.setText(", ".join(map(str, self.default_array)))
        self.target_input.setText(str(random.choice(self.default_array)))

        # Initial calls
        self.parse_input()
        self.show_static_array(self.arr)
        self._update_explanation_content()

    # ---------- background ----------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0.0, GRADIENT_COLOR_0)
        gradient.setColorAt(0.5, GRADIENT_COLOR_1)
        gradient.setColorAt(1.0, GRADIENT_COLOR_2)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

        dot_pen = QPen(QColor(80, 250, 220, 20))
        dot_pen.setWidth(2)
        painter.setPen(dot_pen)
        grid_spacing = 40
        for x in range(0, w, grid_spacing):
            for y in range(0, h, grid_spacing):
                painter.drawPoint(x, y)

    # ---------- styles ----------
    def _get_style_sheet(self):
        return f"""
        QWidget {{ background: transparent; color: #dbeaf2; font-family: "Segoe UI", "Arial"; }}
        QLabel {{ background: transparent; color: #dbeaf2; }}

        QPushButton {{
            background-color: #4a4a4a; border: 1px solid #777; border-radius: 8px; padding: 5px 15px;
            color: #dbeaf2; font-weight: bold; font-size: 13px;
        }}
        QPushButton:hover {{ background-color: #555555; }}
        QPushButton#start_btn {{ background-color: {COL_NEON_DEFAULT}; color: #1a1a1a; border: none; }}
        QPushButton#start_btn:hover {{ background-color: #a0fcd0; }}

        /* back button style */
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

        QComboBox, QLineEdit {{
            background-color: rgba(20, 30, 40, 200); border: 1px solid #57606f; padding: 5px; border-radius: 8px;
            color: #dbeaf2; font-family: 'Consolas';
        }}

        QSlider::groove:horizontal {{ border: 1px solid #3d3d3d; height: 6px; background: #202020; margin: 2px 0; border-radius: 3px; }}
        QSlider::handle:horizontal {{ background: {COL_HIGHLIGHT_CURRENT}; border: 1px solid #fff; width: 14px; margin: -5px 0; border-radius: 7px; }}

        QTextEdit {{
            background: transparent;
            border: none;
            color: #dbeaf2;
            padding: 0px;
        }}
        QTextEdit#code_box {{
            background-color: #1e1e1e;
            border: 1px solid #333;
            border-radius: 5px;
            color: #dcdde1;
            font-family: 'Consolas';
            font-size: 13px;
            padding: 10px;
        }}

        QFrame#control_deck {{
            background-color: {COL_DARK_FRAME};
            border-radius: 12px;
            border: 1px solid rgba(80, 250, 220, 50);
        }}

        QFrame#info_container {{
            background-color: rgba(20, 30, 40, 100);
            border-radius: 10px;
            padding: 15px;
        }}
        """

    # ---------- UI ----------
    def setup_ui(self):
        main = QVBoxLayout()
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(15)

        # 1. control deck
        control_deck = QFrame()
        control_deck.setObjectName("control_deck")
        control_deck.setFixedHeight(80)

        deck_layout = QHBoxLayout(control_deck)
        deck_layout.setContentsMargins(15, 10, 15, 10)
        deck_layout.setSpacing(15)

        # back button (updated)
        self.back_btn = QPushButton("← Back")
        self.back_btn.setObjectName("back_button")
        deck_layout.addWidget(self.back_btn)
        self.back_btn.clicked.connect(self.on_back)

        self.algo_box = QComboBox()
        self.algo_box.addItems(list(SEARCH_ALGORITHM_DETAILS.keys()))
        self.algo_box.setFixedWidth(180)
        self.algo_box.currentTextChanged.connect(self.handle_algo_change)
        deck_layout.addWidget(self.algo_box)

        lbl_input = QLabel("Input (comma separated):")
        lbl_input.setStyleSheet("color: #aabdc9; font-weight: bold;")
        deck_layout.addWidget(lbl_input)

        self.array_input = QLineEdit()
        self.array_input.setPlaceholderText("e.g. 10, 20, 30...")
        self.array_input.textChanged.connect(self.handle_input_change)
        deck_layout.addWidget(self.array_input, stretch=1)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Target")
        self.target_input.setFixedWidth(100)
        self.target_input.textChanged.connect(self.handle_input_change)
        deck_layout.addWidget(self.target_input)

        speed_label = QLabel("Speed:")
        deck_layout.addWidget(speed_label)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(1000)
        self.speed_slider.setValue(400)
        self.speed_slider.setFixedWidth(150)
        deck_layout.addWidget(self.speed_slider)

        self.start_btn = QPushButton("Start Search")
        self.start_btn.setObjectName("start_btn")
        deck_layout.addWidget(self.start_btn)
        self.start_btn.clicked.connect(self.on_start)

        main.addWidget(control_deck)

        # 2. result label + graphics view
        self.result_label = QLabel("Visualization Ready")
        self.result_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet(f"color: {COL_NEON_DEFAULT};")
        main.addWidget(self.result_label)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main.addWidget(self.view, 4)

        # 3. info panel
        info_container = QFrame()
        info_container.setObjectName("info_container")
        info_v_layout = QVBoxLayout(info_container)
        info_v_layout.setContentsMargins(0, 0, 0, 0)

        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setStyleSheet("QSplitter::handle { background: #57606f; width: 4px; }")

        self.theory_box = QTextEdit()
        self.theory_box.setReadOnly(True)
        content_splitter.addWidget(self.theory_box)

        self.code_box = QTextEdit()
        self.code_box.setReadOnly(True)
        self.code_box.setObjectName("code_box")
        content_splitter.addWidget(self.code_box)

        content_splitter.setSizes([300, 300])
        info_v_layout.addWidget(content_splitter)
        main.addWidget(info_container)

        self.setLayout(main)

    # ---------- drawing bars (like sorting visualizer) ----------
    def draw_bars(self, highlight_indices=None, found_indices=None):
        if highlight_indices is None:
            highlight_indices = []
        if found_indices is None:
            found_indices = []

        if self.scene is None or self.view is None:
            return

        self.scene.clear()
        n = len(self.visual_array)
        if n == 0:
            return

        view_w = self.view.viewport().width() - 20
        view_h = self.view.viewport().height() - 20

        bar_w = min(50, max(5, view_w / n))
        spacing = 2
        total_w = n * (bar_w + spacing)
        start_x = (view_w - total_w) / 2

        max_val = max(self.visual_array) if self.visual_array else 1

        details = SEARCH_ALGORITHM_DETAILS[self.algo_box.currentText()]
        default_color_q = QColor(details["Color_Default"])
        current_color_q = QColor(details["Color_Current"])
        found_color_q = QColor(details["Color_Found"])

        for i, val in enumerate(self.visual_array):
            h = (val / max_val) * (view_h * 0.9)
            x = start_x + i * (bar_w + spacing)
            y = view_h - h

            if i in found_indices:
                color = found_color_q
            elif i in highlight_indices:
                color = current_color_q
            else:
                color = default_color_q

            rect = self.scene.addRect(x, y, bar_w, h)
            rect.setPen(QPen(Qt.NoPen))
            rect.setBrush(QBrush(color))

            if bar_w > 20:
                text_item = self.scene.addText(str(val))
                text_item.setDefaultTextColor(QColor("white"))
                font = QFont("Segoe UI", 8)
                text_item.setFont(font)
                txt_w = text_item.boundingRect().width()
                text_item.setPos(x + (bar_w - txt_w) / 2, y - 20)

    # ---------- handlers ----------
    def handle_input_change(self):
        if self.timer.isActive():
            return
        self.parse_input()
        self.show_static_array(self.arr)
        self._update_explanation_content()
        self.reset_ui_state()

    def handle_algo_change(self):
        self.update_explanation()

    def reset_ui_state(self):
        if self.timer.isActive():
            self.timer.stop()
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.step_ptr = 0
        self.steps = []
        self.current_index = -1
        self.result_index = -1
        self.result_label.setText("Visualization Ready")
        self.result_label.setStyleSheet(f"color: {COL_NEON_DEFAULT};")

    def _update_explanation_content(self):
        algo = self.algo_box.currentText()
        details = SEARCH_ALGORITHM_DETAILS[algo]

        self.parse_input(silent=True)

        binary_explainer = ""
        if algo == "Binary Search":
            binary_explainer = (
                f"<p style='color:{COL_NEON_DEFAULT};'>Note: Binary Search "
                f"requires a sorted list. The visualization uses the pre-sorted "
                f"version of your input array (length N={len(self.arr) if self.arr else 0}).</p>"
            )

        theory_html = f"<h2>{algo} Theory</h2>"
        theory_html += details["Theory"]
        theory_html += binary_explainer
        theory_html += "<br><i>Click 'Start Search' to begin the visualization.</i>"

        self.theory_box.setHtml(theory_html)
        self.code_box.setPlainText(details["PseudoCode"])

    def update_explanation(self):
        self.parse_input()
        self.show_static_array(self.arr)
        self._update_explanation_content()
        self.reset_ui_state()

    # ---------- parsing ----------
    def parse_input(self, silent=False):
        text = self.array_input.text().strip()

        if not text:
            arr = list(self.default_array)
        else:
            try:
                arr = [int(x.strip()) for x in text.split(",") if x.strip() != ""]
            except ValueError:
                if not silent:
                    raise ValueError("Array values must be integers separated by commas.")
                else:
                    arr = list(self.default_array)

        target_text = self.target_input.text().strip()
        if target_text != "":
            try:
                self.target = int(target_text)
            except ValueError:
                if not silent:
                    raise ValueError("Target must be an integer.")
                else:
                    self.target = None
        else:
            self.target = None

        self.arr = arr
        self.sorted_arr = sorted(arr)
        return arr

    # ---------- start search ----------
    def on_start(self):
        if self.is_running:
            return

        try:
            arr = self.parse_input()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
            return

        if self.target is None:
            QMessageBox.warning(self, "Input Required", "Please enter a target value.")
            return

        algo = self.algo_box.currentText()

        self.current_index = -1
        self.result_index = -1

        self.is_running = True
        self.start_btn.setEnabled(False)
        self.result_label.setText(f"Searching for {self.target} using {algo}...")
        self.result_label.setStyleSheet(f"color: {COL_HIGHLIGHT_CURRENT};")

        if algo == "Linear Search":
            self.prepare_linear_steps(arr, self.target)
        else:
            self.prepare_binary_steps(self.sorted_arr, self.target)

        interval = self.speed_slider.value()
        self.timer.start(interval)

    # ---------- step generation ----------
    def prepare_linear_steps(self, arr, target):
        self.steps = []
        details = SEARCH_ALGORITHM_DETAILS["Linear Search"]
        default_color = details["Color_Default"]
        current_color = details["Color_Current"]
        found_color = details["Color_Found"]

        base_colors = [default_color] * len(arr)
        self.visual_array = list(arr)

        for i in range(len(arr)):
            colors_copy = list(base_colors)
            colors_copy[i] = current_color
            self.steps.append((i, -1, colors_copy))

            if arr[i] == target:
                colors_found = list(colors_copy)
                colors_found[i] = found_color
                self.steps.append((i, i, colors_found))
                break
        else:
            self.steps.append((-1, -1, list(base_colors)))

        self.step_ptr = 0
        self.redraw_from_step(0)

    def prepare_binary_steps(self, sorted_arr, target):
        self.steps = []
        details = SEARCH_ALGORITHM_DETAILS["Binary Search"]
        default_color = details["Color_Default"]
        current_color = details["Color_Current"]
        found_color = details["Color_Found"]

        arr = list(sorted_arr)
        self.visual_array = arr

        initial_colors = [default_color] * len(arr)
        self.steps.append((-1, -1, initial_colors))

        low = 0
        high = len(arr) - 1
        found = False

        while low <= high:
            mid = (low + high) // 2
            colors_copy = list(initial_colors)

            for i in range(low, high + 1):
                colors_copy[i] = "#3c4a5c"

            colors_copy[mid] = current_color
            self.steps.append((mid, -1, colors_copy))

            if arr[mid] == target:
                colors_found = list(colors_copy)
                colors_found[mid] = found_color
                self.steps.append((mid, mid, colors_found))
                found = True
                break
            elif arr[mid] < target:
                low = mid + 1
            else:
                high = mid - 1

        if not found:
            self.steps.append((-1, -1, list(initial_colors)))

        self.step_ptr = 0
        self.redraw_from_step(0)

    # ---------- animation ----------
    def step_animation(self):
        if self.step_ptr >= len(self.steps):
            self.timer.stop()
            self.show_explanation_after_steps()
            self.is_running = False
            self.start_btn.setEnabled(True)
            return

        current, found, colors = self.steps[self.step_ptr]
        self.current_index = current
        self.result_index = found
        self.current_colors = colors
        self.redraw_from_step(self.step_ptr)
        self.step_ptr += 1

        if found != -1:
            self.timer.stop()
            self.show_explanation_after_steps()
            self.is_running = False
            self.start_btn.setEnabled(True)

    def redraw_from_step(self, step_idx):
        current, found, colors = self.steps[step_idx]
        self.current_index = current
        self.result_index = found
        self.current_colors = colors

        highlight_indices = []
        found_indices = []
        if current != -1:
            highlight_indices.append(current)
        if found != -1:
            found_indices.append(found)

        self.draw_bars(highlight_indices, found_indices)

        if self.result_index != -1:
            self.result_label.setText(
                f"SUCCESS: Target {self.target} found at index {self.result_index}"
            )
            self.result_label.setStyleSheet(
                f"color: {COL_HIGHLIGHT_FOUND}; font-weight: bold;"
            )
        elif self.current_index == -1 and self.step_ptr > 0:
            self.result_label.setText(
                f"FAILED: Target {self.target} not found in the array."
            )
            self.result_label.setStyleSheet(
                f"color: {COL_HIGHLIGHT_SWAP}; font-weight: bold;"
            )
        elif self.current_index != -1 and self.current_index < len(self.visual_array):
            self.result_label.setText(
                f"Comparing element at index {self.current_index} "
                f"(Value: {self.visual_array[self.current_index]})"
            )
            self.result_label.setStyleSheet(f"color: {COL_HIGHLIGHT_CURRENT};")
        else:
            self.result_label.setText(
                f"Searching for {self.target if self.target is not None else 'Target'}..."
            )

    # ---------- explanation after run ----------
    def show_explanation_after_steps(self):
        algo = self.algo_box.currentText()
        details = SEARCH_ALGORITHM_DETAILS[algo]

        if self.result_index != -1:
            msg = (
                f"<p><b>Execution Result:</b> The algorithm found the target "
                f"{self.target} at index {self.result_index}.</p>"
            )
        else:
            msg = (
                f"<p><b>Execution Result:</b> The target {self.target} "
                f"was not found in the list.</p>"
            )

        theory_html = f"<h2>{algo} Analysis</h2>"
        theory_html += details["Theory"]

        if algo == "Binary Search":
            theory_html += (
                f"<p style='color:{COL_NEON_DEFAULT};'>Note: Binary Search "
                f"requires a sorted list. The visualization uses the pre-sorted "
                f"version of your input array.</p>"
            )

        theory_html += msg

        self.theory_box.setHtml(theory_html)
        self.code_box.setPlainText(details["PseudoCode"])
        self.start_btn.setEnabled(True)

    # ---------- static drawing ----------
    def show_static_array(self, arr):
        self.visual_array = arr
        algo = self.algo_box.currentText()
        color_key = SEARCH_ALGORITHM_DETAILS[algo]["Color_Default"]
        self.current_colors = [color_key] * len(arr)
        self.draw_bars()

    # ---------- navigation ----------
    def on_back(self):
        if self.timer.isActive():
            self.timer.stop()
        self.close()
        self.backToHomeSignal.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SearchingVisualizer()
    win.show()
    sys.exit(app.exec_())
