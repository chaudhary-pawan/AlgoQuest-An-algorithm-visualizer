import sys
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QSlider, QTextEdit,
    QProgressBar, QFrame, QApplication, QComboBox,
    QTableWidget, QTableWidgetItem, QTabWidget, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class NaiveBayesVisualizer(QWidget):
    backToMLSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlgoQUEST – Naive Bayes Classifier")
        self.resize(1500, 850)

        self.init_datasets()
        self.init_ui()

    # ==================================================
    # DATA
    # ==================================================
    def init_datasets(self):
        self.email_prob = {
            "spam": {"free": 0.8, "money": 0.7, "meeting": 0.1},
            "ham":  {"free": 0.2, "money": 0.1, "meeting": 0.6}
        }

        self.tennis_df = pd.DataFrame([
            ["Sunny","Hot","High","Weak","No"],
            ["Sunny","Hot","High","Strong","No"],
            ["Overcast","Hot","High","Weak","Yes"],
            ["Rainy","Mild","High","Weak","Yes"],
            ["Rainy","Cool","Normal","Weak","Yes"],
            ["Rainy","Cool","Normal","Strong","No"],
            ["Overcast","Cool","Normal","Strong","Yes"],
            ["Sunny","Mild","High","Weak","No"],
            ["Sunny","Cool","Normal","Weak","Yes"],
            ["Rainy","Mild","Normal","Weak","Yes"],
            ["Sunny","Mild","Normal","Strong","Yes"],
            ["Overcast","Mild","High","Strong","Yes"],
            ["Overcast","Hot","Normal","Weak","Yes"],
            ["Rainy","Mild","High","Strong","No"],
        ], columns=["Outlook","Temperature","Humidity","Wind","Play"])

    # ==================================================
    # UI
    # ==================================================
    def init_ui(self):
        self.setStyleSheet("""
        QWidget { background:#0f2027; color:white; font-family:Segoe UI; }
        QLabel { color:white; }
        QPushButton {
            background:#1e2d37; padding:8px 14px;
            border:1px solid #80fac0; border-radius:6px;
        }
        QPushButton:hover { background:#80fac0; color:black; }
        QTextEdit, QSpinBox, QComboBox {
            background:#13232c; border:1px solid #80fac0;
            padding:6px; color:white;
        }
        QProgressBar {
            border:1px solid #80fac0;
            background:#13232c;
            height:18px;
            color:black;
            font-weight:bold;
            text-align:center;
        }
        QProgressBar::chunk { background:#80fac0; }
        """)

        main = QVBoxLayout(self)

        top = QHBoxLayout()
        title = QLabel("Naive Bayes – Interactive Classifier")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color:#80fac0;")
        top.addWidget(title)
        top.addStretch()

        back = QPushButton("⬅ Back to ML Algorithms")
        back.clicked.connect(self.backToMLSignal.emit)
        top.addWidget(back)

        main.addLayout(top)

        tabs = QTabWidget()
        tabs.addTab(self.email_tab(), "📧 Email Spam / Ham")
        tabs.addTab(self.weather_tab(), "🌤️ Play Tennis")
        main.addWidget(tabs)

    # ==================================================
    # EMAIL TAB
    # ==================================================
    def email_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.prior_label = QLabel("P(Spam)=0.50 | P(Ham)=0.50")
        self.prior_label.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self.prior_label)

        self.prior_slider = QSlider(Qt.Horizontal)
        self.prior_slider.setRange(10, 90)
        self.prior_slider.setValue(50)
        self.prior_slider.valueChanged.connect(self.compute_email)
        layout.addWidget(self.prior_slider)

        self.free = self.spin("free", layout)
        self.money = self.spin("money", layout)
        self.meeting = self.spin("meeting", layout)

        self.laplace = QCheckBox("Enable Laplace Smoothing")
        self.laplace.setChecked(True)
        self.laplace.stateChanged.connect(self.compute_email)
        layout.addWidget(self.laplace)

        self.email_formula = QTextEdit()
        self.email_formula.setReadOnly(True)
        layout.addWidget(self.email_formula)

        self.spam_bar = self.card("P(Spam | Email)", layout)
        self.ham_bar = self.card("P(Ham | Email)", layout)

        self.compute_email()
        return tab

    # ==================================================
    # WEATHER TAB
    # ==================================================
    def weather_tab(self):
        tab = QWidget()
        main = QHBoxLayout(tab)

        left = QVBoxLayout()
        self.outlook = self.combo("Outlook", ["Sunny","Overcast","Rainy"], left)
        self.temp = self.combo("Temperature", ["Hot","Mild","Cool"], left)
        self.humidity = self.combo("Humidity", ["High","Normal"], left)
        self.wind = self.combo("Wind", ["Weak","Strong"], left)

        self.weather_formula = QTextEdit()
        self.weather_formula.setReadOnly(True)
        left.addWidget(self.weather_formula)

        main.addLayout(left, 2)

        right = QVBoxLayout()
        self.play_bar = self.card("P(Play | Conditions)", right)
        self.no_bar = self.card("P(Don't Play | Conditions)", right)

        self.weather_result = QLabel()
        self.weather_result.setFont(QFont("Segoe UI", 18, QFont.Bold))
        right.addWidget(self.weather_result)

        table = QTableWidget(len(self.tennis_df), len(self.tennis_df.columns))
        table.setHorizontalHeaderLabels(self.tennis_df.columns)
        for i in range(len(self.tennis_df)):
            for j in range(len(self.tennis_df.columns)):
                table.setItem(i, j, QTableWidgetItem(self.tennis_df.iloc[i, j]))
        right.addWidget(table)

        main.addLayout(right, 3)

        for cb in [self.outlook, self.temp, self.humidity, self.wind]:
            cb.currentTextChanged.connect(self.compute_weather)

        self.compute_weather()
        return tab

    # ==================================================
    # LOGIC – EMAIL (WITH FORMULA)
    # ==================================================
    def compute_email(self):
        f, m, me = self.free.value(), self.money.value(), self.meeting.value()
        p_spam = self.prior_slider.value() / 100
        p_ham = 1 - p_spam

        def P(cls, word):
            v = self.email_prob[cls][word]
            return max(v, 0.01) if self.laplace.isChecked() else v

        spam = p_spam * P("spam","free")**f * P("spam","money")**m * P("spam","meeting")**me
        ham = p_ham * P("ham","free")**f * P("ham","money")**m * P("ham","meeting")**me

        total = spam + ham + 1e-12
        ps, ph = spam/total, ham/total

        self.spam_bar.setValue(int(ps*100))
        self.ham_bar.setValue(int(ph*100))
        self.spam_bar.setStyleSheet(
            "QProgressBar::chunk { background:red; }" if ps > 0.5 else
            "QProgressBar::chunk { background:#80fac0; }"
        )

        self.prior_label.setText(f"P(Spam)={p_spam:.2f} | P(Ham)={p_ham:.2f}")

        self.email_formula.setText(
            f"P(Spam | Email) = P(Spam) × P(free)^{f} × P(money)^{m} × P(meeting)^{me}\n"
            f"= {p_spam:.2f} × {P('spam','free'):.2f}^{f} × {P('spam','money'):.2f}^{m} × {P('spam','meeting'):.2f}^{me}\n"
            f"= {spam:.4f} (unnormalized)\n"
            f"= {ps:.3f} (normalized)"
        )

    # ==================================================
    # LOGIC – WEATHER (WITH FORMULA)
    # ==================================================
    def compute_weather(self):
        df = self.tennis_df
        X = {
            "Outlook": self.outlook.currentText(),
            "Temperature": self.temp.currentText(),
            "Humidity": self.humidity.currentText(),
            "Wind": self.wind.currentText()
        }

        def posterior(label):
            sub = df[df["Play"] == label]
            p = len(sub) / len(df)
            probs = []
            for k, v in X.items():
                pv = (len(sub[sub[k] == v]) + 1) / (len(sub) + len(df[k].unique()))
                probs.append(pv)
                p *= pv
            return p, probs

        play_u, play_probs = posterior("Yes")
        no_u, _ = posterior("No")

        s = play_u + no_u
        play, no = play_u/s, no_u/s

        self.play_bar.setValue(int(play*100))
        self.no_bar.setValue(int(no*100))

        self.weather_result.setText(
            f"🎾 PLAY TENNIS ({play*100:.1f}%)" if play > no
            else f"❌ DON'T PLAY ({no*100:.1f}%)"
        )

        self.weather_formula.setText(
            f"P(Play | Conditions) = P(Play) × P(O|Play) × P(T|Play) × P(H|Play) × P(W|Play)\n"
            f"= {len(df[df['Play']=='Yes'])/len(df):.3f} × "
            f"{play_probs[0]:.3f} × {play_probs[1]:.3f} × {play_probs[2]:.3f} × {play_probs[3]:.3f}\n"
            f"= {play_u:.4f} (unnormalized)\n"
            f"= {play:.3f} (normalized)"
        )

    # ==================================================
    # HELPERS
    # ==================================================
    def spin(self, name, layout):
        layout.addWidget(QLabel(f'Word "{name}" count'))
        s = QSpinBox()
        s.setRange(0, 10)
        s.valueChanged.connect(self.compute_email)
        layout.addWidget(s)
        return s

    def combo(self, label, items, layout):
        layout.addWidget(QLabel(label))
        cb = QComboBox()
        cb.addItems(items)
        layout.addWidget(cb)
        return cb

    def card(self, title, layout):
        box = QFrame()
        v = QVBoxLayout(box)
        v.addWidget(QLabel(title))
        bar = QProgressBar()
        v.addWidget(bar)
        layout.addWidget(box)
        return bar


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = NaiveBayesVisualizer()
    w.show()
    sys.exit(app.exec_())
