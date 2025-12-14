import sys
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QSlider,
    QGraphicsView, QGraphicsScene, QFrame, QGraphicsDropShadowEffect, QSizePolicy,
    QTextEdit, QLineEdit, QScrollArea, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QPainter, QLinearGradient

class SortingVisualizer(QWidget):
    backToHomeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sorting Visualizer - AlgoQUEST")
        self.resize(1300, 850)
        
        # Internal State
        self.data = []
        self.steps = []
        self.step_index = 0
        self.comparisons = 0
        self.swaps = 0
        
        # Colors (Neon Palette)
        self.col_bar_default = QColor(80, 250, 220)       # Neon Cyan
        self.col_bar_highlight = QColor(255, 215, 0)      # Gold (Compare)
        self.col_bar_swap = QColor(255, 80, 80)           # Neon Red (Swap)
        self.col_bar_sorted = QColor(100, 255, 100)       # Neon Green (Done)
        
        self.initUI()
        self.parse_input_data() # Load initial data

    def paintEvent(self, event):
        """Draw the Cyber Grid Background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Deep Ocean Gradient
        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0.0, QColor(15, 32, 39))  
        gradient.setColorAt(0.5, QColor(20, 40, 50))  
        gradient.setColorAt(1.0, QColor(30, 60, 70)) 
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

        # Matrix Dots
        dot_pen = QPen(QColor(80, 250, 220, 20)) 
        dot_pen.setWidth(2)
        painter.setPen(dot_pen)
        grid_spacing = 40
        for x in range(0, w, grid_spacing):
            for y in range(0, h, grid_spacing):
                painter.drawPoint(x, y)

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ==========================================
        # 1. TOP CONTROL DECK
        # ==========================================
        control_deck = QFrame()
        control_deck.setFixedHeight(80)
        control_deck.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 45, 55, 200);
                border-radius: 12px;
                border: 1px solid rgba(80, 250, 220, 50);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        control_deck.setGraphicsEffect(shadow)

        deck_layout = QHBoxLayout(control_deck)
        deck_layout.setContentsMargins(15, 10, 15, 10)
        deck_layout.setSpacing(15)

        # Back Button
        self.back_btn = QPushButton("← Back")
        self.back_btn.setFixedSize(90, 35)
        self.style_button(self.back_btn, is_secondary=True)
        self.back_btn.clicked.connect(self.go_back)
        deck_layout.addWidget(self.back_btn)

        # Algorithm Combo
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["Bubble Sort", "Selection Sort", "Insertion Sort", "Quick Sort", "Merge Sort"])
        self.algo_combo.setFixedSize(160, 35)
        self.style_combo(self.algo_combo)
        self.algo_combo.currentTextChanged.connect(self.update_info_panel)
        deck_layout.addWidget(self.algo_combo)

        # Custom Input Field
        lbl_input = QLabel("Input (comma separated):")
        lbl_input.setStyleSheet("color: #aabdc9; font-weight: bold; background: transparent; border: none;")
        deck_layout.addWidget(lbl_input)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("e.g. 50, 10, 25, 5")
        self.input_field.setText("45, 12, 88, 32, 56, 7, 23, 90, 15, 67, 34") # Default
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(20, 30, 40, 200);
                color: #ffffff;
                border: 1px solid #57606f;
                border-radius: 8px;
                padding: 5px;
                font-family: 'Consolas';
            }
        """)
        self.input_field.textChanged.connect(self.parse_input_data)
        deck_layout.addWidget(self.input_field, stretch=1)

        # Speed Slider
        lbl_speed = QLabel("Speed:")
        lbl_speed.setStyleSheet("color: #aabdc9; font-weight: bold; background: transparent; border: none;")
        deck_layout.addWidget(lbl_speed)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(50)
        self.speed_slider.setFixedWidth(120)
        self.style_slider(self.speed_slider)
        # Update timer interval dynamically without resetting
        self.speed_slider.valueChanged.connect(self.update_speed)
        deck_layout.addWidget(self.speed_slider)

        # Start/Reset Buttons
        self.reset_btn = QPushButton("Reset")
        self.style_button(self.reset_btn, is_secondary=True)
        self.reset_btn.clicked.connect(self.reset_viz)
        deck_layout.addWidget(self.reset_btn)

        self.start_btn = QPushButton("Start Sorting")
        self.style_button(self.start_btn, is_main=True)
        self.start_btn.clicked.connect(self.start_sorting)
        deck_layout.addWidget(self.start_btn)

        main_layout.addWidget(control_deck)

        # ==========================================
        # 2. VISUALIZATION AREA (Middle)
        # ==========================================
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        main_layout.addWidget(self.view, stretch=4)

        # ==========================================
        # 3. DETAILED INFO PANEL (Bottom - Scrollable)
        # ==========================================
        # Using a ScrollArea to allow extensive content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(300) # Fixed height for bottom panel
        scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #1e272e; width: 10px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #80fac0; min-height: 20px; border-radius: 5px;
            }
        """)

        # Container inside ScrollArea
        self.info_container = QWidget()
        self.info_container.setStyleSheet("background-color: rgba(20, 30, 40, 180); border-radius: 10px;")
        info_layout = QVBoxLayout(self.info_container)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(20)

        # --- Section A: Live Metrics (Top of Info) ---
        metrics_layout = QHBoxLayout()
        self.lbl_comps = QLabel("Comparisons: 0")
        self.lbl_swaps = QLabel("Swaps: 0")
        self.lbl_status = QLabel("Status: Idle")
        
        for lbl in [self.lbl_comps, self.lbl_swaps, self.lbl_status]:
            lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
            lbl.setStyleSheet("color: #80fac0; background: transparent;")
            metrics_layout.addWidget(lbl)
        metrics_layout.addStretch()
        info_layout.addLayout(metrics_layout)

        # Line Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #57606f;")
        info_layout.addWidget(line)

        # --- Section B: Theory & Code (Split horizontally) ---
        content_splitter = QHBoxLayout()

        # Left: Theory
        self.theory_box = QTextEdit()
        self.theory_box.setReadOnly(True)
        self.theory_box.setStyleSheet("""
            background: transparent; border: none; color: #d0e6f0; font-family: 'Segoe UI'; font-size: 14px;
        """)
        self.theory_box.setMaximumHeight(200)
        content_splitter.addWidget(self.theory_box, stretch=1)

        # Right: Pseudo Code
        self.code_box = QTextEdit()
        self.code_box.setReadOnly(True)
        self.code_box.setStyleSheet("""
            background-color: #1e1e1e; 
            border: 1px solid #333; 
            border-radius: 5px;
            color: #dcdde1; 
            font-family: 'Consolas'; 
            font-size: 13px;
            padding: 10px;
        """)
        self.code_box.setMaximumHeight(200)
        content_splitter.addWidget(self.code_box, stretch=1)

        info_layout.addLayout(content_splitter)
        
        scroll_area.setWidget(self.info_container)
        main_layout.addWidget(scroll_area, stretch=2)

        self.setLayout(main_layout)

        # Timer setup
        self.timer = QTimer()
        self.timer.timeout.connect(self.play_step)
        
        # Initialize Info
        self.update_info_panel()

    # ==================== DATA HANDLING ====================
    def parse_input_data(self):
        """Reads input field, cleans data, and updates bar chart immediately."""
        if self.timer.isActive(): return # Don't update while running

        text = self.input_field.text()
        try:
            # Split by comma, strip spaces, convert to int
            self.data = [int(x.strip()) for x in text.split(',') if x.strip().isdigit()]
        except ValueError:
            self.data = [] # Invalid input

        # Reset state
        self.steps = []
        self.step_index = 0
        self.comparisons = 0
        self.swaps = 0
        self.lbl_comps.setText("Comparisons: 0")
        self.lbl_swaps.setText("Swaps: 0")
        self.lbl_status.setText("Status: Ready")
        
        self.draw_bars()

    def update_speed(self):
        """Updates timer interval on the fly."""
        if self.timer.isActive():
            interval = max(1, 101 - self.speed_slider.value()) * 2
            self.timer.setInterval(interval)

    def reset_viz(self):
        self.timer.stop()
        self.parse_input_data()
        self.start_btn.setEnabled(True)
        self.input_field.setEnabled(True)

    def draw_bars(self, highlight=None, sorted_indices=None):
        if highlight is None: highlight = []
        if sorted_indices is None: sorted_indices = []
        
        self.scene.clear()
        n = len(self.data)
        if n == 0: return

        # Dimensions
        view_w = self.view.width() - 20 
        view_h = self.view.height() - 20
        # Calculate width dynamically based on count
        bar_w = min(50, max(5, view_w / n)) 
        spacing = 2
        total_w = n * (bar_w + spacing)
        start_x = (view_w - total_w) / 2 # Center the graph

        max_val = max(self.data) if self.data else 1
        
        for i, val in enumerate(self.data):
            h = (val / max_val) * (view_h * 0.9) 
            x = start_x + i * (bar_w + spacing)
            y = view_h - h
            
            # Color Logic
            color = self.col_bar_default
            if i in sorted_indices:
                color = self.col_bar_sorted
            elif i in highlight:
                color = self.col_bar_swap 
            
            # Draw Bar
            rect = self.scene.addRect(x, y, bar_w, h)
            rect.setPen(QPen(Qt.NoPen))
            rect.setBrush(QBrush(color))
            
            # Text (only if bars are wide enough)
            if bar_w > 20:
                text = self.scene.addText(str(val))
                text.setDefaultTextColor(QColor("white"))
                font = QFont("Segoe UI", 8)
                text.setFont(font)
                # Center text
                txt_w = text.boundingRect().width()
                text.setPos(x + (bar_w - txt_w)/2, y - 20)

    # ==================== SORTING EXECUTION ====================
    def start_sorting(self):
        if self.timer.isActive(): return
        if not self.data: return
        
        # Lock Input
        self.input_field.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.lbl_status.setText("Status: Sorting...")

        algo = self.algo_combo.currentText()
        arr_copy = self.data.copy()
        
        # Generate Steps
        if algo == "Bubble Sort": self.steps = self._bubble_steps(arr_copy)
        elif algo == "Selection Sort": self.steps = self._selection_steps(arr_copy)
        elif algo == "Insertion Sort": self.steps = self._insertion_steps(arr_copy)
        elif algo == "Quick Sort": self.steps = self._quick_steps(arr_copy)
        elif algo == "Merge Sort": self.steps = self._merge_steps(arr_copy)

        self.step_index = 0
        interval = max(1, 101 - self.speed_slider.value()) * 2
        self.timer.start(interval)

    def play_step(self):
        if self.step_index >= len(self.steps):
            self.timer.stop()
            self.lbl_status.setText("Status: Completed")
            self.draw_bars(sorted_indices=list(range(len(self.data)))) # All Green
            self.show_final_analysis()
            return

        # Unpack Step
        arr_state, highlight, comps, swaps = self.steps[self.step_index]
        self.data = arr_state
        self.comparisons = comps
        self.swaps = swaps
        
        # Update UI
        self.lbl_comps.setText(f"Comparisons: {comps}")
        self.lbl_swaps.setText(f"Swaps: {swaps}")
        
        self.draw_bars(highlight)
        self.step_index += 1

    def show_final_analysis(self):
        # Calculate complexity based on N and Comparisons
        n = len(self.data)
        comps = self.comparisons
        algo = self.algo_combo.currentText()
        
        analysis = f"\n[FINAL ANALYSIS]\nArray Size (N): {n}\nTotal Comparisons: {comps}\n"
        
        if algo == "Bubble Sort":
            if comps <= n: analysis += "Result: Best Case (O(n)) - Array was nearly sorted."
            else: analysis += "Result: Average/Worst Case (O(n²))"
        elif algo in ["Selection Sort", "Insertion Sort"]:
             analysis += "Result: Quadratic Time (O(n²)) behavior observed."
        else:
             analysis += "Result: Log-Linear Time (O(n log n)) efficient behavior."
             
        # Append to Theory Box
        current_text = self.theory_box.toPlainText()
        self.theory_box.setPlainText(current_text + "\n" + analysis)
        # Scroll to bottom
        sb = self.theory_box.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ==================== CONTENT MANAGER ====================
    def update_info_panel(self):
        algo = self.algo_combo.currentText()
        
        # Theory Content
        theory = {
            "Bubble Sort": "<b>Bubble Sort</b><br>Repeatedly steps through the list, compares adjacent elements and swaps them if they are in the wrong order.<br><br><b>Complexity:</b><br>• Best: O(n)<br>• Average: O(n²)<br>• Worst: O(n²)<br>• Space: O(1)",
            "Selection Sort": "<b>Selection Sort</b><br>Divides the input list into two parts: a sorted sublist and an unsorted sublist. Repeatedly selects the smallest element from unsorted part.<br><br><b>Complexity:</b><br>• Time: O(n²) (Always)<br>• Space: O(1)",
            "Insertion Sort": "<b>Insertion Sort</b><br>Builds the final sorted array one item at a time. Efficient for small data sets or nearly sorted data.<br><br><b>Complexity:</b><br>• Best: O(n)<br>• Worst: O(n²)<br>• Space: O(1)",
            "Quick Sort": "<b>Quick Sort</b><br>Divide and Conquer. Picks a 'pivot' and partitions the array into elements less than pivot and greater than pivot.<br><br><b>Complexity:</b><br>• Best/Avg: O(n log n)<br>• Worst: O(n²)<br>• Space: O(log n)",
            "Merge Sort": "<b>Merge Sort</b><br>Divide and Conquer. Recursively divides array into halves, sorts them, and then merges them back.<br><br><b>Complexity:</b><br>• Time: O(n log n) (Always)<br>• Space: O(n)"
        }

        # Pseudo Code
        codes = {
            "Bubble Sort": "procedure bubbleSort(A: list of items)\n  n = length(A)\n  repeat\n    swapped = false\n    for i = 1 to n-1 inclusive do\n      if A[i-1] > A[i] then\n        swap(A[i-1], A[i])\n        swapped = true\n      end if\n    end for\n  until not swapped\nend procedure",
            "Selection Sort": "procedure selectionSort(A)\n  for i = 0 to n - 2 do\n    min_idx = i\n    for j = i + 1 to n - 1 do\n      if A[j] < A[min_idx] then\n        min_idx = j\n      end if\n    end for\n    swap(A[i], A[min_idx])\n  end for\nend procedure",
            "Insertion Sort": "procedure insertionSort(A)\n  for i = 1 to n - 1 do\n    key = A[i]\n    j = i - 1\n    while j >= 0 and A[j] > key do\n      A[j + 1] = A[j]\n      j = j - 1\n    end while\n    A[j + 1] = key\n  end for\nend procedure",
            "Quick Sort": "procedure quickSort(A, low, high)\n  if low < high then\n    p = partition(A, low, high)\n    quickSort(A, low, p - 1)\n    quickSort(A, p + 1, high)\n  end if\nend procedure",
            "Merge Sort": "procedure mergeSort(A)\n  if length(A) <= 1 return A\n  mid = length(A) / 2\n  left = mergeSort(A[0..mid])\n  right = mergeSort(A[mid..end])\n  return merge(left, right)\nend procedure"
        }

        self.theory_box.setHtml(theory.get(algo, ""))
        self.code_box.setPlainText(codes.get(algo, ""))

    # ==================== ALGORITHMS (Generators) ====================
    # Each returns a list of tuples: (array_state, highlight_indices, comparisons, swaps)
    
    def _bubble_steps(self, arr):
        steps = []
        comps, swaps = 0, 0
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                comps += 1
                steps.append((arr.copy(), [j, j+1], comps, swaps))
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swaps += 1
                    steps.append((arr.copy(), [j, j+1], comps, swaps))
        return steps

    def _selection_steps(self, arr):
        steps = []
        comps, swaps = 0, 0
        n = len(arr)
        for i in range(n):
            min_idx = i
            for j in range(i + 1, n):
                comps += 1
                steps.append((arr.copy(), [min_idx, j], comps, swaps))
                if arr[j] < arr[min_idx]:
                    min_idx = j
            if min_idx != i:
                arr[i], arr[min_idx] = arr[min_idx], arr[i]
                swaps += 1
                steps.append((arr.copy(), [i, min_idx], comps, swaps))
        return steps

    def _insertion_steps(self, arr):
        steps = []
        comps, swaps = 0, 0
        n = len(arr)
        for i in range(1, n):
            key = arr[i]
            j = i - 1
            steps.append((arr.copy(), [i], comps, swaps))
            while j >= 0:
                comps += 1
                if arr[j] > key:
                    arr[j + 1] = arr[j]
                    swaps += 1
                    steps.append((arr.copy(), [j, j+1], comps, swaps))
                    j -= 1
                else:
                    break
            arr[j + 1] = key
            steps.append((arr.copy(), [j+1], comps, swaps))
        return steps

    def _quick_steps(self, arr):
        steps = []
        comps, swaps = 0, 0
        def partition(a, low, high):
            nonlocal comps, swaps
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
                pi = partition(a, low, high)
                quicksort(a, low, pi - 1)
                quicksort(a, pi + 1, high)
        
        quicksort(arr, 0, len(arr) - 1)
        return steps

    def _merge_steps(self, arr):
        steps = []
        comps, swaps = 0, 0
        def merge(a, l, m, r):
            nonlocal comps, swaps
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
                else:
                    a[k] = R[j]
                    j += 1
                swaps += 1 # Assignment
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
        return steps

    # ==================== HELPERS ====================
    def style_button(self, btn, is_main=False, is_secondary=False):
        base_style = """
            QPushButton { font-family: 'Segoe UI'; font-weight: bold; font-size: 13px; border-radius: 8px; padding: 5px; }
        """
        if is_main:
            btn.setStyleSheet(base_style + """
                QPushButton { background-color: #80fac0; color: #1a1a1a; border: none; }
                QPushButton:hover { background-color: #a0fcd0; }
                QPushButton:pressed { background-color: #60daa0; }
            """)
        elif is_secondary:
             btn.setStyleSheet(base_style + """
                QPushButton { background-color: rgba(255, 255, 255, 10); color: #80fac0; border: 1px solid #80fac0; }
                QPushButton:hover { background-color: rgba(80, 250, 220, 20); }
            """)

    def style_combo(self, combo):
        combo.setStyleSheet("""
            QComboBox { background-color: rgba(20, 30, 40, 200); color: #ffffff; border: 1px solid #57606f; border-radius: 8px; padding-left: 10px; font-family: 'Segoe UI'; }
            QComboBox QAbstractItemView { background-color: #2f3640; color: white; selection-background-color: #80fac0; selection-color: black; }
        """)

    def style_slider(self, slider):
        slider.setStyleSheet("""
            QSlider::groove:horizontal { border: 1px solid #3d3d3d; height: 6px; background: #202020; border-radius: 3px; }
            QSlider::handle:horizontal { background: #80fac0; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
        """)

    def go_back(self):
        self.timer.stop()
        self.backToHomeSignal.emit()
        self.close()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = SortingVisualizer()
    window.show()
    sys.exit(app.exec_())