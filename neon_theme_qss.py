# neon_theme_qss.py
NEON_QSS = r"""
/* App background */
QWidget {
    background: qlineargradient(x1:0 y1:0, x2:1 y2:1,
        stop:0 #0f1114, stop:1 #0b0c0e);
    color: #e6eef6;
    font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial;
}

/* Glass panel */
QFrame#panel {
    background: rgba(20,24,30,220); /* semi transparent dark */
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.03);
    box-shadow: 0 6px 30px rgba(0,0,0,0.6);
}

/* Neon card header */
QLabel#panelTitle {
    color: #ffd400;
    font-weight: 700;
    font-size: 20px;
}

/* Neon buttons (main) */
QPushButton.neon {
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(10,120,255,0.12), stop:1 rgba(120,10,255,0.12));
    color: #dff4ff;
    border-radius: 10px;
    padding: 10px 18px;
    border: 1px solid rgba(255,255,255,0.06);
    font-weight: 600;
    min-height: 36px;
    min-width: 160px;
}
QPushButton.neon:hover {
    border: 1px solid rgba(80,200,255,0.35);
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(30,150,255,0.16), stop:1 rgba(150,30,255,0.16));
    box-shadow: 0 0 18px rgba(30,150,255,0.12), inset 0 1px 0 rgba(255,255,255,0.02);
}
QPushButton.neon:pressed {
    transform: translateY(1px);
}

/* Small control buttons */
QPushButton.small {
    background: rgba(255,255,255,0.02);
    color: #cfeeff;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.03);
    padding: 6px 12px;
}
QPushButton.small:hover {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(100,180,255,0.12);
}

/* Titles & subtitles */
QLabel.title {
    font-size: 28px;
    color: #ffd400;
    font-weight: 800;
}
QLabel.subtitle {
    font-size: 14px;
    color: #9fb6c9;
}

/* Left control items */
QGroupBox {
    border: none;
    margin-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px;
    color: #a0b3c7;
}

/* Matplotlib canvas background correction (QWidget) */
QWidget#canvasContainer {
    background: transparent;
}

/* Thin separators */
QFrame.separator {
    background: rgba(255,255,255,0.03);
    min-height: 1px;
}

/* small text areas */
QLabel.info {
    color: #cde7ff;
    font-size: 12px;
}

/* Scrollbar (subtle) */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,0.06);
    border-radius: 4px;
}
"""
