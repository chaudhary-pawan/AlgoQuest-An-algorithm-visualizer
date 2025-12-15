import sys
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSlider
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont


# ===================== COLORS =====================
BLUE_POINT = QColor(30, 120, 255)
ORANGE_POINT = QColor(255, 165, 0)
EDGE_POS = QColor(40, 110, 255)
EDGE_NEG = QColor(255, 120, 0)


# ===================== DATASET =====================
def make_circles(n=60, noise=0.05):
    n2 = n // 2
    r1 = np.random.randn(n2) * noise + 0.6
    t1 = np.random.rand(n2) * 2*np.pi
    r2 = np.random.randn(n2) * noise + 1.4
    t2 = np.random.rand(n2) * 2*np.pi

    X1 = np.c_[r1*np.cos(t1), r1*np.sin(t1)]
    X2 = np.c_[r2*np.cos(t2), r2*np.sin(t2)]

    X = np.vstack([X1, X2])
    y = np.array([1]*n2 + [0]*n2)
    return X, y


# ===================== NEURAL NETWORK =====================
class NeuralNetwork:
    def __init__(self):
        self.h1, self.h2 = 8, 6
        self.lr = 0.15
        self.activation = "tanh"
        self.reset()

    def reset(self):
        self.W1 = np.random.randn(2, self.h1) * 0.6
        self.b1 = np.zeros((1, self.h1))
        self.W2 = np.random.randn(self.h1, self.h2) * 0.6
        self.b2 = np.zeros((1, self.h2))
        self.W3 = np.random.randn(self.h2, 1) * 0.6
        self.b3 = np.zeros((1, 1))

    # ---- activations ----
    def act(self, x):
        if self.activation == "relu":
            return np.maximum(0, x)
        if self.activation == "sigmoid":
            return 1 / (1 + np.exp(-x))
        return np.tanh(x)

    def dact(self, x):
        if self.activation == "relu":
            return (x > 0).astype(float)
        if self.activation == "sigmoid":
            s = 1 / (1 + np.exp(-x))
            return s * (1 - s)
        return 1 - np.tanh(x)**2

    def forward(self, X):
        self.z1 = X @ self.W1 + self.b1
        self.a1 = self.act(self.z1)
        self.z2 = self.a1 @ self.W2 + self.b2
        self.a2 = self.act(self.z2)
        self.z3 = self.a2 @ self.W3 + self.b3
        self.out = 1 / (1 + np.exp(-self.z3))
        return self.out

    def train(self, X, y):
        y = y.reshape(-1,1)
        out = self.forward(X)

        eps = 1e-9
        loss = -np.mean(y*np.log(out+eps)+(1-y)*np.log(1-out+eps))

        dZ3 = out - y
        dW3 = self.a2.T @ dZ3
        db3 = dZ3.mean(axis=0)

        dZ2 = (dZ3 @ self.W3.T) * self.dact(self.z2)
        dW2 = self.a1.T @ dZ2
        db2 = dZ2.mean(axis=0)

        dZ1 = (dZ2 @ self.W2.T) * self.dact(self.z1)
        dW1 = X.T @ dZ1
        db1 = dZ1.mean(axis=0)

        self.W3 -= self.lr * dW3
        self.b3 -= self.lr * db3
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1

        return loss


# ===================== NETWORK VIEW =====================
class NetworkView(QWidget):
    def __init__(self, nn):
        super().__init__()
        self.nn = nn
        self.setFixedWidth(360)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        h = self.height()

        layers = [2, self.nn.h1, self.nn.h2, 1]
        xs = [60, 160, 260, 330]
        Ws = [self.nn.W1, self.nn.W2, self.nn.W3]

        for i, W in enumerate(Ws):
            maxw = np.max(np.abs(W)) + 1e-6
            for a in range(W.shape[0]):
                for b in range(W.shape[1]):
                    y1 = (h-80)/(layers[i]+1)*(a+1)+40
                    y2 = (h-80)/(layers[i+1]+1)*(b+1)+40
                    col = EDGE_POS if W[a,b] > 0 else EDGE_NEG
                    thick = 1 + 5*abs(W[a,b])/maxw
                    p.setPen(QPen(col, thick))
                    p.drawLine(QPointF(xs[i],y1), QPointF(xs[i+1],y2))

        p.setBrush(QColor(90,150,255))
        p.setPen(Qt.black)
        for i,n in enumerate(layers):
            for j in range(n):
                y = (h-80)/(n+1)*(j+1)+40
                p.drawEllipse(QPointF(xs[i],y), 8, 8)


# ===================== OUTPUT VIEW =====================
class OutputView(QWidget):
    def __init__(self, nn):
        super().__init__()
        self.nn = nn
        self.losses = []
        self.X, self.y = make_circles()

    def paintEvent(self, e):
        p = QPainter(self)
        w,h = self.width(), self.height()
        p.setFont(QFont("Arial",10))

        if self.losses:
            p.drawText(10,20,f"Training loss: {self.losses[-1]:.3f}")

        # ---- EMA loss curve ----
        if len(self.losses) > 2:
            ema=[]
            a=0.15
            for l in self.losses:
                ema.append(l if not ema else a*l+(1-a)*ema[-1])
            p.setPen(QPen(QColor(200,30,30),2))
            for i in range(len(ema)-1):
                p.drawLine(
                    QPointF(220+i*1.2,60-ema[i]*25),
                    QPointF(220+(i+1)*1.2,60-ema[i+1]*25)
                )

        # ---- decision surface ----
        offset = 80
        for i in range(0, w, 2):
            for j in range(offset, h, 2):
                x = (i/w)*4 - 2
                y = ((j-offset)/(h-offset))*4 - 2
                prob = self.nn.forward(np.array([[x,y]]))[0][0]
                if prob > 0.5:
                    c = QColor(80, 130, 255)    # solid blue
                else:
                    c = QColor(255, 170, 60)    # solid orange

                p.setPen(c)
                p.drawPoint(int(i), int(j))

        for pt,l in zip(self.X,self.y):
            px=int((pt[0]+2)/4*w)
            py=int((pt[1]+2)/4*(h-offset)+offset)
            p.setBrush(BLUE_POINT if l else ORANGE_POINT)
            p.setPen(QPen(Qt.white,1.5))
            p.drawEllipse(px-4,py-4,8,8)


# ===================== MAIN APP =====================
class ANNVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ANN Visualizer")
        self.resize(1400,800)

        self.nn=NeuralNetwork()
        self.net=NetworkView(self.nn)
        self.out=OutputView(self.nn)

        self.timer=QTimer()
        self.timer.timeout.connect(self.train_step)

        self.patience=0
        self.last_loss=None

        # ---- controls ----
        start=QPushButton("▶ Start")
        stop=QPushButton("⏹ Stop")
        reset=QPushButton("⟳ Reset")

        lr_slider=QSlider(Qt.Horizontal)
        lr_slider.setRange(1,50)
        lr_slider.setValue(15)
        lr_label=QLabel("LR: 0.15")

        act_box=QComboBox()
        act_box.addItems(["tanh","relu","sigmoid"])

        start.clicked.connect(lambda:self.timer.start(60))
        stop.clicked.connect(self.timer.stop)
        reset.clicked.connect(self.reset)

        lr_slider.valueChanged.connect(
            lambda v:(setattr(self.nn,"lr",v/100),lr_label.setText(f"LR: {v/100:.2f}"))
        )

        act_box.currentTextChanged.connect(
            lambda a:(setattr(self.nn,"activation",a),self.reset())
        )

        top=QHBoxLayout()
        for w in (start,stop,reset,lr_label,lr_slider,QLabel("Activation:"),act_box):
            top.addWidget(w)

        center=QHBoxLayout()
        center.addWidget(self.net)
        center.addWidget(self.out,1)

        lay=QVBoxLayout()
        lay.addLayout(top)
        lay.addLayout(center)

        c=QWidget()
        c.setLayout(lay)
        self.setCentralWidget(c)

    def train_step(self):
        loss=self.nn.train(self.out.X,self.out.y)
        self.out.losses.append(loss)
        self.out.losses=self.out.losses[-200:]

        # ---- early stopping ----
        if self.last_loss and abs(self.last_loss-loss)<1e-4:
            self.patience+=1
            if self.patience>15:
                self.timer.stop()
        else:
            self.patience=0
        self.last_loss=loss

        pred=(self.nn.forward(self.out.X)>0.5).astype(int).flatten()
        acc=(pred==self.out.y).mean()*100
        self.setWindowTitle(f"ANN Visualizer | Loss: {loss:.3f} | Accuracy: {acc:.1f}%")

        self.net.update()
        self.out.update()

    def reset(self):
        self.timer.stop()
        self.nn.reset()
        self.out.losses.clear()
        self.last_loss=None
        self.patience=0
        self.net.update()
        self.out.update()


# ===================== RUN =====================
if __name__=="__main__":
    app=QApplication(sys.argv)
    win=ANNVisualizer()
    win.show()
    sys.exit(app.exec_())
