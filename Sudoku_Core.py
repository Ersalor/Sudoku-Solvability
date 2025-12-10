import re
import google.generativeai as gemini
import PIL.Image
from pysat.solvers import Glucose3

import config


# ==========================
#         Gemini API 
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

def image_to_sudoku_grid(image_path):
    try:
        img = PIL.Image.open(image_path)
    except FileNotFoundError:
        print("ERROR: Image file not found:", image_path)
        return None

    prompt = """
You are a vision OCR model. Your ONLY job is to READ the Sudoku grid from the image as raw digits. DO NOT solve the puzzle.

TASK:
Extract the 9×9 Sudoku grid exactly as it appears in the image and output it as digits.

HARD OUTPUT RULES (MUST OBEY ALL):
1. Output EXACTLY 9 lines.
2. Each line MUST contain EXACTLY 9 integers.
3. Integers MUST be separated by a single comma (",").
4. Use ONLY digits 0–9.
5. Use 0 for any cell that is blank, partially visible, unclear, ambiguous, or hard to read.
6. NEVER guess or infer digits. If you are not 100% sure about a cell → output 0 for that cell.
7. DO NOT add explanations, text, comments, markdown, code blocks, labels, or extra lines.

OUTPUT FORMAT EXAMPLE:

5,3,0,0,7,0,0,0,0
6,0,0,1,9,5,0,0,0
0,9,8,0,0,0,0,6,0
8,0,0,0,6,0,0,0,3
4,0,0,8,0,3,0,0,1
7,0,0,0,2,0,0,0,6
0,6,0,0,0,0,2,8,0
0,0,0,4,1,9,0,0,5
0,0,0,0,8,0,0,7,9

Now output ONLY the 9 lines in this exact format.
"""

    response = GEMINI_MODEL.generate_content([prompt, img])

    try:
        raw = response.text
    except Exception as e:
        print("ERROR: Could not read Gemini output:", e)
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
                # boş veya okunamayan → 0
                values.append(0)
            elif len(digits) == 1:
                values.append(int(digits))
            else:
                print("ERROR: Cell has more than 1 digit:", cell, "->", digits)
                return None

        grid.append(values)

    return grid


# ==========================
#       SAT Encoding
# ==========================

def var_id(i, j, n):
    """
    i,j konumunda n rakamı için tekil değişken ID'si.
    i,j,n = 1..9
    """
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
    cnf = encode_sudoku_to_cnf(grid)

    solver = Glucose3()
    for clause in cnf:
        solver.add_clause(clause)

    sat = solver.solve()
    solver.delete()

    return sat


# ==========================
#          Solver
# ==========================

def solve_sudoku_from_grid(grid):
    from Sudoku_Backtracking import solve_all_solutions

    if grid is None:
        return None, None

    if not is_satisfiable_via_sat(grid):
        return grid, []

    solutions = solve_all_solutions(grid)
    return grid, solutions
