# Sudoku_GUI.py

import tkinter as tk
from tkinter import filedialog, messagebox

from Sudoku_Core import image_to_sudoku_grid, solve_sudoku_from_grid


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

        # 1) Sadece OCR yapan buton
        btn_load = tk.Button(top, text="Load Image (OCR)", command=self.load_image_only)
        btn_load.pack(side=tk.LEFT)

        # 2) Şu an ekrandaki grid'den çözen buton
        btn_solve = tk.Button(top, text="Solve Current Grid", command=self.solve_from_gui)
        btn_solve.pack(side=tk.LEFT, padx=5)

        self.status = tk.Label(top, text="Waiting for input...")
        self.status.pack(side=tk.LEFT, padx=10)

        # Sudoku board (Entry'ler)
        board = tk.Frame(self.root)
        board.pack()

        self.cells = []
        for i in range(9):
            row = []
            for j in range(9):
                entry = tk.Entry(
                    board,
                    width=2,
                    font=("Consolas", 18),
                    justify="center",
                    borderwidth=1,
                    relief="solid"
                )
                entry.grid(row=i, column=j, padx=1, pady=1)
                row.append(entry)
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

    # ==========================
    # 1) OCR: resmi okuyup grid göster
    # ==========================

    def load_image_only(self):
        """
        Sadece resmi seçer, OCR ile grid'i okur ve GUI'de gösterir.
        Henüz çözüm üretmez. Çözmek için kullanıcı 'Solve Current Grid'e basar.
        """
        path = filedialog.askopenfilename(
            title="Select Sudoku Image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if not path:
            return

        self.status.config(text="Reading grid from image...")
        self.root.update()

        grid = image_to_sudoku_grid(path)

        if grid is None:
            messagebox.showerror("Error", "Could not read Sudoku from image.")
            self.status.config(text="Failed.")
            return

        # OCR'den gelen grid'i göster ve kullanıcıya düzeltme şansı ver
        self.grid = grid
        self.solutions = []
        self.index = 0

        self.display_grid(grid)
        self.update_nav()  # çözümler boş, navigation disable olacak

        self.status.config(text="Grid loaded. You can edit the cells, then click 'Solve Current Grid'.")

    # ==========================
    # 2) GUI'deki grid'den çöz
    # ==========================

    def solve_from_gui(self):
        """
        Şu an GUI'de görünen (Entry'lerde yazan) grid'i alır ve çözer.
        """
        # 1) Entry'lerden 9x9 grid'i oku
        grid = []
        for i in range(9):
            row = []
            for j in range(9):
                text = self.cells[i][j].get().strip()
                if text == "":
                    row.append(0)
                elif text.isdigit():
                    v = int(text)
                    if 0 <= v <= 9:
                        row.append(v)
                    else:
                        # 0-9 dışı girilmişse 0 sayalım
                        row.append(0)
                else:
                    # Rakam değilse 0
                    row.append(0)
            grid.append(row)

        self.grid = grid

        self.status.config(text="Solving current grid...")
        self.root.update()

        # 2) Core fonksiyonla çöz
        grid, solutions = solve_sudoku_from_grid(grid)

        self.solutions = solutions
        self.index = 0

        if not solutions:
            self.status.config(text="UNSAT - No solution found for this grid.")
            self.display_grid(grid)
            self.update_nav()
            return

        self.status.config(text=f"{len(solutions)} solution(s) found.")
        self.display_grid(solutions[0])
        self.update_nav()

    # ==========================
    # Yardımcı GUI fonksiyonları
    # ==========================

    def display_grid(self, grid):
        """
        grid'deki değerleri Entry'lere yaz.
        0 olan hücreler boş bırakılır (görünür 0 yok).
        """
        for i in range(9):
            for j in range(9):
                val = grid[i][j]
                entry = self.cells[i][j]
                entry.delete(0, tk.END)
                if val != 0:
                    entry.insert(0, str(val))

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
