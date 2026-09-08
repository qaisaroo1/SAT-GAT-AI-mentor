# SAT Quantitative Prep Guide

## Linear Equations and Slope-Intercept Form

### Core Concept
A linear equation in two variables can be written in slope-intercept form:
$$y = mx + b$$
where $m$ is the slope and $b$ is the $y$-intercept $(0, b)$.

The slope $m$ between two points $(x_1, y_1)$ and $(x_2, y_2)$ is given by:
$$m = \frac{y_2 - y_1}{x_2 - x_1}$$

### Parallel and Perpendicular Lines
- **Parallel lines** have equal slopes: $m_1 = m_2$.
- **Perpendicular lines** have negative reciprocal slopes: $m_1 \cdot m_2 = -1 \implies m_2 = -\frac{1}{m_1}$.

### Common SAT Traps
- **Trap 1 (Inverted Slope):** Calculating $\frac{\Delta x}{\Delta y}$ instead of $\frac{\Delta y}{\Delta x}$.
- **Trap 2 (Sign Error on Negative Reciprocal):** Forgetting to negate when finding the perpendicular slope (e.g., thinking perpendicular to $3$ is $\frac{1}{3}$ instead of $-\frac{1}{3}$).
- **Trap 3 (Standard Form Confusion):** For $Ax + By = C$, the slope is $-\frac{A}{B}$, not $\frac{A}{B}$.

---

## Systems of Linear Equations

### Number of Solutions
For a system of two linear equations:
$$\begin{cases} a_1 x + b_1 y = c_1 \\ a_2 x + b_2 y = c_2 \end{cases}$$

1. **Exactly One Solution:** The lines intersect at one point. This occurs when slopes are different: $\frac{a_1}{a_2} \neq \frac{b_1}{b_2}$.
2. **Infinitely Many Solutions:** The lines are identical (coincident). Slopes and intercepts are proportional: $\frac{a_1}{a_2} = \frac{b_1}{b_2} = \frac{c_1}{c_2}$.
3. **No Solution:** The lines are parallel and distinct. Slopes are equal, but intercepts differ: $\frac{a_1}{a_2} = \frac{b_1}{b_2} \neq \frac{c_1}{c_2}$.

### Common SAT Traps
- **Trap 1:** Confusing "No solution" with "Infinitely many solutions" by forgetting to compare the constants ($c_1, c_2$).
- **Trap 2:** Not solving for the requested expression (e.g., the question asks for $x + y$, but the student stops after finding $x$).

---

## Quadratic Functions and Parabola Properties

### Standard, Vertex, and Factored Forms
1. **Standard Form:** $f(x) = ax^2 + bx + c$
   - $y$-intercept is $(0, c)$.
   - Axis of symmetry: $x = -\frac{b}{2a}$.
   - Vertex coordinates: $\left(-\frac{b}{2a}, f\left(-\frac{b}{2a}\right)\right)$.

2. **Vertex Form:** $f(x) = a(x - h)^2 + k$
   - Vertex is $(h, k)$.
   - If $a > 0$, the parabola opens upward and has a minimum value of $k$.
   - If $a < 0$, the parabola opens downward and has a maximum value of $k$.

3. **Factored Form:** $f(x) = a(x - r_1)(x - r_2)$
   - $x$-intercepts (roots/zeros) are $r_1$ and $r_2$.

### The Discriminant
For $ax^2 + bx + c = 0$, the discriminant is $D = b^2 - 4ac$:
- $D > 0$: Two distinct real solutions.
- $D = 0$: Exactly one real solution (double root; tangent to $x$-axis).
- $D < 0$: No real solutions (two complex roots; does not touch $x$-axis).

### Common SAT Traps
- **Trap 1 (Vertex Sign Error):** In $y = 2(x + 3)^2 - 5$, the vertex is $(-3, -5)$, NOT $(3, -5)$.
- **Trap 2 (Extreme Value Meaning):** Confusing the $x$-value where the maximum occurs ($x = h$) with the maximum value itself ($y = k$).

---

## Geometry: Circles in the Coordinate Plane

### Standard Equation of a Circle
The standard equation of a circle with center $(h, k)$ and radius $r$ is:
$$(x - h)^2 + (y - k)^2 = r^2$$

### Completing the Square for Circles
If given in general form $x^2 + y^2 + Dx + Ey + F = 0$:
1. Group $x$ terms and $y$ terms: $(x^2 + Dx) + (y^2 + Ey) = -F$.
2. Complete the square for both: add $\left(\frac{D}{2}\right)^2$ and $\left(\frac{E}{2}\right)^2$ to both sides.
3. Factor into standard form $(x - h)^2 + (y - k)^2 = r^2$.

### Common SAT Traps
- **Trap 1 ($r^2$ vs $r$):** The right side of the equation is $r^2$. If the equation ends in $= 25$, the radius is $5$, NOT $25$. If radius is $6$, the equation ends in $36$.
- **Trap 2 (Center Signs):** In $(x - 4)^2 + (y + 7)^2 = 16$, center is $(4, -7)$, not $(-4, 7)$.
