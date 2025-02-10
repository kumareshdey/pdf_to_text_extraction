import threading
import openpyxl
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import traceback
import pandas as pd
import logging
import queue
from full_implementation_1 import main

name = 'PDF extractor'
class Logger(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.textbox = tk.Text(self, width=130, height=50, state="disabled")
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.textbox.yview)
        self.textbox.config(yscrollcommand=self.scrollbar.set)
        self.textbox.tag_config("info")
        self.textbox.tag_config("error", foreground="red")
        self.textbox.pack(side="left", fill="y")
        self.scrollbar.pack(side="right", fill="y")

    def log_text(self, text: str, tag: str) -> None:
        self.textbox.config(state="normal")
        self.textbox.insert("end", f"{text}\n", tag)
        self.textbox.config(state="disabled")
        self.textbox.see(tk.END)

    def info(self, text: str) -> None:
        self.log_text(text, "info")

    def error(self, text: str) -> None:
        self.log_text(text, "error")


class TextHandler(logging.Handler):
    """A custom logging handler that sends log messages to a Tkinter Text widget."""

    def __init__(self, logger_widget):
        super().__init__()
        self.logger_widget = logger_widget

    def emit(self, record):
        msg = self.format(record)
        tag = "info" if record.levelno < logging.ERROR else "error"
        self.logger_widget.log_text(msg, tag)


class ExcelProcessorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(name)

        # Title
        self.title_label = tk.Label(root, text=name, font=("Arial", 24))
        self.title_label.pack(pady=10)

        # Input for source Excel file
        self.source_label = tk.Label(root, text="Select Source PDF File:")
        self.source_label.pack(pady=5)
        self.source_entry = tk.Entry(root, width=60)
        self.source_entry.pack(pady=5)
        self.source_button = tk.Button(root, text="Browse", command=self.browse_source_file)
        self.source_button.pack(pady=5)

        # Input for destination Excel file
        self.dest_label = tk.Label(root, text="Select Destination PDF File:")
        self.dest_label.pack(pady=5)
        self.dest_entry = tk.Entry(root, width=60)
        self.dest_entry.pack(pady=5)
        self.dest_button = tk.Button(root, text="Browse", command=self.browse_dest_file)
        self.dest_button.pack(pady=5)
        self.basic_var = tk.BooleanVar()
        self.basic_checkbox = tk.Checkbutton(root, text="Do you want basic extraction? (Faster)", variable=self.basic_var)
        self.basic_checkbox.pack(pady=5)

        # Submit button
        self.submit_button = tk.Button(root, text="Submit", command=self.process_excel)
        self.submit_button.pack(pady=20)

        # Progress bar
        self.progress = ttk.Progressbar(root, orient='horizontal', length=800, mode='determinate')
        self.progress.pack(pady=10)

        # Progress label
        self.progress_label = tk.Label(root, text="")
        self.progress_label.pack(pady=5)

        # Logging area
        self.logger_frame = Logger(root)
        self.logger_frame.pack(pady=10)

        # Configure logger
        self.logger = logging.getLogger('PDFProcessor')
        self.logger.setLevel(logging.DEBUG)

        # Create a file handler and set its level to DEBUG
        file_handler = logging.FileHandler('logs.log')
        file_handler.setLevel(logging.DEBUG)

        # Create a logging format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Set the formatter for the handler
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        self.logger.addHandler(file_handler)

        # Create a custom handler for displaying logs in the UI
        ui_handler = TextHandler(self.logger_frame)
        ui_handler.setLevel(logging.DEBUG)
        ui_handler.setFormatter(formatter)
        self.logger.addHandler(ui_handler)

        # Queue for communication between threads
        self.queue = queue.Queue()
        self.root.after(100, self.process_queue)

    def browse_source_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, file_path)

    def browse_dest_file(self):
        file_path = filedialog.askdirectory()
        if file_path:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, file_path)

    def process_excel(self):
        source_file = self.source_entry.get()
        dest_file = self.dest_entry.get()
        basic = self.basic_var.get()
        print(basic)

        if not source_file or not dest_file:
            messagebox.showerror("Error", "Please select both source and destination files")
            return

        threading.Thread(target=self.process_excel_thread, args=(source_file, dest_file, basic)).start()

    def process_excel_thread(self, source_file, dest_file, basic):
        try:
            self.queue.put(('submit_button', 'disabled'))
            self.queue.put(('progress', 0))
            self.queue.put(('progress_label', "0% (0/0)"))
            self.logger.info(f"Starting PDF extraction. Source path: {source_file}. Dest path: {dest_file}")
            main(source_file, dest_file, self.logger, self.queue, basic)
            # # Read the source Excel file
            # df = pd.read_excel(source_file)
            # total_rows = len(df)
            # self.logger.info(f"Total rows to process: {total_rows}")
            # df.columns = ["FIRST_NAME", "LAST_NAME", "STREET", "CITY", "DIST", "ZIP"]

            # for index, row in df.iterrows():
            #     df = process_row(row, dest_file, self.logger)

            #     while True:
            #         try:
            #             df.to_excel(dest_file, index=False)
            #             break
            #         except PermissionError:
            #             result = messagebox.askretrycancel("Error", "Updating excel could not be possible. Please close the file if you are viewing")
            #             if not result:
            #                 raise

            #     progress_percentage = (index + 1) / total_rows * 100
            #     self.queue.put(('progress', progress_percentage))
            #     self.queue.put(('progress_label', f"{progress_percentage:.2f}% ({index + 1}/{total_rows})"))

            self.logger.info("PDF extraction completed.")
            self.queue.put(('messagebox', ('info', "PDF extraction completed successfully.")))
        except Exception as e:
            self.logger.error("Error occurred: %s", str(e))
            self.logger.error(traceback.format_exc())
            self.queue.put(('messagebox', ('error', str(e))))
        finally:
            self.queue.put(('submit_button', 'normal'))
            self.queue.put(('progress', 100))
            self.queue.put(('quit',))

    def process_queue(self):
        while not self.queue.empty():
            msg = self.queue.get()
            if msg[0] == 'submit_button':
                self.submit_button.config(state=msg[1])
            elif msg[0] == 'progress':
                self.progress['value'] = msg[1]
            elif msg[0] == 'progress_label':
                self.progress_label.config(text=msg[1])
            elif msg[0] == 'messagebox':
                if msg[1][0] == 'info':
                    messagebox.showinfo("Info", msg[1][1])
                elif msg[1][0] == 'error':
                    messagebox.showerror("Error", msg[1][1])
            elif msg[0] == 'quit':
                self.root.quit()
        self.root.after(100, self.process_queue)


if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelProcessorApp(root)
    root.mainloop()

