# Mathematical Model Specification

**Project Title:** System and Method for Evolutionary Software Quality Assessment and Metric Recommendation Using Software DNA Mutation Analysis

---

## 1. Metric Normalization

To convert raw metrics $m_k(u,t)$ into a standard normalized scale $\tilde{m}_k(u,t) \in [0, 1]$:

$$\tilde{m}_k(u,t) = \frac{1}{1 + \exp\left(-\gamma_k (m_k(u,t) - \theta_k^{(0)})\right)}$$

Where:
- $m_k(u,t)$: Raw value of metric $k$ for source unit $u$ at commit/version $t$.
- $\theta_k^{(0)}$: Baseline threshold or domain median for metric $k$ (e.g., CC=15, WMC=30, CBO=14, LCOM=0.5).
- $\gamma_k$: Scaling parameter controlling sigmoidal slope.

---

## 2. Evolutionary Software DNA State

At each commit/version $t$, the software state is formally defined as:

$$D_t = (V_t, E_t, M_t)$$

- $V_t$: Set of structural software units (modules, classes, methods).
- $E_t$: Directed structural dependency graph edges (calls, imports, inheritance).
- $M_t$: Normalized metric state matrix across all units $u \in V_t$ and metrics $k \in \{LOC, CC, WMC, CBO, LCOM\}$.

---

## 3. Five-Dimensional Mutation Vector $\Phi(u,k,t)$

A metric mutation occurs when the change exceeds a sensitivity threshold $\delta_k$:

$$\mu(u,k,t) = \begin{cases} 1 & \text{if } \Delta \tilde{m}_k(u,t) \ge \delta_k \\ 0 & \text{otherwise} \end{cases}$$

Where $\Delta \tilde{m}_k(u,t) = \tilde{m}_k(u,t) - \tilde{m}_k(u,t-1)$.

For each detected mutation, the 5-Dimensional vector is evaluated:

$$\Phi(u,k,t) = [M, P, A, C, R]^T$$

### 1. Magnitude ($M$)
$$M(u,k,t) = \min\left(1.0, \frac{\Delta \tilde{m}_k(u,t)}{\sigma_k}\right)$$
Where $\sigma_k$ is the historical standard deviation of changes for metric $k$ (with fallback $\sigma_k > 0$).

### 2. Persistence ($P$)
$$P(u,k,t) = \frac{1}{H} \sum_{h=0}^{H-1} \mu(u,k,t-h)$$
Over historical inspection window $H$.

### 3. Acceleration ($A$)
$$A_{\text{raw}} = \max\left(0, \frac{\Delta m_t - \Delta m_{t-1}}{\max(\Delta m_{t-1}, \varepsilon)}\right)$$
$$A = \frac{2}{1 + \exp(-A_{\text{raw}})} - 1$$

### 4. Co-occurrence ($C$)
$$C(u,k,t) = \frac{1}{K-1} \sum_{j \ne k} \mu(u,j,t)$$
Where $K$ is the total count of canonical DNA metrics ($K=5$: LOC, CC, WMC, CBO, LCOM). The evaluated metric $k$ is excluded from the summation ($j \ne k$), and the denominator is $K-1=4$. For binary mutation indicators $\mu(u,j,t) \in \{0, 1\}$, valid co-occurrence values are strictly discrete: $C \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$, representing 0, 1, 2, 3, or 4 other mutated metrics in unit $u$.

### 5. Recency ($R$)
$$R(t) = \exp(-\lambda (t_{\text{current}} - t)) \quad \text{or} \quad R(t) = \frac{t}{N}$$
Where $\lambda$ is the exponential decay parameter and $N$ is total version sequence length.

---

## 4. Source-Level Evolutionary Risk

The mutation severity $S(u,k,t)$ combining the 5 dimensions:

$$S(u,k,t) = W_{\text{dim}} \cdot \Phi(u,k,t)$$

Where $W_{\text{dim}} = [w_M, w_P, w_A, w_C, w_R]$ with $\sum w_d = 1.0$.

The composite risk for source unit $u$ across all metrics:

$$R(u,t) = \sum_{k} \omega_k \mu(u,k,t) S(u,k,t)$$

Where $\omega_k$ are metric importance weights ($\sum \omega_k = 1.0$).

---

## 5. Evolutionary Software DNA Index (ESDI)

$$ESDI(t) = \sum_{u \in V_t} \alpha(u) R(u,t)$$

Where $\alpha(u)$ represents the normalized graph centrality (e.g., PageRank or degree centrality) of source unit $u$, satisfying:

$$\sum_{u \in V_t} \alpha(u) = 1.0$$

---

## 6. CI/CD Quality Gate Thresholds

| Decision | ESDI Condition | Unit Peak Risk Condition | Action |
|---|---|---|---|
| **PASS** | $ESDI < 0.35$ (or $< 50.0$) | $\max_u R(u,t) < 0.50$ | Build proceeds automatically. |
| **WARN** | $0.35 \le ESDI < 0.65$ | $\max_u R(u,t) < 0.80$ | Build passes with review warnings. |
| **BLOCK** | $0.65 \le ESDI < 0.80$ | $0.80 \le \max_u R(u,t) < 0.90$ | PR blocked; automated remediation suggested. |
| **CRITICAL BLOCK** | $ESDI \ge 0.80$ (or $\ge 90.0$) | $\max_u R(u,t) \ge 0.90$ | Build rejected; quarantine commit. |
