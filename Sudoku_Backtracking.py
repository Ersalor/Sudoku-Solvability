# Sudoku_Backtracking.py

def is_safe(grid, row, col, num):
    """Check if 'num' can be placed in (row,col)."""

    # Row check
    for j in range(9):
        if grid[row][j] == num:
            return False

    # Column check
    for i in range(9):
        if grid[i][col] == num:
            return False

    # 3x3 block check
    start_row = (row // 3) * 3
    start_col = (col // 3) * 3

    for i in range(start_row, start_row + 3):
        for j in range(start_col, start_col + 3):
            if grid[i][j] == num:
                return False

    return True


def find_empty(grid):
    """Find next empty cell, or (None,None)."""
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                return i, j
    return None, None


def copy_grid(grid):
    """Deep copy grid."""
    return [row[:] for row in grid]


def solve_all_solutions(grid):
    """Return a list of ALL valid Sudoku solutions."""
    solutions = []
    solve_recursive(grid, solutions)
    return solutions


def solve_recursive(grid, solutions):
    row, col = find_empty(grid)

    if row is None:
        # No empty cells left → one complete solution
        solutions.append(copy_grid(grid))
        return

    for num in range(1, 10):
        if is_safe(grid, row, col, num):
            grid[row][col] = num
            solve_recursive(grid, solutions)
            grid[row][col] = 0  # backtrack
