# 🚀 AlgoQuest – An Interactive Algorithm Visualizer

AlgoQuest is an **interactive algorithm visualization platform** designed to help students and beginners **understand how algorithms work internally** through real-time visual simulations.  
Instead of just reading theory, users can *see* how data changes step-by-step during algorithm execution.

This project focuses on **learning by visualization**, making complex concepts intuitive and engaging.

---

## ✨ Features

### 🔢 Algorithm Visualizations
- **Sorting Algorithms**
  - Bubble Sort
  - Selection Sort
  - Insertion Sort
  - (Extendable to Merge Sort, Quick Sort, etc.)
- **Searching Algorithms**
  - Linear Search
  - Binary Search
- **Machine Learning (Planned / In Progress)**
  - K-Nearest Neighbors (KNN)
  - Decision Tree
  - Naive Bayes
  - Neural Network Workflow Visualization

---

### 🎛️ Interactive Controls
- Adjustable **input size**
- **Speed control** for animations
- Step-by-step execution
- Real-time value and comparison highlights

---

### 📊 Educational Focus
- Clear visualization of:
  - Comparisons
  - Swaps
  - Traversals
- Helps understand:
  - Time complexity intuition
  - Algorithm behavior on different inputs

---

## 🛠️ Tech Stack

- **Python**
- **PyQt5** – GUI development
- **NumPy** – data handling
- **Custom animation logic** for step-wise visualization

---

## 🎯 Learning Objectives

- Understand algorithm flow visually

- Bridge the gap between theory and execution

- Build intuition for time & space complexity

- Explore ML algorithm workflows interactively
---

## How to Use

1. Clone the repository:
   ```bash
   git clone https://github.com/chaudhary-pawan/AlgoQuest-An-algorithm-visualizer.git
   ```

2. Navigate to the project directory:
   ```bash
   cd AlgoQuest-An-algorithm-visualizer
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the visualizer:
   ```bash
   python main.py
   ```

## 🧠 Implemented Algorithms

AlgoQuest currently supports a wide range of **algorithm visualizations**, covering **core DSA topics** as well as **Machine Learning workflows**. Each algorithm is implemented as a separate visualizer module for clarity and extensibility.

---

### 🔁 Sorting Algorithms
Implemented in:
- `sorting_visualizer.py`

Algorithms visualized:
- Bubble Sort
- Selection Sort
- Insertion Sort  
(With step-by-step comparisons, swaps, and animated transitions)

---

### 🔍 Searching Algorithms
Implemented in:
- `search_visualizer.py`

Algorithms visualized:
- Linear Search
- Binary Search  
(Highlights comparisons and search boundaries dynamically)

---

### 🌳 Graph Algorithms
Implemented in:
- `graph_visualizer.py`
- `graph_traversal.py`

Algorithms visualized:
- Breadth First Search (BFS)
- Depth First Search (DFS)

Features:
- Node-by-node traversal animation
- Visited / unvisited state visualization

---

### 🧮 Dynamic Programming
Implemented in:
- `dp_visualizer.py`

Algorithms visualized:
- Common DP problems with table-based visualization
- Shows state transitions and optimal substructure clearly

---

### 🛣️ Shortest Path Algorithms
Implemented in:
- `shortest_path.py`

Algorithms visualized:
- Dijkstra’s Algorithm  
(Shows distance updates and path relaxation process)

---

### 🌲 Minimum Spanning Tree (MST)
Implemented in:
- `mst_visualizer.py`

Algorithms visualized:
- Prim’s Algorithm
- Kruskal’s Algorithm  
(Edge selection and cycle detection are animated)

---

### 🔗 Directed Acyclic Graph (DAG)
Implemented in:
- `dag_visualizer.py`

Algorithms visualized:
- Topological Sorting  
(Shows dependency resolution visually)

---

## 🤖 Machine Learning Algorithm Visualizers

### 🧠 Artificial Neural Network (ANN)
Implemented in:
- `ml_ann_visualizer.py`

Features:
- Input, hidden, and output layer visualization
- Forward propagation
- Loss calculation
- Weight & bias updates during backpropagation

---

### 🌳 Decision Tree
Implemented in:
- `ml_decision_tree_visualizer.py`
- Output example: `decision_tree_final.png`

Features:
- Tree structure visualization
- Feature-based splitting
- Decision paths highlighting

---

### 📊 Naive Bayes Classifier
Implemented in:
- `ml_naive_bayes_visualizer.py`

Features:
- Probability calculation steps
- Class-wise likelihood visualization
- Final prediction explanation

---

### 📈 Regression Algorithms
Implemented in:
- `ml_regression_visualizer.py`

Algorithms visualized:
- Linear Regression

Features:
- Line fitting process
- Error / loss visualization

---

### 📌 K-Means Clustering
Implemented in:
- `ml_kmeans_visualizer.py`

Features:
- Cluster initialization
- Iterative centroid updates
- Data point re-assignment visualization

---

### 🧩 ML Workflow Controller
Implemented in:
- `ml_visualizer.py`

Purpose:
- Acts as a unified interface to launch and manage ML algorithm visualizations

---

## 🧠 Core Application Files

- `main.py` → Entry point of the application
- `neon_theme_qss.py` → Custom neon UI theme
- `requirements.txt` → Project dependencies
- `build/` & `dist/` → Packaged executable files
- `main.spec` → PyInstaller configuration

---

📌 **Note:**  
The modular design allows easy addition of new algorithms by simply creating a new visualizer file and registering it in `main.py`.

---

## Contributing

Contributions to AlgoQuest are welcome! To contribute, follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes and submit a pull request.

For more detailed contribution guidelines, refer to `CONTRIBUTING.md`.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
