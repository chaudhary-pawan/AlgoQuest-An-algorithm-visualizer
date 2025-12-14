import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QFrame, 
    QHBoxLayout, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt5.QtGui import (
    QFont, QPainter, QColor, QBrush, QPen, 
    QLinearGradient, QPainterPath, QRadialGradient
)

# ==========================================
# SAFETY IMPORT BLOCK
# ==========================================
try:
    from sorting_visualizer import SortingVisualizer
    from search_visualizer import SearchingVisualizer
    from graph_visualizer import GraphVisualizer
    from dp_visualizer import DPVisualizer
    from ml_visualizer import MLVisualizer
    IMPORTS_SUCCESS = True
except ImportError:
    class Placeholder(QWidget):
        backToHomeSignal = pyqtSignal()
        def __init__(self, name="Visualizer"):
            super().__init__()
            self.setWindowTitle(name)
            self.resize(600, 400)
            layout = QVBoxLayout(self)
            label = QLabel(f"{name} Module\n(File not found)", self)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: white; font-size: 20px;")
            layout.addWidget(label)
            self.setStyleSheet("background-color: #1a1a1a;")

    SortingVisualizer = lambda: Placeholder("Sorting")
    SearchingVisualizer = lambda: Placeholder("Searching")
    GraphVisualizer = lambda: Placeholder("Graphs")
    DPVisualizer = lambda: Placeholder("Dynamic Programming")
    MLVisualizer = lambda: Placeholder("Machine Learning")

# ==========================================
# 1. ADVANCED ICON WIDGET (Redesigned)
# ==========================================
class IconWidget(QWidget):
    def __init__(self, module_type, parent=None):
        super().__init__(parent)
        self.module_type = module_type
        self.setFixedSize(64, 64) 
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 1. Icon Container Background
        p.setBrush(QBrush(QColor(30, 45, 55)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, 64, 64, 16, 16)

        # 2. Setup Pens
        main_color = QColor(80, 250, 220)
        glow_color = QColor(80, 250, 220, 60)
        
        pen_outline = QPen(main_color, 2.5)
        pen_outline.setCapStyle(Qt.RoundCap)
        pen_outline.setJoinStyle(Qt.RoundJoin)
        
        pen_glow = QPen(glow_color, 6)
        pen_glow.setCapStyle(Qt.RoundCap)

        # --- DRAWING LOGIC ---
        
        if self.module_type == "sorting":
            # Ascending Bar Chart with Arrow
            bars = [(18, 44, 8, 14), (29, 44, 8, 24), (40, 44, 8, 34)]
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(main_color))
            for (x, bottom_y, w, h) in bars:
                rect = QRectF(x, bottom_y - h, w, h)
                p.drawRoundedRect(rect, 2, 2)
            
            p.setPen(pen_outline)
            p.setBrush(Qt.NoBrush)
            path = QPainterPath()
            path.moveTo(14, 20)
            path.cubicTo(20, 10, 45, 10, 50, 20)
            p.drawPath(path)

        elif self.module_type == "search":
            # Magnifying Glass
            p.setPen(pen_outline)
            p.drawLine(38, 38, 48, 48)
            lens_rect = QRectF(16, 16, 24, 24)
            p.setBrush(QBrush(QColor(80, 250, 220, 30))) 
            p.drawEllipse(lens_rect)
            p.setBrush(QBrush(main_color))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(28, 28), 3, 3)

        elif self.module_type == "graph":
            # NEW DESIGN: Central Hub & Spoke Network
            center = QPointF(32, 32)
            # Surrounding nodes
            nodes = [
                QPointF(32, 14),  # Top
                QPointF(14, 42),  # Bottom Left
                QPointF(50, 42)   # Bottom Right
            ]
            
            # Draw Connections (Center to all, and outer ring)
            p.setPen(pen_glow)
            for node in nodes:
                p.drawLine(center, node)
            p.drawLine(nodes[0], nodes[1])
            p.drawLine(nodes[1], nodes[2])
            p.drawLine(nodes[2], nodes[0])

            p.setPen(pen_outline)
            for node in nodes:
                p.drawLine(center, node)
            p.drawLine(nodes[0], nodes[1])
            p.drawLine(nodes[1], nodes[2])
            p.drawLine(nodes[2], nodes[0])

            # Draw Nodes (Center node slightly bigger)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(main_color))
            p.drawEllipse(center, 4, 4)
            for node in nodes:
                p.drawEllipse(node, 3, 3)

        elif self.module_type == "dp":
            # 3x3 Grid with Diagonal Highlight
            p.setPen(pen_outline)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(16, 16, 32, 32, 4, 4)
            
            p.setPen(QPen(main_color, 1.5))
            p.drawLine(16, 26, 48, 26) 
            p.drawLine(16, 37, 48, 37) 
            p.drawLine(26, 16, 26, 48) 
            p.drawLine(37, 16, 37, 48) 
            
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(main_color))
            p.drawRect(19, 19, 5, 5)
            p.drawRect(29, 29, 5, 5)
            p.drawRect(40, 40, 5, 5)

        elif self.module_type == "ml":
            # NEW DESIGN: Dense Neural Network (3 Layers)
            p.setBrush(QBrush(main_color))
            p.setPen(pen_outline)
            
            # Layer coordinates (More symmetric)
            input_layer = [QPointF(14, 20), QPointF(14, 32), QPointF(14, 44)]
            hidden_layer = [QPointF(32, 15), QPointF(32, 27), QPointF(32, 39), QPointF(32, 51)]
            output_layer = [QPointF(50, 26), QPointF(50, 38)]
            
            # Draw Connections (Thin lines for complexity)
            p.setPen(QPen(QColor(80, 250, 220, 100), 1))
            
            # Connect Input -> Hidden
            for inp in input_layer:
                for hid in hidden_layer:
                    p.drawLine(inp, hid)
            
            # Connect Hidden -> Output
            for hid in hidden_layer:
                for out in output_layer:
                    p.drawLine(hid, out)
            
            # Draw Nodes
            p.setPen(Qt.NoPen)
            # Input Nodes
            for pt in input_layer: p.drawEllipse(pt, 3, 3)
            # Hidden Nodes
            for pt in hidden_layer: p.drawEllipse(pt, 3, 3)
            # Output Nodes
            for pt in output_layer: p.drawEllipse(pt, 4, 4)

        p.end()

# ==========================================
# 2. CARD WIDGET (Wider for Long Text)
# ==========================================
class CardWidget(QFrame):
    clicked = pyqtSignal()

    def __init__(self, module_type, title):
        super().__init__()
        self.module_type = module_type
        # INCREASED WIDTH: 360 -> 400 (Fixes "Dynamic Programming" cutoff)
        self.setFixedSize(400, 130)
        self.setCursor(Qt.PointingHandCursor)
        
        self.default_style = """
            QFrame {
                background-color: rgba(30, 40, 50, 200); 
                border-radius: 20px;
                border: 1px solid rgba(80, 250, 220, 40);
            }
        """
        self.hover_style = """
            QFrame {
                background-color: rgba(45, 60, 75, 230);
                border-radius: 20px;
                border: 1px solid rgba(80, 250, 220, 255); 
            }
        """
        self.setStyleSheet(self.default_style)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(8)
        self.shadow.setColor(QColor(0, 0, 0, 90)) 
        self.setGraphicsEffect(self.shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(25)

        icon = IconWidget(module_type)
        layout.addWidget(icon)

        label = QLabel(title)
        label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        label.setStyleSheet("border: none; color: #f0f0f0; background: transparent;") 
        label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        layout.addWidget(label, 1)

    def enterEvent(self, event):
        self.shadow.setBlurRadius(35)
        self.shadow.setYOffset(10)
        self.setStyleSheet(self.hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.shadow.setBlurRadius(25)
        self.shadow.setYOffset(8)
        self.setStyleSheet(self.default_style)
        super().leaveEvent(event)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()

# ==========================================
# 3. MAIN WINDOW
# ==========================================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlgoQUEST - Algorithm Visualizer Hub")
        self.resize(1200, 800)
        
        self.generate_background_data()
        self.init_ui()

    def generate_background_data(self):
        self.graph_points = []
        points_count = 15
        for i in range(points_count + 1):
            y_factor = random.uniform(0.3, 0.7) 
            self.graph_points.append(y_factor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()

        # Gradient
        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0.0, QColor(15, 32, 39))  
        gradient.setColorAt(0.5, QColor(28, 50, 60))  
        gradient.setColorAt(1.0, QColor(44, 83, 100)) 
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

        # Matrix Dots
        dot_pen = QPen(QColor(80, 250, 220, 30)) 
        dot_pen.setWidth(2)
        painter.setPen(dot_pen)
        grid_spacing = 40
        for x in range(0, w, grid_spacing):
            for y in range(0, h, grid_spacing):
                painter.drawPoint(x, y)

        # Background Bars
        painter.setBrush(QBrush(QColor(255, 255, 255, 8)))
        painter.setPen(Qt.NoPen)
        bar_width = 30
        gap = 50
        num_bars = w // gap
        random_gen = random.Random(42) 
        for i in range(num_bars + 1):
            x = i * gap
            bar_h = random_gen.randint(50, int(h * 0.4))
            painter.drawRect(x, h - bar_h, bar_width, bar_h)

        # Glowing Line
        if len(self.graph_points) > 1:
            path = QPainterPath()
            x_step = w / (len(self.graph_points) - 1)
            start_y = self.graph_points[0] * h
            path.moveTo(0, start_y)
            
            for i in range(1, len(self.graph_points)):
                prev_x = (i - 1) * x_step
                prev_y = self.graph_points[i-1] * h
                curr_x = i * x_step
                curr_y = self.graph_points[i] * h
                c1_x = prev_x + x_step * 0.5
                c2_x = curr_x - x_step * 0.5
                path.cubicTo(c1_x, prev_y, c2_x, curr_y, curr_x, curr_y)

            glow_pen = QPen(QColor(80, 250, 220, 40), 6)
            glow_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
            
            core_pen = QPen(QColor(80, 250, 220, 200), 2)
            painter.setPen(core_pen)
            painter.drawPath(path)

    def init_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(50, 40, 50, 40)
        main.setSpacing(25)

        # Title
        title = QLabel()
        title.setText("<span style='color:#ffffff;'>Algo</span><span style='color:#80fac0;'>QUEST</span>")
        title.setFont(QFont("Segoe UI", 52, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0,0,0, 150))
        title.setGraphicsEffect(shadow)
        main.addWidget(title)

        subtitle = QLabel("Explore · Visualize · Understand")
        subtitle.setFont(QFont("Segoe UI", 16))
        subtitle.setStyleSheet("color: #d0e6f0;") 
        subtitle.setAlignment(Qt.AlignCenter)
        main.addWidget(subtitle)

        main.addSpacing(160) 

        # Cards
        cards = {
            "sorting": CardWidget("sorting", "Sorting Visualizer"),
            "search": CardWidget("search", "Searching Visualizer"),
            "graph": CardWidget("graph", "Graph Visualizer"),
            "dp": CardWidget("dp", "Dynamic Programming"),
            "ml": CardWidget("ml", "Machine Learning"),
        }

        cards["sorting"].clicked.connect(self.open_sorting)
        cards["search"].clicked.connect(self.open_search)
        cards["graph"].clicked.connect(self.open_graph)
        cards["dp"].clicked.connect(self.open_dp)
        cards["ml"].clicked.connect(self.open_ml)

        # Layout
        row1 = QHBoxLayout()
        row1.addStretch()
        row1.addWidget(cards["sorting"])
        row1.addSpacing(40)
        row1.addWidget(cards["search"])
        row1.addSpacing(40) 
        row1.addWidget(cards["graph"])
        row1.addStretch()

        row2 = QHBoxLayout()
        row2.addStretch()
        row2.addWidget(cards["dp"])
        row2.addSpacing(40)
        row2.addWidget(cards["ml"])
        row2.addStretch()

        main.addLayout(row1)
        main.addSpacing(35) 
        main.addLayout(row2)

        main.addStretch()

        footer = QLabel("Built by Praveen — AlgoQUEST")
        footer.setFont(QFont("Segoe UI", 11))
        footer.setStyleSheet("color: #8daab9;")
        footer.setAlignment(Qt.AlignCenter)
        main.addWidget(footer)

    def _open_module(self, VisualizerClass):
        self.hide()
        self.w = VisualizerClass() 
        if hasattr(self.w, 'backToHomeSignal'):
            self.w.backToHomeSignal.connect(self.show)
        else:
            self.w.closeEvent = lambda e: self.show()
        self.w.show()

    def open_sorting(self): self._open_module(SortingVisualizer)
    def open_search(self): self._open_module(SearchingVisualizer)
    def open_graph(self): self._open_module(GraphVisualizer)
    def open_dp(self): self._open_module(DPVisualizer)
    def open_ml(self): self._open_module(MLVisualizer)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())