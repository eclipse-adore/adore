#!/usr/bin/env python3

import subprocess
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

def run_git_command(args):
    result = subprocess.run(["git"] + args, capture_output=True, text=True)
    print ("git " + " ".join(args))
    if result.returncode != 0:
        messagebox.showerror("Git Error", result.stderr)
        sys.exit(1)
    return result.stdout.strip()

def get_diff_files(branch):
    return run_git_command(["diff", "--name-only", branch]).splitlines()

class FileTreeGUI:
    def __init__(self, root, files, branch):
        self.root = root
        self.branch = branch
        self.root.title(f"Checkout files from '{branch}'")
        self.root.geometry("700x500")

        self.tree = ttk.Treeview(root)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=10, pady=10)

        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_vars = {}  # file path → BooleanVar

        self.insert_files(files)

        btn = ttk.Button(root, text="Checkout Selected Files", command=self.on_confirm)
        btn.pack(pady=5)

    def insert_files(self, files):
        for file_path in files:
            parts = file_path.split('/')
            current_parent = ""
            full_path = ""
            for i, part in enumerate(parts):
                full_path = os.path.join(full_path, part) if full_path else part
                if full_path not in self.file_vars:
                    is_file = (i == len(parts) - 1)
                    var = tk.BooleanVar()
                    self.file_vars[full_path] = var
                    node_id = self.tree.insert(current_parent, "end", iid=full_path, text=part, open=False)
                    self.tree.item(node_id, tags=("file" if is_file else "folder",))
                current_parent = full_path

        # Add checkboxes manually using tags
        self.tree.tag_configure("file")
        self.tree.bind("<ButtonRelease-1>", self.on_click)

    def on_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        path = item
        var = self.file_vars.get(path)
        if var is None:
            return

        new_val = not var.get()
        self.set_checked_recursively(path, new_val)
        self.update_checkbox_labels()
    
    def update_checkbox_labels(self):
        for path, var in self.file_vars.items():
            part = os.path.basename(path)
            prefix = "[x]" if var.get() else "[ ]"
            self.tree.item(path, text=f"{prefix} {part}")



    def set_checked_recursively(self, item, value):
        var = self.file_vars.get(item)
        if var is not None:
            var.set(value)

        for child in self.tree.get_children(item):
            self.set_checked_recursively(child, value)

    def get_selected_files(self):
        return [path for path, var in self.file_vars.items()
                if var.get() and not self.tree.get_children(path)]  # only leaf nodes (files)

    def on_confirm(self):
        selected = self.get_selected_files()
        if not selected:
            messagebox.showinfo("No Selection", "No files selected.")
            return

        confirm = messagebox.askyesno("Confirm Checkout", f"Checkout {len(selected)} file(s) from '{self.branch}'?")
        if confirm:
            for file in selected:
                run_git_command(["checkout", self.branch, "--", file])
            messagebox.showinfo("Done", "Files checked out successfully.")
            self.root.destroy()

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <branch>")
        sys.exit(1)

    branch = sys.argv[1]
    files = get_diff_files(branch)

    if not files:
        print("No differing files found.")
        sys.exit(0)

    root = tk.Tk()
    FileTreeGUI(root, files, branch)
    root.mainloop()

if __name__ == "__main__":
    main()
