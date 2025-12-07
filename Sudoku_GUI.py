# sudoku_gui.py

import tkinter as tk
from tkinter import filedialog, messagebox

from Sudoku_Core import solve_sudoku_from_image


class SudokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Solver")

        self.grid = None
        self.solutions = []
        self.index = 0

        self.build_ui()

    def build_ui(self):
        # Top controls
        top = tk.Frame(self.root)
        top.pack(pady=10)

        btn = tk.Button(top, text="Load Image & Solve", command=self.load_and_solve)
        btn.pack(side=tk.LEFT)

        self.status = tk.Label(top, text="Waiting for input...")
        self.status.pack(side=tk.LEFT, padx=10)

        # Sudoku board
        board = tk.Frame(self.root)
        board.pack()

        self.cells = []
        for i in range(9):
            row = []
            for j in range(9):
                lbl = tk.Label(
                    board, text="", width=3, height=1,
                    font=("Consolas", 18),
                    borderwidth=1, relief="solid"
                )
                lbl.grid(row=i, column=j, padx=1, pady=1)
                row.append(lbl)
            self.cells.append(row)

        # Navigation
        nav = tk.Frame(self.root)
        nav.pack(pady=10)

        self.btn_prev = tk.Button(nav, text="<< Prev", command=self.prev_solution, state=tk.DISABLED)
        self.btn_prev.pack(side=tk.LEFT)

        self.info = tk.Label(nav, text="Solution 0 / 0")
        self.info.pack(side=tk.LEFT, padx=10)

        self.btn_next = tk.Button(nav, text="Next >>", command=self.next_solution, state=tk.DISABLED)
        self.btn_next.pack(side=tk.LEFT)

    def load_and_solve(self):
        path = filedialog.askopenfilename(
            title="Select Sudoku Image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if not path:
            return

        self.status.config(text="Solving... please wait.")
        self.root.update()

        grid, solutions = solve_sudoku_from_image(path)

        if grid is None:
            messagebox.showerror("Error", "Could not read Sudoku from image.")
            self.status.config(text="Failed.")
            return

        self.grid = grid
        self.solutions = solutions
        self.index = 0

        if not solutions:
            self.status.config(text="UNSAT - No solution found.")
            self.display_grid(grid)
            self.update_nav()
            return

        self.status.config(text=f"{len(solutions)} solution(s) found.")
        self.display_grid(solutions[0])
        self.update_nav()

    def display_grid(self, grid):
        for i in range(9):
            for j in range(9):
                val = grid[i][j]
                self.cells[i][j].config(text="" if val == 0 else str(val))

    def update_nav(self):
        total = len(self.solutions)

        if total == 0:
            self.info.config(text="Solution 0 / 0")
            self.btn_prev.config(state=tk.DISABLED)
            self.btn_next.config(state=tk.DISABLED)
            return

        self.info.config(text=f"Solution {self.index + 1} / {total}")
        self.btn_prev.config(state=tk.NORMAL if self.index > 0 else tk.DISABLED)
        self.btn_next.config(state=tk.NORMAL if self.index < total - 1 else tk.DISABLED)

    def prev_solution(self):
        if self.index > 0:
            self.index -= 1
            self.display_grid(self.solutions[self.index])
            self.update_nav()

    def next_solution(self):
        if self.index < len(self.solutions) - 1:
            self.index += 1
            self.display_grid(self.solutions[self.index])
            self.update_nav()


def main():
    root = tk.Tk()
    SudokuGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
