import tkinter as tk
from tkinter import filedialog
import os
BASE_DIR = os.getcwd()

class Application(tk.Frame):
    def __init__(self, title, master = None):
        tk.Frame.__init__(self, master)
        self.grid()
        self.createWidgets()
        self.master.title(title)
        self.master.eval('tk::PlaceWindow . center')
        self.output_text = ""
        self.curr_file = ""

    def createWidgets(self):
        # make file picker
        self.filePickLabel = tk.Label(self, text = "Select a file to enable data import and analysis.")
        self.filePickLabel.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        self.filePickLabel.config(font=("Verdana", 10),fg="#000000")
        self.filePickButton = tk.Button(self, text = "Select File",command = self.start_file_picker,state = tk.NORMAL)
        self.filePickButton.grid(row=1, column=2, padx=10, pady=10)
        self.filePickButton.config(bg="#FF0000",font=("Verdana", 10))
        # display picked filename
        self.outputLabel = tk.Label(self, text = "File path: ")
        self.outputLabel.grid(row=2, column=0, padx=10, pady=10)
        self.outputLabel.config(font=("Verdana", 10),fg="#FF0000")
        self.outputMessage = tk.Label(self, text = "")
        self.outputMessage.grid(row=2, column=1, columnspan=2, padx=10, pady=10)
        self.outputMessage.config(font=("Verdana", 10),fg="#000000")

    def start_file_picker(self):
        # self.clear_error_text()
        # self.withdraw()
        self.curr_file = filedialog.askopenfilename(initialdir=BASE_DIR)
        self.outputMessage.config(text=self.curr_file)

def test_file_picking():
    app_title = 'File Selector Test'
    app = Application(app_title)
    app.mainloop()
    assert app.curr_file != "", "no filepath stored"

if __name__ == "__main__":
    test_file_picking()