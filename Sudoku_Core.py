import re
import google.generativeai as gemini
import PIL.Image
from pysat.solvers import Glucose3

import config  # must contain GOOGLE_API_KEY


# ==========================
# 0) Gemini API setup
# ==========================

GOOGLE_API_KEY = config.GOOGLE_API_KEY

gemini.configure(api_key=GOOGLE_API_KEY)

GENERATION_CONFIG = {
    "temperature": 0.1,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

GEMINI_MODEL = gemini.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=GENERATION_CONFIG
)


# ==========================
# 1) Image -> 9x9 grid
# ==========================

def image_to_sudoku_grid(image_path):
    try:
        img = PIL.Image.open(image_path)
    except FileNotFoundError:
        print("ERROR: Image file not found:", image_path)
        return None

    prompt = """
Extract the Sudoku grid from this image.
Return EXACTLY 9 lines.
Each line must contain 9 integers separated by commas.
Use 0 for empty cells.
No explanation or extra text.
"""

    response = GEMINI_MODEL.generate_content([prompt, img])

    try:
        raw = response.text
    except:
        print("ERROR: Could not read Gemini output.")
        return None

    rows = raw.strip().split("\n")
    if len(rows) != 9:
        print("ERROR: Gemini did not return 9 lines.")
        return None

    grid = []
    for row in rows:
        cells = row.split(",")
        if len(cells) != 9:
            print("ERROR: Row does not contain 9 cells:", row)
            return None

        values = []
        for cell in cells:
            digits = re.sub(r"\D", "", cell.strip())
            if digits == "":
                values.append(0)
            else:
                values.append(int(digits))

        grid.append(values)

    return grid


# ==========================
# 2) SAT encoding
# ==========================

def var_id(i, j, n):
    return 81 * (n - 1) + 9 * (i - 1) + j


def encode_sudoku_to_cnf(grid):
    cnf = []

    # Cell constraints: each cell has EXACTLY 1 number
    for i in range(1, 10):
        for j in range(1, 10):

            # At least one number
            clause = []
            for n in range(1, 10):
                clause.append(var_id(i, j, n))
            cnf.append(clause)

            # At most one number
            for n1 in range(1, 10):
                for n2 in range(n1 + 1, 10):
                    cnf.append([
                        -var_id(i, j, n1),
                        -var_id(i, j, n2)
                    ])

    # Row constraints
    for i in range(1, 10):
        for n in range(1, 10):

            clause = []
            for j in range(1, 10):
                clause.append(var_id(i, j, n))
            cnf.append(clause)

            for j1 in range(1, 10):
                for j2 in range(j1 + 1, 10):
                    cnf.append([
                        -var_id(i, j1, n),
                        -var_id(i, j2, n)
                    ])

    # Column constraints
    for j in range(1, 10):
        for n in range(1, 10):

            clause = []
            for i in range(1, 10):
                clause.append(var_id(i, j, n))
            cnf.append(clause)

            for i1 in range(1, 10):
                for i2 in range(i1 + 1, 10):
                    cnf.append([
                        -var_id(i1, j, n),
                        -var_id(i2, j, n)
                    ])

    # Block constraints
    for br in range(0, 3):
        for bc in range(0, 3):
            for n in range(1, 10):

                cells = []
                for di in range(1, 4):
                    for dj in range(1, 4):
                        i = 3 * br + di
                        j = 3 * bc + dj
                        cells.append((i, j))

                clause = []
                for (i, j) in cells:
                    clause.append(var_id(i, j, n))
                cnf.append(clause)

                for a in range(len(cells)):
                    for b in range(a + 1, len(cells)):
                        i1, j1 = cells[a]
                        i2, j2 = cells[b]
                        cnf.append([
                            -var_id(i1, j1, n),
                            -var_id(i2, j2, n)
                        ])

    # Given clues
    for i in range(1, 10):
        for j in range(1, 10):
            v = grid[i - 1][j - 1]
            if v != 0:
                cnf.append([var_id(i, j, v)])

    return cnf


def is_satisfiable_via_sat(grid):
    """Return True if Sudoku has at least one solution."""
    cnf = encode_sudoku_to_cnf(grid)

    solver = Glucose3()
    for clause in cnf:
        solver.add_clause(clause)

    sat = solver.solve()
    solver.delete()

    return sat


# ==========================
# 3) High-level solver for GUI
# ==========================

def solve_sudoku_from_image(image_path):
    """Used by GUI: image → grid → SAT → backtracking → solutions."""
    from Sudoku_Backtracking import solve_all_solutions

    grid = image_to_sudoku_grid(image_path)
    if grid is None:
        return None, None

    if not is_satisfiable_via_sat(grid):
        return grid, []

    solutions = solve_all_solutions(grid)
    return grid, solutions
