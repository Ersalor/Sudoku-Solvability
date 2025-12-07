import re

import google.generativeai as genai
import PIL.Image
from pysat.solvers import Glucose3

import config  # must contain GOOGLE_API_KEY


# ==========================
# 0) Gemini API setup
# ==========================

GOOGLE_API_KEY = config.Google_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)

GENERATION_CONFIG = {
    "temperature": 0.1,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

GEMINI_MODEL = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=GENERATION_CONFIG
)


# ==========================
# 1) Image -> 9x9 Sudoku grid
# ==========================

def image_to_sudoku_grid(image_path):
    """
    Use Gemini to read a Sudoku image and convert it into a 9x9 integer grid.
    Filled cells: 1..9, empty cells: 0.
    Returns the 9x9 grid, or None if something goes wrong.
    """
    try:
        img = PIL.Image.open(image_path)
    except FileNotFoundError:
        print("ERROR: Image file not found:", image_path)
        return None

    prompt = """
You are given an image of a Sudoku puzzle.
Convert the Sudoku grid into a 9x9 matrix.

- Use 0 for empty cells.
- Use the digit you see for filled cells.
- Output EXACTLY 9 lines.
- Each line must contain 9 numbers separated by commas.
- Do NOT add any explanation or extra text.

Example format:
0,0,3,0,2,0,6,0,0
9,0,0,3,0,5,0,0,1
0,0,1,8,0,6,4,0,0
0,0,8,1,0,2,9,0,0
7,0,0,0,0,0,0,0,8
0,0,6,7,0,8,2,0,0
0,0,2,6,0,9,5,0,0
8,0,0,2,0,3,0,0,9
0,0,5,0,1,0,3,0,0
"""

    print("Sending Sudoku image to Gemini...")
    response = GEMINI_MODEL.generate_content([prompt, img])

    try:
        raw_text = response.text
    except Exception as e:
        print("ERROR: Could not read text from Gemini response:", e)
        return None

    print("\n--- Raw API response ---")
    print(raw_text)
    print("------------------------")

    rows = raw_text.strip().split("\n")
    if len(rows) != 9:
        print("ERROR: Expected 9 lines, got", len(rows))
        return None

    grid = []

    for row_str in rows:
        cells = row_str.split(",")
        if len(cells) != 9:
            print("ERROR: Expected 9 cells in a row, got", len(cells))
            print("Row:", row_str)
            return None

        row_values = []
        for cell in cells:
            cell = cell.strip()
            # Keep only digits
            digits = re.sub(r"\D", "", cell)
            if digits == "":
                row_values.append(0)
            else:
                row_values.append(int(digits))

        grid.append(row_values)

    print("\n=== Parsed 9x9 grid ===")
    for row in grid:
        print(row)

    return grid


# ==========================
# 2) Phase 1: SAT encoding
# ==========================

def var_id(i, j, n):
    """
    Map proposition p(i, j, n) to a unique integer in [1, 729].
    i, j, n are 1..9 (1-based indices).
    """
    return 81 * (n - 1) + 9 * (i - 1) + j


def encode_sudoku_to_cnf(grid):
    """
    Encode a 9x9 Sudoku grid into CNF clauses.

    grid:
        9x9 list of ints
        0    -> empty cell
        1..9 -> given number

    Returns:
        cnf: list of clauses
        each clause is a list of ints (literals).
    """
    cnf = []

    # 2.1) Cell constraints: each cell contains EXACTLY one number
    for i in range(1, 10):          # row index (1..9)
        for j in range(1, 10):      # column index (1..9)

            # At least one number in this cell:
            # p(i,j,1) OR p(i,j,2) OR ... OR p(i,j,9)
            clause = []
            for n in range(1, 10):
                clause.append(var_id(i, j, n))
            cnf.append(clause)

            # At most one number in this cell:
            # For each pair (n1, n2): ¬p(i,j,n1) OR ¬p(i,j,n2)
            for n1 in range(1, 10):
                for n2 in range(n1 + 1, 10):
                    cnf.append([
                        -var_id(i, j, n1),
                        -var_id(i, j, n2),
                    ])

    # 2.2) Row constraints: each number appears EXACTLY once in each row
    for i in range(1, 10):          # row
        for n in range(1, 10):      # number

            # At least once: p(i,1,n) OR p(i,2,n) OR ... OR p(i,9,n)
            clause = []
            for j in range(1, 10):
                clause.append(var_id(i, j, n))
            cnf.append(clause)

            # At most once:
            # For each pair (j1, j2): ¬p(i,j1,n) OR ¬p(i,j2,n)
            for j1 in range(1, 10):
                for j2 in range(j1 + 1, 10):
                    cnf.append([
                        -var_id(i, j1, n),
                        -var_id(i, j2, n),
                    ])

    # 2.3) Column constraints: each number appears EXACTLY once in each column
    for j in range(1, 10):          # column
        for n in range(1, 10):      # number

            # At least once: p(1,j,n) OR ... OR p(9,j,n)
            clause = []
            for i in range(1, 10):
                clause.append(var_id(i, j, n))
            cnf.append(clause)

            # At most once:
            # For each pair (i1, i2): ¬p(i1,j,n) OR ¬p(i2,j,n)
            for i1 in range(1, 10):
                for i2 in range(i1 + 1, 10):
                    cnf.append([
                        -var_id(i1, j, n),
                        -var_id(i2, j, n),
                    ])

    # 2.4) Block constraints: each number appears EXACTLY once in each 3x3 block
    for block_row in range(0, 3):       # 0,1,2
        for block_col in range(0, 3):   # 0,1,2
            for n in range(1, 10):      # number

                # Collect all cells in the current 3x3 block
                cells = []
                for di in range(1, 4):      # 1..3
                    for dj in range(1, 4):  # 1..3
                        i = 3 * block_row + di
                        j = 3 * block_col + dj
                        cells.append((i, j))

                # At least once in the block
                clause = []
                for (i, j) in cells:
                    clause.append(var_id(i, j, n))
                cnf.append(clause)

                # At most once in the block:
                # For each pair of different cells:
                # ¬p(i1,j1,n) OR ¬p(i2,j2,n)
                for idx1 in range(len(cells)):
                    for idx2 in range(idx1 + 1, len(cells)):
                        i1, j1 = cells[idx1]
                        i2, j2 = cells[idx2]
                        cnf.append([
                            -var_id(i1, j1, n),
                            -var_id(i2, j2, n),
                        ])

    # 2.5) Initial givens: fix the numbers already present in the grid
    for i in range(1, 10):
        for j in range(1, 10):
            value = grid[i - 1][j - 1]  # grid is 0-based
            if value != 0:
                # This cell must contain "value"
                cnf.append([var_id(i, j, value)])

    return cnf


def is_satisfiable_via_sat(grid):
    """
    Phase 1:
    Check if the given Sudoku grid has at least one solution.

    Returns:
        True  -> SAT (at least one solution exists)
        False -> UNSAT (no solution exists)
    """
    cnf = encode_sudoku_to_cnf(grid)

    solver = Glucose3()
    for clause in cnf:
        solver.add_clause(clause)

    sat = solver.solve()
    solver.delete()

    return sat


# ==========================
# 3) Main: glue everything
# ==========================

def main():
    image_path = "sudoku1.png"

    # Step 1: use Gemini to parse the Sudoku image
    grid = image_to_sudoku_grid(image_path)
    if grid is None:
        print("Could not build Sudoku grid from image. Exiting.")
        return

    # Step 2: Phase 1 – check satisfiability using SAT
    print("\nChecking satisfiability via SAT...")
    if is_satisfiable_via_sat(grid):
        print("RESULT: This Sudoku is SAT (at least one solution exists).")
        print("Next step: implement your own backtracking solver to find ALL solutions.")
    else:
        print("RESULT: This Sudoku is UNSAT (no solution exists).")


if __name__ == "__main__":
    main()
