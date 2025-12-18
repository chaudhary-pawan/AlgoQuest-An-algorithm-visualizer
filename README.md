# AlgoQuest: An Algorithm Visualizer

AlgoQuest is a comprehensive algorithm visualizer that provides insightful visuals and step-by-step breakdowns of various algorithms. The goal of this project is to make understanding complex algorithms easier and more intuitive.

## Table of Contents
- [Features](#features)
- [How to Use](#how-to-use)
- [Implemented Algorithms](#implemented-algorithms)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- Supports visualization of a variety of graph-related algorithms.
- Enables users to input custom graphs or use predefined examples.
- Interactive features for pausing, rewinding, and customizing the visualization.

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

## Implemented Algorithms

### 1. Greedy Source Expansion
A community detection algorithm that identifies local communities around a source node. It adds neighboring nodes that maximize local modularity to the community iteratively until no more gain is possible.
- **Applications**: Social networks, clustering in graphs.

---

### 2. Minimum Spanning Tree (Kruskal’s and Prim’s Algorithms)
Finds the minimum spanning tree (or forest) of a graph.
- **Kruskal's Algorithm**: Adds edges in increasing order of weight, avoiding cycles.
- **Prim's Algorithm**: Grows a single tree by adding the smallest edge that expands the tree.

---

### 3. Double Edge Swap
Maintains graph connectivity while performing random double-edge swaps to anonymize graphs effectively.
- **Applications**: Privacy in graph datasets, random graph testing.

---

### 4. Bridge-Finding Algorithms
Detects "bridges" (critical edges) in a graph. A bridge is an edge whose removal increases the number of disconnected components of the graph.
- **Applications**: Network reliability, road networks.

---

### 5. Dominating Sets
An approximation algorithm for finding connected dominating sets in a graph. This is used for problems like network coverage and routing in ad hoc networks.
- **Algorithm**: Iteratively adds nodes to a dominating set by considering degrees of neighbors.

---

### 6. Sparsifiers
Implements sparsification methods that reduce the number of edges in a graph while preserving its essential properties.
- **Applications**: Faster graph operations, graph compression.

---

### 7. Communicability
Measures the ease of communication or flow of information between nodes using spectral graph theory.
- **Applications**: Social network analysis, information flow studies.

---

### 8. Maximum Flow (Edmonds-Karp Algorithm)
Uses the Edmonds-Karp method to calculate the maximum flow in a network graph. This is an important algorithm in graph algorithms, solving single-source-to-single-sink network flow problems.
- **Applications**: Logistics, water distribution, telecommunications.

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
