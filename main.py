import tkinter as tk  # Import the tkinter library for GUI
from tkinter import messagebox, filedialog  # Import messagebox and filedialog for dialogs

# --- Rope Data Structure ---
class Rope:
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right
        self.length = (len(left) if isinstance(left, str) else left.length if left else 0) + \
                      (len(right) if isinstance(right, str) else right.length if right else 0)

    def __str__(self):
        return (str(self.left) if isinstance(self.left, Rope) else self.left or '') + \
               (str(self.right) if isinstance(self.right, Rope) else self.right or '')

    def insert(self, index, string):
        if index < self.length // 2:
            if isinstance(self.left, Rope):
                self.left.insert(index, string)
            else:
                self.left = self.left[:index] + string + self.left[index:]
        else:
            if isinstance(self.right, Rope):
                self.right.insert(index - self.length // 2, string)
            else:
                self.right = self.right[:index - self.length // 2] + string + self.right[index - self.length // 2:]

    def get_text(self):
        return str(self)

# --- Piece Table Data Structure ---
class PieceTable:
    def __init__(self, original_text):
        self.original = original_text  # Store the original text
        self.added = []  # List to store added text segments
        self.pieces = [(0, len(original_text), True)]  # Initial pieces
        self.rope = Rope(original_text, "")  # Use Rope to manage text efficiently

    def insert(self, index, text):
        self.added.append(text)  # Add to the list of added texts
        self.pieces.insert(index, (len(self.added) - 1, len(text), False))  # Create a new piece
        self.rope.insert(index, text)  # Use Rope for efficient text insertion

    def remove(self, index, text):
        # Remove text logic
        for i, (piece_index, length, is_original) in enumerate(self.pieces):
            start_index = sum(len(self.added[j]) if not self.pieces[j][2] else len(self.original[self.pieces[j][0]:self.pieces[j][1]])
                              for j in range(i))

            if start_index <= index < start_index + length:
                # Remove the piece and update the rope
                self.pieces.pop(i)
                self.rope = Rope(self.get_text()[:index], self.get_text()[index + len(text):])
                break

    def get_text(self):
        return self.rope.get_text()

# --- Stack for Undo/Redo Operations ---
class UndoRedoStack:
    def __init__(self):
        self.undo_stack = []  # Stack to store undo actions
        self.redo_stack = []  # Stack to store redo actions

    def push_undo(self, action):
        self.undo_stack.append(action)
        self.redo_stack.clear()

    def undo(self, piece_table):
        if self.undo_stack:
            action = self.undo_stack.pop()
            self.redo_stack.append(action)

            if action['type'] == 'insert':
                piece_table.remove(action['index'], action['text'])
            elif action['type'] == 'delete':
                piece_table.insert(action['index'], action['text'])
            return action
        return None

    def redo(self, piece_table):
        if self.redo_stack:
            action = self.redo_stack.pop()
            self.undo_stack.append(action)

            if action['type'] == 'insert':
                piece_table.insert(action['index'], action['text'])
            elif action['type'] == 'delete':
                piece_table.remove(action['index'], action['text'])
            return action
        return None

# --- GUI Application ---
class TextEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TEXT EDITOR")  # Set the window title
        self.root.geometry("800x600")  # Set the window size

        self.text_widget = tk.Text(root, font="Helvetica 14")
        self.text_widget.pack(expand=True, fill=tk.BOTH)  # Make the widget expand and fill the window

        self.piece_table = PieceTable("")  # Initialize Piece Table with an empty string
        self.undo_redo_stack = UndoRedoStack()  # Initialize Undo/Redo stack

        self.create_menu()  # Create the menu bar
        self.create_status_bar()  # Create the status bar

        self.previous_text = ""  # Store the previous text for tracking changes

    def create_menu(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)  # Open file
        file_menu.add_command(label="Save", command=self.save_file)  # Save file
        file_menu.add_separator()  # Separator line
        file_menu.add_command(label="Exit", command=self.root.quit)  # Exit application

        edit_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo)  # Undo action
        edit_menu.add_command(label="Redo", command=self.redo)  # Redo action

    def create_status_bar(self):
        self.status_bar = tk.Label(self.root, text="Status Bar", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def open_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not filepath:
            return
        try:
            with open(filepath, "r") as file:
                content = file.read()  # Read the content
                self.piece_table = PieceTable(content)  # Load content into Piece Table and Rope
                self.text_widget.delete(1.0, tk.END)
                self.text_widget.insert(tk.END, self.piece_table.get_text())
                self.status_bar.config(text=f"Opened: {filepath}")
                self.previous_text = self.piece_table.get_text()  # Update previous text
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")

    def save_file(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not filepath:
            return
        try:
            with open(filepath, "w") as file:
                content = self.piece_table.get_text()
                file.write(content)  # Write the modified content
                self.status_bar.config(text=f"Saved: {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def undo(self):
        action = self.undo_redo_stack.undo(self.piece_table)
        if action:
            self.update_text_widget()  # Update text widget after undo
            self.status_bar.config(text="Undid last action")

    def redo(self):
        action = self.undo_redo_stack.redo(self.piece_table)
        if action:
            self.update_text_widget()  # Update text widget after redo
            self.status_bar.config(text="Redid last action")

    def on_key_press(self, event):
        if event.char:
            current_text = self.piece_table.get_text()  # Get current text
            index = len(current_text)  # Get current text length
            self.piece_table.insert(index, event.char)  # Insert character using Piece Table and Rope
            
            # Record the action for undo
            self.undo_redo_stack.push_undo({'type': 'insert', 'index': index, 'text': event.char})
            self.update_text_widget()
            self.status_bar.config(text=f"Inserted: {event.char}")

    def update_text_widget(self):
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.END, self.piece_table.get_text())

# Main execution to start the GUI
root = tk.Tk()
app = TextEditorApp(root)
root.bind("<Key>", app.on_key_press)  # Bind key press events to the on_key_press method
root.mainloop()
