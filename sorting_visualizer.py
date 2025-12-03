# sorting_visualizer.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QSlider,
    QGraphicsView, QGraphicsScene, QSpinBox, QTextEdit, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QPen, QFont
import random
import time
import copy

class SortingVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sorting Visualizer - algoQUIST")
        self.setGeometry(180, 90, 1000, 760)
        self.initUI()

    def initUI(self):
        # === Layouts ===
        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        algo_layout = QHBoxLayout()
        viz_layout = QVBoxLayout()
        summary_layout = QVBoxLayout()

        # === Title ===
        title = QLabel("Sorting Visualizer")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # === Algorithm selection ===
        algo_label = QLabel("Algorithm:")
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["Bubble Sort", "Selection Sort", "Insertion Sort", "Quick Sort", "Merge Sort"])
        self.algo_combo.setFixedWidth(160)
        algo_layout.addWidget(algo_label)
        algo_layout.addWidget(self.algo_combo)

        # === Array size slider + spinbox ===
        size_label = QLabel("Array size:")
        self.size_spin = QSpinBox()
        self.size_spin.setRange(5, 40)
        self.size_spin.setValue(20)
        self.size_spin.setFixedWidth(70)

        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(5, 40)
        self.size_slider.setValue(20)
        self.size_slider.setFixedWidth(220)
        self.size_slider.valueChanged.connect(self.size_spin.setValue)
        self.size_spin.valueChanged.connect(self.size_slider.setValue)

        size_layout = QHBoxLayout()
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_spin)
        algo_layout.addLayout(size_layout)

        control_layout.addLayout(algo_layout)

        # === Generate / Start / Reset buttons ===
        self.generate_btn = QPushButton("Generate Random Array")
        self.generate_btn.clicked.connect(self.generate_array)
        self.start_btn = QPushButton("Start Sorting")
        self.start_btn.clicked.connect(self.start_sorting)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_all)
        control_layout.addWidget(self.generate_btn)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.reset_btn)

        # === Speed control ===
        speed_label = QLabel("Speed:")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 1000)   # maps to timer interval ms (fast -> small ms)
        self.speed_slider.setValue(200)
        self.speed_slider.setFixedWidth(200)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        control_layout.addLayout(speed_layout)

        # === Back button ===
        self.back_btn = QPushButton("← Back to Home")
        self.back_btn.clicked.connect(self.go_back)
        control_layout.addWidget(self.back_btn)

        main_layout.addLayout(control_layout)

        # === Visualization area (QGraphicsScene) ===
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setMinimumHeight(420)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        viz_layout.addWidget(self.view)

        # === Info & Metrics area ===
        info_metrics_layout = QHBoxLayout()

        # Info box for explanation and complexity
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setFixedHeight(160)
        self.info_box.setFont(QFont("Arial", 11))
        info_metrics_layout.addWidget(self.info_box, 60)

        # Metrics panel
        metrics_panel = QVBoxLayout()
        self.comparisons_label = QLabel("Comparisons: 0")
        self.swaps_label = QLabel("Swaps/Assignments: 0")
        self.time_label = QLabel("Elapsed (simulated): 0.00s")
        for lbl in (self.comparisons_label, self.swaps_label, self.time_label):
            lbl.setFont(QFont("Arial", 11))
            metrics_panel.addWidget(lbl)
        metrics_panel.addStretch()
        info_metrics_layout.addLayout(metrics_panel, 40)

        viz_layout.addLayout(info_metrics_layout)
        main_layout.addLayout(viz_layout)

        # === Summary: best/avg/worst explanation (visible after execution) ===
        summary_title = QLabel("Execution Summary (shown after sorting)")
        summary_title.setFont(QFont("Arial", 12, QFont.Bold))
        summary_layout.addWidget(summary_title)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setFont(QFont("Arial", 11))
        self.summary_text.setFixedHeight(150)
        summary_layout.addWidget(self.summary_text)

        main_layout.addLayout(summary_layout)
        self.setLayout(main_layout)

        # === Internal state ===
        self.data = []
        self.steps = []               # list of tuples (arr_copy, highlight_indices, comps, swaps)
        self.step_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.play_step)
        self.start_time = 0.0

        # Prepare default array
        self.generate_array()

        # Show info for selected algorithm
        self.algo_combo.currentTextChanged.connect(self.show_algorithm_info)
        self.show_algorithm_info()

    # ---------------- UI & control methods ----------------

    def generate_array(self):
        n = self.size_spin.value()
        # generate random numbers within range so bars fit nicely
        self.data = [random.randint(10, 100) for _ in range(n)]
        self.draw_bars()
        # reset metrics & steps
        self.steps = []
        self.step_index = 0
        self.comparisons = 0
        self.swaps = 0
        self.update_metrics()
        self.summary_text.clear()

    def reset_all(self):
        self.timer.stop()
        self.generate_array()
        self.info_box.clear()
        self.summary_text.clear()

    def draw_bars(self, highlight=None):
        """Draw bars according to self.data. 'highlight' is a list of indices to color."""
        if highlight is None:
            highlight = []
        self.scene.clear()
        n = len(self.data)
        width = max(6, int(self.view.width() / (n + 1)))  # adaptive bar width
        spacing = 4
        maxh = 360
        max_val = max(self.data) if self.data else 1
        for i, val in enumerate(self.data):
            # scale height
            h = int((val / max_val) * maxh)
            x = i * (width + spacing)
            y = maxh - h
            color = QColor(100, 149, 237)  # default blue
            if i in highlight:
                color = QColor(255, 99, 71)  # red highlight
            rect = self.scene.addRect(x, y, width, h, QPen(Qt.black), QBrush(color))
            # draw value label if few elements
            if n <= 20:
                self.scene.addText(str(val)).setPos(x, y - 18)
        # force update
        self.view.setSceneRect(0, 0, max(800, n * (width + spacing)), maxh + 50)
        self.view.update()

    # ---------------- Sorting orchestration ----------------

    def start_sorting(self):
        if self.timer.isActive():
            return  # ignore if already running
        algo = self.algo_combo.currentText()
        # prepare steps anew from current self.data (do not modify displayed array until animation)
        self.steps = []
        self.comparisons = 0
        self.swaps = 0
        arr_copy = self.data.copy()

        if algo == "Bubble Sort":
            self.steps = self._bubble_steps(arr_copy)
        elif algo == "Selection Sort":
            self.steps = self._selection_steps(arr_copy)
        elif algo == "Insertion Sort":
            self.steps = self._insertion_steps(arr_copy)
        elif algo == "Quick Sort":
            self.steps = self._quick_steps(arr_copy)
        elif algo == "Merge Sort":
            self.steps = self._merge_steps(arr_copy)
        else:
            return

        if not self.steps:
            return

        self.step_index = 0
        self.start_time = time.time()
        interval = max(10, self.speed_slider.value())  # ms
        self.timer.start(interval)

    def play_step(self):
        if self.step_index >= len(self.steps):
            self.timer.stop()
            elapsed = time.time() - self.start_time
            self.time_label.setText(f"Elapsed (simulated): {elapsed:.3f}s")
            # final draw to ensure sorted array shown
            if self.steps:
                final_arr = self.steps[-1][0]
                self.data = final_arr.copy()
                self.draw_bars(highlight=[])
            # show summary and final metrics
            self.update_metrics(final=True)
            self.show_execution_summary()
            return

        arr_state, highlight, comps, swaps = self.steps[self.step_index]
        # update running comps/swaps
        self.comparisons = comps
        self.swaps = swaps
        # set data shown to current arr_state
        self.data = arr_state.copy()
        self.draw_bars(highlight=highlight)
        self.update_metrics()
        self.step_index += 1

    def update_metrics(self, final=False):
        self.comparisons_label.setText(f"Comparisons: {self.comparisons}")
        self.swaps_label.setText(f"Swaps/Assignments: {self.swaps}")
        if final:
            # keep elapsed time already set in play_step
            pass

    def go_back(self):
        # signal main to show home and close this window
        self.backToHomeSignal.emit()
        self.close()

    # ---------------- Algorithms that produce step lists ----------------
    # Each step is (arr_copy, highlight_indices, comparisons_so_far, swaps_so_far)

    def _bubble_steps(self, arr):
        steps = []
        comps = 0
        swaps = 0
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                comps += 1
                steps.append((arr.copy(), [j, j + 1], comps, swaps))
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swaps += 1
                    steps.append((arr.copy(), [j, j + 1], comps, swaps))
        # final state
        steps.append((arr.copy(), [], comps, swaps))
        return steps

    def _selection_steps(self, arr):
        steps = []
        comps = 0
        swaps = 0
        n = len(arr)
        for i in range(n):
            min_idx = i
            for j in range(i + 1, n):
                comps += 1
                steps.append((arr.copy(), [min_idx, j], comps, swaps))
                if arr[j] < arr[min_idx]:
                    min_idx = j
                    # highlight new min as change (no swap yet)
                    steps.append((arr.copy(), [min_idx], comps, swaps))
            # swap minimum into position i
            if min_idx != i:
                arr[i], arr[min_idx] = arr[min_idx], arr[i]
                swaps += 1
                steps.append((arr.copy(), [i, min_idx], comps, swaps))
        steps.append((arr.copy(), [], comps, swaps))
        return steps

    def _insertion_steps(self, arr):
        steps = []
        comps = 0
        swaps = 0  # here count assignments/shifts as swaps for demonstration
        n = len(arr)
        for i in range(1, n):
            key = arr[i]
            j = i - 1
            # show initial key
            steps.append((arr.copy(), [i], comps, swaps))
            while j >= 0:
                comps += 1
                steps.append((arr.copy(), [j, j + 1], comps, swaps))
                if arr[j] > key:
                    arr[j + 1] = arr[j]
                    swaps += 1
                    steps.append((arr.copy(), [j, j + 1], comps, swaps))
                    j -= 1
                else:
                    break
            arr[j + 1] = key
            swaps += 1
            steps.append((arr.copy(), [j + 1], comps, swaps))
        steps.append((arr.copy(), [], comps, swaps))
        return steps

    def _quick_steps(self, arr):
        steps = []
        comps = 0
        swaps = 0

        def partition(a, low, high):
            nonlocal comps, swaps, steps
            pivot = a[high]
            i = low - 1
            for j in range(low, high):
                comps += 1
                steps.append((a.copy(), [j, high], comps, swaps))
                if a[j] < pivot:
                    i += 1
                    a[i], a[j] = a[j], a[i]
                    swaps += 1
                    steps.append((a.copy(), [i, j], comps, swaps))
            a[i + 1], a[high] = a[high], a[i + 1]
            swaps += 1
            steps.append((a.copy(), [i + 1, high], comps, swaps))
            return i + 1

        def quicksort(a, low, high):
            if low < high:
                p = partition(a, low, high)
                quicksort(a, low, p - 1)
                quicksort(a, p + 1, high)

        quicksort(arr, 0, len(arr) - 1)
        steps.append((arr.copy(), [], comps, swaps))
        return steps

    def _merge_steps(self, arr):
        steps = []
        comps = 0
        swaps = 0  # count assignments into main array as swaps/assignments

        def merge(a, l, m, r):
            nonlocal comps, swaps, steps
            L = a[l:m+1]
            R = a[m+1:r+1]
            i = j = 0
            k = l
            while i < len(L) and j < len(R):
                comps += 1
                steps.append((a.copy(), [k], comps, swaps))
                if L[i] <= R[j]:
                    a[k] = L[i]
                    i += 1
                    swaps += 1
                else:
                    a[k] = R[j]
                    j += 1
                    swaps += 1
                steps.append((a.copy(), [k], comps, swaps))
                k += 1
            while i < len(L):
                a[k] = L[i]
                i += 1
                k += 1
                swaps += 1
                steps.append((a.copy(), [k-1], comps, swaps))
            while j < len(R):
                a[k] = R[j]
                j += 1
                k += 1
                swaps += 1
                steps.append((a.copy(), [k-1], comps, swaps))

        def mergesort(a, l, r):
            if l < r:
                m = (l + r) // 2
                mergesort(a, l, m)
                mergesort(a, m+1, r)
                merge(a, l, m, r)

        mergesort(arr, 0, len(arr) - 1)
        steps.append((arr.copy(), [], comps, swaps))
        return steps

    # ---------------- Execution summary (post-run) ----------------

    def show_algorithm_info(self):
        algo = self.algo_combo.currentText()
        text = ""
        if algo == "Bubble Sort":
            text = ("Bubble Sort:\n"
                    "- Repeatedly compares adjacent items and swaps them if out of order.\n"
                    "- Best case: O(n) (when array already sorted, one pass with no swaps)\n"
                    "- Average/Worst: O(n²) (nested passes). Space: O(1). Stable.\n")
        elif algo == "Selection Sort":
            text = ("Selection Sort:\n"
                    "- Finds the minimum element and places it each time at current index.\n"
                    "- Best/Average/Worst: O(n²) (comparisons always ~n²). Space: O(1). Not stable.\n")
        elif algo == "Insertion Sort":
            text = ("Insertion Sort:\n"
                    "- Builds sorted portion by inserting next element at correct position.\n"
                    "- Best: O(n) (already sorted). Average/Worst: O(n²). Space: O(1). Stable.\n")
        elif algo == "Quick Sort":
            text = ("Quick Sort:\n"
                    "- Picks pivot, partitions array into elements < pivot and > pivot, then recurses.\n"
                    "- Best/Average: O(n log n). Worst: O(n²) (bad pivots). Space: O(log n) average. Not stable.\n")
        elif algo == "Merge Sort":
            text = ("Merge Sort:\n"
                    "- Recursively divides and merges sorted halves.\n"
                    "- Best/Average/Worst: O(n log n). Space: O(n). Stable.\n")
        self.info_box.setPlainText(text)

    def show_execution_summary(self):
        algo = self.algo_combo.currentText()
        comps = self.comparisons
        swaps = self.swaps
        # time label already set
        best, avg, worst = "", "", ""
        reason_best, reason_avg, reason_worst = "", "", "",

        if algo == "Bubble Sort":
            best = "O(n) — already sorted; only single pass with no swaps."
            avg = worst = "O(n²) — nested passes over the array (many comparisons & swaps)."
            reason_best = "When array is sorted bubble detects no swaps and stops early (depending on implementation)."
            reason_avg = "Elements must move many positions requiring many swaps; compares adjacent pairs in nested loops."
        elif algo == "Selection Sort":
            best = avg = worst = "O(n²) — selection always searches min across remaining elements."
            reason_best = reason_avg = reason_worst = "Selection does full scans for minimum each iteration; swaps minimal but comparisons remain ~n²."
        elif algo == "Insertion Sort":
            best = "O(n) — already sorted, just linear pass."
            avg = worst = "O(n²) — many shifts when element needs to be moved left repeatedly."
            reason_best = "Each new element finds correct spot quickly if already sorted."
            reason_avg = "Needs shifting of elements to insert at correct place; cost grows quadratically."
        elif algo == "Quick Sort":
            best = "O(n log n) average — balanced partitions."
            avg = "O(n log n) — expected with random pivots."
            worst = "O(n²) — degenerate partitions (already sorted pivot selection)."
            reason_best = "Good pivots split array evenly leading to log n depth recursion."
            reason_avg = "Random pivot choices tend to split reasonably well."
            reason_worst = "Poor pivot choices produce highly unbalanced partitions making recursion depth O(n)."
        elif algo == "Merge Sort":
            best = avg = worst = "O(n log n) — divides and merges consistently."
            reason_best = reason_avg = reason_worst = "Always divides array in halves, merging cost O(n) at each level; depth log n."

        summary = f"Algorithm: {algo}\n\n"
        summary += f"Comparisons performed: {comps}\n"
        summary += f"Swaps/Assignments performed: {swaps}\n\n"
        summary += "Complexities:\n"
        if algo == "Bubble Sort":
            summary += f"- Best: {best}\n- Average: {avg}\n- Worst: {worst}\n"
        elif algo == "Selection Sort":
            summary += f"- Best/Average/Worst: {best}\n"
        elif algo == "Insertion Sort":
            summary += f"- Best: {best}\n- Average: {avg}\n- Worst: {worst}\n"
        elif algo == "Quick Sort":
            summary += f"- Best: {best}\n- Average: {avg}\n- Worst: {worst}\n"
        elif algo == "Merge Sort":
            summary += f"- Best/Average/Worst: {best}\n"
        summary += "\nWhy (short explanation):\n"
        if algo == "Bubble Sort":
            summary += reason_best + "\n" + reason_avg
        elif algo == "Selection Sort":
            summary += reason_best
        elif algo == "Insertion Sort":
            summary += reason_best + "\n" + reason_avg
        elif algo == "Quick Sort":
            summary += reason_best + "\n" + reason_worst
        elif algo == "Merge Sort":
            summary += reason_best

        self.summary_text.setPlainText(summary)

