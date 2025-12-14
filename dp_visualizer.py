# dp_visualizer.py
# Dynamic Programming Visualizer for PyQt5
# Algorithms included: Fibonacci (tabulation), 0/1 Knapsack, LCS, Coin Change (min coins)
# Uses QTableWidget for DP tables and matplotlib for Fibonacci bar chart
# Emits backToHomeSignal to integrate with main app

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QComboBox,
    QLineEdit, QSlider, QSizePolicy, QTextEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


class DPVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic Programming Visualizer")
        self.setGeometry(120, 60, 1000, 700)

        # state
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)
        self.steps = []          # list of step functions (callables)
        self.step_ptr = 0
        self.current_algo = None

        # UI
        self.setup_ui()

    def setup_ui(self):
        main = QVBoxLayout()
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        title = QLabel("Dynamic Programming Visualizer")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        # Controls: algorithm select, input fields (will switch based on algorithm)
        ctrl_row = QHBoxLayout()
        self.algo_box = QComboBox()
        self.algo_box.addItems(["Fibonacci (Tabulation)", "0/1 Knapsack", "Longest Common Subsequence", "Coin Change (Min coins)"])
        self.algo_box.currentIndexChanged.connect(self.on_algo_change)
        ctrl_row.addWidget(self.algo_box, 1)

        # common controls container
        self.input_container = QHBoxLayout()
        ctrl_row.addLayout(self.input_container, 3)

        main.addLayout(ctrl_row)

        # Speed & start/back buttons
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        speed_label = QLabel("Speed:")
        speed_label.setFixedWidth(50)
        row2.addWidget(speed_label)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(1500)
        self.speed_slider.setValue(400)
        row2.addWidget(self.speed_slider, 1)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.on_start)
        row2.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.on_stop)
        row2.addWidget(self.stop_btn)

        self.back_btn = QPushButton("Back to Home")
        self.back_btn.clicked.connect(self.on_back)
        row2.addWidget(self.back_btn)

        main.addLayout(row2)

        # Split: left (DP table / chart), right (explanation + details)
        content_row = QHBoxLayout()

        # Left: Table or Canvas area
        left_col = QVBoxLayout()

        # Matplotlib canvas for Fibonacci bars (created but hidden except for Fibonacci)
        self.fig, self.ax = plt.subplots(figsize=(6, 3.2))
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_col.addWidget(self.canvas)

        # Table widget for DP tables
        self.table = QTableWidget()
        left_col.addWidget(self.table)

        content_row.addLayout(left_col, 2)

        # Right: Explanation & outputs
        right_col = QVBoxLayout()
        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Arial", 12, QFont.Bold))
        right_col.addWidget(self.result_label)

        self.explanation = QTextEdit()
        self.explanation.setReadOnly(True)
        self.explanation.setFixedHeight(300)
        right_col.addWidget(self.explanation)

        content_row.addLayout(right_col, 1)

        main.addLayout(content_row)

        self.setLayout(main)

        # prepare dynamic input widgets
        self.on_algo_change(0)

    # ----------------- UI input builders per algorithm -----------------
    def clear_input_container(self):
        # remove existing widgets from input container
        while self.input_container.count():
            item = self.input_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def on_algo_change(self, idx):
        self.current_algo = self.algo_box.currentText()
        self.clear_input_container()
        # Fibonacci: input n (spinbox)
        if self.current_algo.startswith("Fibonacci"):
            lbl = QLabel("n:")
            self.input_container.addWidget(lbl)
            self.fib_input = QSpinBox()
            self.fib_input.setMinimum(1)
            self.fib_input.setMaximum(50)
            self.fib_input.setValue(12)
            self.input_container.addWidget(self.fib_input)
            # hide table, show canvas
            self.table.hide()
            self.canvas.show()
            self.result_label.setText("")
            self.explanation.setHtml(self._fib_explanation())
            # draw default
            self.draw_fib_static(self.fib_input.value())
        elif self.current_algo.startswith("0/1 Knapsack"):
            # items input: weights, values and capacity
            self.table.show()
            self.canvas.hide()
            lbl1 = QLabel("weights (comma):")
            self.input_container.addWidget(lbl1)
            self.weights_input = QLineEdit()
            self.weights_input.setPlaceholderText("e.g. 2,3,4")
            self.input_container.addWidget(self.weights_input, 1)
            lbl2 = QLabel("values (comma):")
            self.input_container.addWidget(lbl2)
            self.values_input = QLineEdit()
            self.values_input.setPlaceholderText("e.g. 3,4,5")
            self.input_container.addWidget(self.values_input, 1)
            lbl3 = QLabel("Capacity:")
            self.input_container.addWidget(lbl3)
            self.capacity_input = QSpinBox()
            self.capacity_input.setMinimum(1)
            self.capacity_input.setMaximum(1000)
            self.capacity_input.setValue(10)
            self.input_container.addWidget(self.capacity_input)
            self.explanation.setHtml(self._knap_explanation())
            self.result_label.setText("")
            self.table.clear()
        elif self.current_algo.startswith("Longest Common Subsequence"):
            self.table.show()
            self.canvas.hide()
            lbl1 = QLabel("String A:")
            self.input_container.addWidget(lbl1)
            self.a_input = QLineEdit()
            self.input_container.addWidget(self.a_input)
            lbl2 = QLabel("String B:")
            self.input_container.addWidget(lbl2)
            self.b_input = QLineEdit()
            self.input_container.addWidget(self.b_input)
            self.explanation.setHtml(self._lcs_explanation())
            self.result_label.setText("")
            self.table.clear()
        elif self.current_algo.startswith("Coin Change"):
            self.table.show()
            self.canvas.hide()
            lbl1 = QLabel("coins (comma):")
            self.input_container.addWidget(lbl1)
            self.coins_input = QLineEdit()
            self.coins_input.setPlaceholderText("e.g. 1,2,5")
            self.input_container.addWidget(self.coins_input, 1)
            lbl2 = QLabel("Amount:")
            self.input_container.addWidget(lbl2)
            self.amount_input = QSpinBox()
            self.amount_input.setMinimum(1)
            self.amount_input.setMaximum(10000)
            self.amount_input.setValue(27)
            self.input_container.addWidget(self.amount_input)
            self.explanation.setHtml(self._coin_explanation())
            self.result_label.setText("")
            self.table.clear()

    # ----------------- Start / Stop / Back -----------------
    def on_start(self):
        # initialize steps based on algorithm
        if self.timer.isActive():
            self.timer.stop()
        self.steps = []
        self.step_ptr = 0
        algo = self.current_algo
        try:
            if algo.startswith("Fibonacci"):
                n = int(self.fib_input.value())
                self.prepare_fibonacci_steps(n)
            elif algo.startswith("0/1 Knapsack"):
                weights = self._parse_csv_ints(self.weights_input.text())
                values = self._parse_csv_ints(self.values_input.text())
                if len(weights) == 0 or len(values) == 0 or len(weights) != len(values):
                    raise ValueError("Provide matching comma-separated weights and values.")
                cap = int(self.capacity_input.value())
                self.prepare_knap_steps(weights, values, cap)
            elif algo.startswith("Longest Common Subsequence"):
                a = self.a_input.text()
                b = self.b_input.text()
                if a == "" or b == "":
                    raise ValueError("Provide both strings.")
                self.prepare_lcs_steps(a, b)
            elif algo.startswith("Coin Change"):
                coins = self._parse_csv_ints(self.coins_input.text())
                if len(coins) == 0:
                    raise ValueError("Provide coin denominations.")
                amt = int(self.amount_input.value())
                self.prepare_coin_steps(coins, amt)
            else:
                raise ValueError("Unknown algorithm.")
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
            return

        interval = max(50, self.speed_slider.value())
        self.timer.start(interval)

    def on_stop(self):
        if self.timer.isActive():
            self.timer.stop()

    def on_back(self):
        if self.timer.isActive():
            self.timer.stop()
        self.close()
        self.backToHomeSignal.emit()

    # ----------------- Utilities -----------------
    def _parse_csv_ints(self, s):
        s = s.strip()
        if not s:
            return []
        parts = [p.strip() for p in s.split(",") if p.strip() != ""]
        try:
            return [int(x) for x in parts]
        except:
            raise ValueError("Input must be integers separated by commas.")

    # ----------------- Steps execution loop -----------------
    def step(self):
        if self.step_ptr >= len(self.steps):
            self.timer.stop()
            return
        action = self.steps[self.step_ptr]
        # action is a callable that updates UI
        try:
            action()
        except Exception as e:
            # stop on unexpected error and show
            self.timer.stop()
            QMessageBox.critical(self, "Runtime Error", str(e))
            return
        self.step_ptr += 1

    # ----------------- Fibonacci (tabulation) -----------------
    def _fib_explanation(self):
        return (
            "<b>Fibonacci (Tabulation)</b><br><br>"
            "Build an array dp[0..n] where dp[i] = dp[i-1] + dp[i-2].<br>"
            "This visualizer shows the array evolving. Complexity: O(n) time, O(n) space."
        )

    def draw_fib_static(self, n):
        arr = [0] * (n + 1)
        arr[0] = 0
        if n >= 1:
            arr[1] = 1
        self.ax.clear()
        self.ax.bar(range(len(arr)), arr, color="#7fb3ff", edgecolor="black")
        self.ax.set_title(f"Fibonacci array (size {len(arr)})")
        self.canvas.draw()

    def prepare_fibonacci_steps(self, n):
        # prepare dp array; create steps showing each write
        dp = [0] * (n + 1)
        dp[0] = 0
        steps_local = []

        def show_step(highlight_index=None):
            def fn():
                self.ax.clear()
                colors = ["#7fb3ff"] * len(dp)
                if highlight_index is not None:
                    colors[highlight_index] = "#ffa500"
                self.ax.bar(range(len(dp)), dp, color=colors, edgecolor="black")
                self.ax.set_title("Fibonacci tabulation")
                # annotate values
                mx = max(max(dp), 1)
                for i, v in enumerate(dp):
                    self.ax.text(i, v + mx * 0.03, str(v), ha="center", fontsize=9)
                self.canvas.draw()
                self.result_label.setText(f"dp[{highlight_index}] = {dp[highlight_index]}" if highlight_index is not None else "")
            return fn

        # initial state
        steps_local.append(show_step(None))
        if n >= 1:
            dp[1] = 1
            steps_local.append(show_step(1))

        for i in range(2, n + 1):
            dp[i] = dp[i - 1] + dp[i - 2]
            steps_local.append(show_step(i))

        # final explanation at end
        def final_fn():
            self.result_label.setText(f"F({n}) = {dp[n]}")
            self.explanation.append(f"<br><b>Result:</b> F({n}) = {dp[n]}<br>")
        steps_local.append(final_fn)

        self.steps = steps_local
        self.step_ptr = 0

    # ----------------- 0/1 Knapsack -----------------
    def _knap_explanation(self):
        return (
            "<b>0/1 Knapsack</b><br><br>"
            "Given weights[] and values[] and a capacity W, build DP table dp[i][w] = maximum value using first i items with capacity w."
        )

    def prepare_knap_steps(self, weights, values, capacity):
        n = len(weights)
        # dp 2D table (n+1) x (capacity+1)
        dp = [[0] * (capacity + 1) for _ in range(n + 1)]
        steps_local = []

        # first step: draw empty table
        def draw_table(highlight=None, note=""):
            def fn():
                # build table view
                self.table.clear()
                self.table.setRowCount(n + 1)
                self.table.setColumnCount(capacity + 1)
                self.table.setHorizontalHeaderLabels([str(c) for c in range(capacity + 1)])
                self.table.setVerticalHeaderLabels([str(i) for i in range(n + 1)])
                for i in range(n + 1):
                    for w in range(capacity + 1):
                        item = QTableWidgetItem(str(dp[i][w]))
                        if highlight and (i, w) == highlight:
                            item.setBackground(Qt.yellow)
                        self.table.setItem(i, w, item)
                self.result_label.setText(note)
            return fn

        steps_local.append(draw_table(None, "Initial DP table (all zeros)"))

        for i in range(1, n + 1):
            wi = weights[i - 1]
            vi = values[i - 1]
            for w in range(0, capacity + 1):
                # record before
                steps_local.append(draw_table((i, w), f"Computing dp[{i}][{w}]"))
                if wi <= w:
                    val_take = dp[i - 1][w - wi] + vi
                    val_skip = dp[i - 1][w]
                    dp[i][w] = max(val_take, val_skip)
                else:
                    dp[i][w] = dp[i - 1][w]
                # record after write
                steps_local.append(draw_table((i, w), f"Set dp[{i}][{w}] = {dp[i][w]}"))
        # final step: reconstruct chosen items
        chosen = []
        w = capacity
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i - 1][w]:
                chosen.append(i - 1)  # item index
                w -= weights[i - 1]
        chosen.reverse()

        def final_fn():
            self.result_label.setText(f"Max value = {dp[n][capacity]}; chosen indices = {chosen}")
            self.explanation.append(f"<b>Result:</b> Max Value = {dp[n][capacity]}<br>Chosen items (0-based): {chosen}<br>")
            # also show final table
            draw_table(None, "Final DP table (end)")( )
        steps_local.append(final_fn)

        self.steps = steps_local
        self.step_ptr = 0

    # ----------------- LCS -----------------
    def _lcs_explanation(self):
        return (
            "<b>Longest Common Subsequence (LCS)</b><br><br>"
            "DP relation: if A[i-1] == B[j-1] then dp[i][j] = 1 + dp[i-1][j-1] else max(dp[i-1][j], dp[i][j-1])."
        )

    def prepare_lcs_steps(self, A, B):
        n = len(A)
        m = len(B)
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        steps_local = []

        def draw_dp(highlight=None, note=""):
            def fn():
                self.table.clear()
                self.table.setRowCount(n + 1)
                self.table.setColumnCount(m + 1)
                self.table.setHorizontalHeaderLabels([""] + list(B))
                self.table.setVerticalHeaderLabels([""] + list(A))
                for i in range(n + 1):
                    for j in range(m + 1):
                        val = dp[i][j]
                        item = QTableWidgetItem(str(val))
                        if highlight and (i, j) == highlight:
                            item.setBackground(Qt.yellow)
                        self.table.setItem(i, j, item)
                self.result_label.setText(note)
            return fn

        steps_local.append(draw_dp(None, "Initial 0-filled table"))

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                steps_local.append(draw_dp((i, j), f"Computing dp[{i}][{j}]"))
                if A[i - 1] == B[j - 1]:
                    dp[i][j] = 1 + dp[i - 1][j - 1]
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                steps_local.append(draw_dp((i, j), f"Set dp[{i}][{j}] = {dp[i][j]}"))
        # backtrack to get LCS
        i, j = n, m
        lcs_chars = []
        def backtrack_fn():
            nonlocal i, j
            while i > 0 and j > 0:
                if A[i - 1] == B[j - 1]:
                    lcs_chars.append(A[i - 1])
                    i -= 1; j -= 1
                else:
                    if dp[i - 1][j] >= dp[i][j - 1]:
                        i -= 1
                    else:
                        j -= 1
            lcs = "".join(reversed(lcs_chars))
            self.result_label.setText(f"LCS length = {len(lcs)}; LCS = '{lcs}'")
            self.explanation.append(f"<b>Result:</b> LCS = '{lcs}' (length {len(lcs)})")
            # show final table
            draw_dp(None, "Final DP table (end)")( )
        steps_local.append(backtrack_fn)

        self.steps = steps_local
        self.step_ptr = 0

    # ----------------- Coin Change (Min coins) -----------------
    def _coin_explanation(self):
        return (
            "<b>Coin Change (Min coins)</b><br><br>"
            "DP relation: dp[x] = min(dp[x], 1 + dp[x - coin]) for each coin. Initialize dp[0]=0 and large for others."
        )

    def prepare_coin_steps(self, coins, amount):
        INF = 10 ** 9
        dp = [INF] * (amount + 1)
        dp[0] = 0
        steps_local = []

        def draw_dp(idx=None, note=""):
            def fn():
                # show dp array as table with one row
                self.table.clear()
                self.table.setRowCount(2)
                self.table.setColumnCount(amount + 1)
                self.table.setVerticalHeaderLabels(["Index", "dp"])
                self.table.setHorizontalHeaderLabels([str(k) for k in range(amount + 1)])
                for k in range(amount + 1):
                    self.table.setItem(0, k, QTableWidgetItem(str(k)))
                    val = dp[k] if dp[k] != INF else "∞"
                    item = QTableWidgetItem(str(val))
                    if idx is not None and k == idx:
                        item.setBackground(Qt.yellow)
                    self.table.setItem(1, k, item)
                self.result_label.setText(note)
            return fn

        steps_local.append(draw_dp(None, "Initial dp array (dp[0]=0, others ∞)"))

        for coin in coins:
            for x in range(coin, amount + 1):
                steps_local.append(draw_dp(x, f"Considering coin {coin} for amount {x} (before)"))
                if dp[x - coin] + 1 < dp[x]:
                    dp[x] = dp[x - coin] + 1
                steps_local.append(draw_dp(x, f"After update dp[{x}] = {dp[x] if dp[x] != INF else '∞'}"))
        def final_fn():
            if dp[amount] >= INF:
                self.result_label.setText("No solution (cannot form amount with given coins).")
                self.explanation.append("<b>Result:</b> No solution")
            else:
                # reconstruct (greedy-ish) one solution path
                amt = amount
                used = []
                while amt > 0:
                    for c in coins:
                        if amt - c >= 0 and dp[amt - c] == dp[amt] - 1:
                            used.append(c)
                            amt -= c
                            break
                    else:
                        # fail-safe
                        break
                self.result_label.setText(f"Min coins = {dp[amount]}; coins used = {used}")
                self.explanation.append(f"<b>Result:</b> Min coins = {dp[amount]}; coins used = {used}")
            draw_dp(None, "Final dp array (end)")( )
        steps_local.append(final_fn)

        self.steps = steps_local
        self.step_ptr = 0

    # ----------------- Explanations helpers -----------------
    # Short static explanations already embedded above; can extend if needed.

# Standalone test
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = DPVisualizer()
    w.show()
    sys.exit(app.exec_())
