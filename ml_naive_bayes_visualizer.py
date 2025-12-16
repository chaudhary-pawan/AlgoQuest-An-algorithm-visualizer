import sys
import math

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QSpinBox,
    QTextEdit, QProgressBar, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


# =========================================================
# NAIVE BAYES LOGIC (EDUCATIONAL DEMO)
# =========================================================
class NaiveBayesModel:
    def __init__(self):
        # Likelihoods (fixed demo probabilities)
        self.probs = {
            "free":     {"spam": 0.8, "ham": 0.1},
            "money":    {"spam": 0.7, "ham": 0.05},
            "meeting":  {"spam": 0.1, "ham": 0.8},
        }

    def compute(self, counts, prior_spam, laplace=False):
        prior_ham = 1 - prior_spam

        spam_score = prior_spam
        ham_score = prior_ham

        log = []
        log.append("Step 1: Prior Probabilities")
        log.append(f"P(Spam) = {prior_spam:.2f}")
        log.append(f"P(Ham) = {prior_ham:.2f}\n")

        log.append("Step 2: Likelihoods with word counts")

        for word, count in counts.items():
            if laplace:
                ps = (self.probs[word]["spam"] + 1) / 2
                ph = (self.probs[word]["ham"] + 1) / 2
            else:
                ps = self.probs[word]["spam"]
                ph = self.probs[word]["ham"]

            log.append(f"P({word}|Spam)^{count} = {ps}^{count}")
            log.append(f"P({word}|Ham)^{count} = {ph}^{count}")

            spam_score *= ps ** count
            ham_score *= ph ** count

        log.append("\nStep 3: Unnormalized Scores")
        log.append(f"Spam Score = {spam_score:.6e}")
        log.append(f"Ham Score = {ham_score:.6e}")

        total = spam_score + ham_score + 1e-12
        p_spam = spam_score / total
        p_ham = ham_score / total

        # UI realism clipping
        p_spam = min(max(p_spam, 0.001), 0.999)
        p_ham = 1 - p_spam

        log.append("\nStep 4: Normalization")
        log.append(f"P(Spam | Email) = {p_spam:.3f}")
        log.append(f"P(Ham | Email) = {p_ham:.3f}")

        return p_spam, p_ham, "\n".join(log)


# =========================================================
# UI
# =========================================================
class NaiveBayesVisualizer(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlgoQUEST – Naive Bayes (Spam / Ham)")
        self.resize(1400, 800)

        self.model = NaiveBayesModel()

        # ---------- STYLES ----------
        self.setStyleSheet("""
            QWidget {
                background:#0f2027;
                color:white;
                font-family:Segoe UI;
                font-size:16px;
            }
            QLabel { color:white; font-size:16px; }
            QPushButton {
                background:#1e2d37;
                color:white;
                padding:10px 18px;
                border:1px solid #80fac0;
                border-radius:8px;
                font-size:15px;
            }
            QPushButton:hover {
                background:#80fac0;
                color:black;
            }
            QTextEdit {
                background:#13232c;
                border:1px solid #80fac0;
                color:white;
                font-size:14px;
            }
            QProgressBar {
                border:1px solid #80fac0;
                border-radius:8px;
                text-align:center;
                height:26px;
                font-size:14px;
            }
            QProgressBar::chunk {
                background:#80fac0;
            }
            QSpinBox {
                font-size:15px;
                padding:4px;
            }
            QCheckBox {
                font-size:15px;
            }
        """)

        self.init_ui()

    # -----------------------------------------------------
    def init_ui(self):
        main = QVBoxLayout(self)

        # ---------- TITLE ----------
        title = QLabel("Naive Bayes – Email Spam / Ham Classifier")
        title.setFont(QFont("Segoe UI", 26, QFont.Bold))
        title.setStyleSheet("color:#80fac0;")
        main.addWidget(title)

        # ---------- TOP BAR ----------
        top = QHBoxLayout()
        compute = QPushButton("▶ Compute")
        reset = QPushButton("⟳ Reset")
        back = QPushButton("⬅ Back to ML Algorithms")

        compute.clicked.connect(self.compute)
        reset.clicked.connect(self.reset)
        back.clicked.connect(self.close)

        top.addWidget(compute)
        top.addWidget(reset)
        top.addStretch()
        top.addWidget(back)
        main.addLayout(top)

        # ---------- BODY ----------
        body = QHBoxLayout()

        # LEFT PANEL
        left = QVBoxLayout()

        left.addWidget(QLabel("Prior Probability"))

        self.prior_label = QLabel("P(Spam) = 0.50  |  P(Ham) = 0.50")
        self.prior_label.setFont(QFont("Segoe UI", 16))
        left.addWidget(self.prior_label)

        self.prior_slider = QSlider(Qt.Horizontal)
        self.prior_slider.setRange(1, 99)
        self.prior_slider.setValue(50)
        self.prior_slider.valueChanged.connect(self.update_prior)
        left.addWidget(self.prior_slider)

        left.addSpacing(20)
        left.addWidget(QLabel("Word Counts (0 – 10)"))

        self.spins = {}
        for word in ["free", "money", "meeting"]:
            lbl = QLabel(f'Word "{word}"')
            spin = QSpinBox()
            spin.setRange(0, 10)
            self.spins[word] = spin
            left.addWidget(lbl)
            left.addWidget(spin)

        self.laplace = QCheckBox("Enable Laplace Smoothing")
        left.addWidget(self.laplace)

        body.addLayout(left, 2)

        # RIGHT PANEL
        right = QVBoxLayout()

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        right.addWidget(self.log, 2)

        self.result_label = QLabel("Prediction Result")
        self.result_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("color:#80fac0;")
        right.addWidget(self.result_label)

        self.spam_bar = QProgressBar()
        self.spam_bar.setMaximum(100)
        right.addWidget(QLabel("P(Spam | Email)"))
        right.addWidget(self.spam_bar)

        self.ham_bar = QProgressBar()
        self.ham_bar.setMaximum(100)
        right.addWidget(QLabel("P(Ham | Email)"))
        right.addWidget(self.ham_bar)

        body.addLayout(right, 3)
        main.addLayout(body)

    # -----------------------------------------------------
    def update_prior(self):
        p = self.prior_slider.value() / 100
        self.prior_label.setText(f"P(Spam) = {p:.2f}  |  P(Ham) = {1-p:.2f}")

    # -----------------------------------------------------
    def compute(self):
        counts = {w: s.value() for w, s in self.spins.items()}
        prior = self.prior_slider.value() / 100

        p_spam, p_ham, log = self.model.compute(
            counts, prior, self.laplace.isChecked()
        )

        self.log.setText(log)

        self.spam_bar.setValue(int(p_spam * 100))
        self.ham_bar.setValue(int(p_ham * 100))

        if p_spam > p_ham:
            self.result_label.setText(f"📧 SPAM ({p_spam*100:.1f}% confidence)")
        else:
            self.result_label.setText(f"📩 HAM ({p_ham*100:.1f}% confidence)")

    # -----------------------------------------------------
    def reset(self):
        self.prior_slider.setValue(50)
        for s in self.spins.values():
            s.setValue(0)
        self.log.clear()
        self.spam_bar.setValue(0)
        self.ham_bar.setValue(0)
        self.result_label.setText("Prediction Result")


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = NaiveBayesVisualizer()
    w.show()
    sys.exit(app.exec_())
