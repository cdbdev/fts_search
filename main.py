import logging
import queue
import tkinter as tk
import subprocess
from tkinter import ttk
from tkinter.messagebox import showwarning
from tkinter.filedialog import askdirectory

from process_executor import PyProcessExecutor

class GuiBuilder():
    """ Create the main application window and start the GUI loop
    
    Attributes:
        root (tkinter.Tk): contains the tkinter root window  
    """
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ftsSearch - Search for text in files")
        self.root.geometry("{}x{}+{}+{}".format(1200, 640, 40, 40))
        self.root.configure(bg='white')
        self.root.resizable(0,0)
    
    def create(self):
        app = Application(master = self.root)
        app.mainloop()


class Application(tk.Frame):
    """ Create widgets inside a window

    Attributes:
        master (tkinter.Tk)
        q (queue.Queue)
        results (list)
        cancelled (bool)
        lf_search (tk.LabelFrame)
        lbl_search_path (tk.Label)
        txt_search_path (tk.Entry)
        btn_file_chooser (tk.Button)
        lbl_file_types (tk.Label)
        txt_file_types (tk.Entry)
        lbl_search_text (tk.Label)
        txt_search_text (tk.Entry)
        btn_search (tk.Button)
        btn_cancel (tk.Button)
        cnt_treeview (TreeViewContainer)
        cnt_text (TextContainer)
        lbl_status (tk.Label)
    Args:
        master (tk.Tk)
    """
    
    # Constants
    START_DIR = "C:\\"
    FILE_TYPES = "*.md"
    #~ FILE_TYPES = "*.md,*.markdown,*.txt"
    DELAY = 100

    X_PAD_ZERO = (0, 0)
    X_PAD_LEFT = (20, 0)
    X_PAD_RIGHT = (0, 20)
    X_PAD_LR = (20,20)
    X_PAD_LBL = (10,10)
    X_PAD_LBL_L = (100,10)
    Y_PAD_TOP = (10, 0)
    Y_PAD_TOP_BOT = (10, 10)
    Y_PAD_BOTTOM = (0, 10)

    # Methods    
    def __init__(self, master: tk.Tk = None):
        super().__init__(master)

        self.master = master
        self.create_widgets()
        self.q = queue.Queue()
        self.results = []
        self.cancelled = False

    def create_widgets(self):
        # ================
        # Search Frame
        # ================
        
        # Search: LabelFrame
        self.lf_search = tk.LabelFrame(self.master, text= "Search")
        self.lf_search.grid(row = 0, column = 0, sticky="WE", columnspan = 5, padx = Application.X_PAD_LR , pady = Application.Y_PAD_TOP)
        self.lf_search.configure(bg='white')

        # Path: Label + Entry + Button
        self.lbl_search_path = tk.Label(self.lf_search, text = "Path:")
        self.lbl_search_path.grid(row = 0, column = 0, sticky="W", padx = Application.X_PAD_LBL, pady = Application.Y_PAD_TOP)
        self.lbl_search_path.configure(bg='white')

        self.txt_search_path = tk.Entry(self.lf_search, width = 120)
        self.txt_search_path.insert(tk.END, Application.START_DIR)
        self.txt_search_path.grid(row = 0, column = 1, sticky="W", padx = Application.X_PAD_ZERO, pady = Application.Y_PAD_TOP)
        self.txt_search_path.configure(state = "disabled")

        self.btn_file_chooser = tk.Button(self.lf_search, text = "...", command = self.on_file_choose , relief = tk.GROOVE, height = 1)
        self.btn_file_chooser.grid(row = 0, column = 2, sticky="W", padx = Application.X_PAD_RIGHT, pady = Application.Y_PAD_TOP)

        # Filetype: Label + Entry
        self.lbl_file_types = tk.Label(self.lf_search, text = "File Types:")
        self.lbl_file_types.grid(row = 0, column = 2, sticky="W", padx = Application.X_PAD_LBL_L, pady = Application.Y_PAD_TOP)
        self.lbl_file_types.configure(bg='white')

        self.txt_file_types = tk.Entry(self.lf_search, width = 30)
        self.txt_file_types.insert(tk.END, Application.FILE_TYPES)
        self.txt_file_types.configure(state = "disabled")
        self.txt_file_types.grid(row = 0, column = 3, sticky="W", columnspan = 2, padx = Application.X_PAD_RIGHT, pady = Application.Y_PAD_TOP)

        # Search text: Label + Entry
        self.lbl_search_text = tk.Label(self.lf_search, text = "Text:")
        self.lbl_search_text.grid(row = 1, column = 0, sticky="W", padx = Application.X_PAD_LBL, pady = Application.Y_PAD_TOP_BOT)
        self.lbl_search_text.configure(bg='white')

        self.txt_search_text = tk.Entry(self.lf_search, width = 100)
        self.txt_search_text.focus_set()
        self.txt_search_text.grid(row = 1, column = 1, sticky="W", columnspan = 3, padx = Application.X_PAD_RIGHT, pady = Application.Y_PAD_TOP_BOT)
        self.txt_search_text.configure(bg='white')

        # Search: Button
        self.btn_search = tk.Button(self.lf_search, text = "Search", command = self.on_search, width = 8)
        self.btn_search.grid(row = 1, column = 3, sticky="W", padx = Application.X_PAD_RIGHT, pady = Application.Y_PAD_TOP_BOT)
        self.master.bind("<Return>", self.on_search_enter)
        
        # Cancel: Button
        self.btn_cancel = tk.Button(self.lf_search, text = "Cancel", command = self.on_cancel , width = 8, relief = tk.GROOVE )
        self.btn_cancel.grid(row = 1, column = 3, sticky="E", padx = Application.X_PAD_LEFT, pady = Application.Y_PAD_TOP_BOT)
        self.btn_cancel.configure(state = "disabled")

        # =============================================
        # Table (TreeView) inside Frame with results
        # =============================================

        self.cnt_treeview = TreeViewContainer(self.master)
        self.cnt_treeview.grid(row = 4, column = 0, columnspan = 5, padx = Application.X_PAD_LR, pady = Application.Y_PAD_TOP, sticky = "WE")
        self.cnt_treeview.bind_single_click(self.on_select_item)
        #~ self.cnt_treeview.bind_double_click(self.on_double_click_item)
        
        # =====================================================
        # Text inside Frame with found text in selected file
        # =====================================================

        self.cnt_text = TextContainer(self.master)
        self.cnt_text.grid(row=6, column=0,  columnspan = 5, padx = Application.X_PAD_LR, pady = Application.Y_PAD_TOP, sticky = "WE")

        # =============
        # Status bar
        # =============
        self.lbl_status = tk.Label(self.master, text = "Ready")
        self.lbl_status.grid(row = 7, column = 0, sticky="W", padx = Application.X_PAD_LR, pady = Application.Y_PAD_TOP)
        self.lbl_status.config(bg = "orange")        
    
    def on_file_choose(self):
        filename = askdirectory()
        
        if filename:
            self.txt_search_path.configure(state = "normal")
            self.txt_search_path.delete(0,tk.END)  
            self.txt_search_path.insert(tk.END, filename)
            self.txt_search_path.configure(state = "disabled")

    def on_search(self):
        invalid_input = self.check_input()

        if not invalid_input:
            # Refresh result
            self.results.clear()

            # Refresh TreeView
            self.cnt_treeview.tvw_results.delete(*self.cnt_treeview.tvw_results.get_children())
            self.cnt_treeview.apply_width(0)

            # Refresh text output
            self.cnt_text.refresh()

            # Call Executor            
            input = (self.txt_search_path.get(), self.txt_file_types.get(), self.txt_search_text.get())
            self.executor = PyProcessExecutor(input, self.q)
            self.executor.start()

            # Prepare GUI for result
            self.toggle_search()
            self.update_status("Searching...")
            self.master.after(Application.DELAY, self.on_after_elapsed)
        else:
            showwarning("Check input!", invalid_input)

    def on_search_enter(self, event: tk.Event):
        """
        Args:
            event (tk.Event)
        """
        self.on_search()

    def on_cancel(self):
        self.executor.stop()
        self.cancelled = True
        self.update_status("Search cancelled.")

    def on_after_elapsed(self):
        """ Retrieve results from thread and display results

            This method checks periodically, after DELAY time, if the launched thread is finished.
            When finished, the queue from this thread is read.

            Cancelling can occur in the following 2 cases:
                - Before the thread is finished
                - While reading out the queue
        """
        # Check for cancel in case thread not yet finished
        if self.cancelled == True:
            self.q.queue.clear()
            self.toggle_search()            
            return

        # Only read queue when thread is done
        if not self.executor.is_alive():
            max_length = 0

            try:
                for data in iter(self.q.get_nowait, PyProcessExecutor.SENTINEL):
                    # Check for cancel while reading out queue
                    if self.cancelled == True:
                        self.q.queue.clear()
                        self.toggle_search()            
                        return

                    # Insert data into TreeView and result
                    self.results.append(data)
                    self.cnt_treeview.insert(parent = "", index = tk.END, text = data.key)
                        
                    self.cnt_treeview.update()

                    # Determine max length of TreeView to determine largest entry
                    if len(data.key) > max_length:
                        max_length = len(data.key)

                # Queue succesfully read until the end ('Sentinel' result is reached)
                self.toggle_search()
                self.update_status(f"Search done (matches: { len(self.cnt_treeview.tvw_results.get_children()) })")
                self.cnt_treeview.apply_width(max_length)

                return
            except queue.Empty:
                self.update_status("Search failed.")
                return

        self.master.after(Application.DELAY, self.on_after_elapsed)

    def on_select_item(self, event: tk.Event):
        current_key = self.cnt_treeview.get_current_item().get("text")
        self.cnt_text.file = current_key.replace("\\","/")
        
        for data in self.results:
            if data.key == current_key:
                self.cnt_text.insert_text(data.dat)                
                break
        
        self.cnt_text.highlight_text(self.txt_search_text.get())

    def toggle_search(self):
        if self.btn_search['state'] == "disabled":
            self.btn_search.configure(state = "normal")
            self.btn_cancel.configure(state = "disabled")
            self.cancelled = False
        else:
            self.btn_search.configure(state = "disabled")
            self.btn_cancel.configure(state = "normal")

    def update_status(self, status: str):
        """
        Args:
            status (str)
        """
        self.lbl_status.config(text = status)

    def check_input(self) -> str:
        """If input is OK return empty, else return error"""
        
        if len(self.txt_search_path.get()) == 0:
            return "Enter a search path."

        if len(self.txt_search_text.get()) < 3:
            return "A text string of at least 3 characters is required."
            
        if len(self.txt_file_types.get()) == 0:
            return "At least 1 file type has to be provided."
            
        return ""


class TreeViewContainer(tk.Frame):
    """ Class to create a TreeView inside a Frame

    Remarks: 
        Content in a treeview column is allowed to be wider than the column. You can see that if you grab the column edge on 
        the header bar and drag it around. So to change the width of a column, you need to set the minwidth, not the width, or 
        write some code that will adjust the column width to match the content.

        In this example we use the font 'Consolas' for the content as this is a 'Monospaced' font which makes the calculation of the
        width easier. 

    Attributes:
        tvw_results (ttk.Treeview): TreeView component
    """
    CHAR_WIDTH = 7.2 # Approx. width for Consolas 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.configure(bg='white')

        # Treeview style (Important: use a monospaced font like 'Consolas' -> for use with calculation of minwidth)
        style = ttk.Style()
        style.configure("mystyle.Treeview.Heading", font=("Calibri", 13,"bold italic")) # Modify the font of the headings
        style.configure("mystyle.Treeview", font=("Consolas", 10)) # Modify the font of the body

        # The actual TreeView
        self.tvw_results = ttk.Treeview(self, style = "mystyle.Treeview")
        self.insert = self.tvw_results.insert
        self.move = self.tvw_results.move
        
        self.tvw_results.grid(row = 0, column = 0, sticky="NSEW")
        self.tvw_results.column("#0", minwidth = 0, stretch = tk.YES)
        self.tvw_results.heading("#0", text = "Found results", anchor = tk.W, command = lambda : self.treeview_sort(True))

        # Scrollbars + attach scrollbars to TreeView
        sb_vertical = tk.Scrollbar(self, orient = "vertical", command = self.tvw_results.yview)
        sb_horizontal = tk.Scrollbar(self, orient = "horizontal", command = self.tvw_results.xview)
        self.tvw_results.configure(yscrollcommand = sb_vertical.set, xscrollcommand = sb_horizontal.set)
        sb_vertical.grid(row = 0, column = 1, sticky = "NS")
        sb_horizontal.grid(row = 1, column = 0, sticky = "EW")

        # Configure and position grid for TreeView
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

    def apply_width(self, width: int):
        # Take the TreeView width minus 2 for the boundaries
        self.tvw_results.column("#0", width = self.tvw_results.winfo_width() -2, minwidth = int(width * TreeViewContainer.CHAR_WIDTH))

    def bind_single_click(self, method):
        # Note that the callback will be executed before the focus in the tree changed, i.e. you will get the item that was selected before 
        # you clicked the new item. One way to solve this is to use the event type ButtonRelease instead.
        self.tvw_results.bind("<ButtonRelease-1>", method)
        
    def treeview_sort(self, reverse):
        col = "#0"
        
        l = [(self.tvw_results.item(k)["text"], k) for k in self.tvw_results.get_children()]
        l.sort(reverse = reverse)
        
        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self.tvw_results.move(k, '', index)
            
        # Reset heading action after sort
        self.tvw_results.heading(col, command = lambda: self.treeview_sort(not reverse))

    def get_current_item(self) -> ttk.Treeview.item:
        current_item = self.tvw_results.focus()
        return self.tvw_results.item(current_item)


class TextContainer(tk.Frame):
    """ Class to create a Text component inside a Frame

    Attributes:
        txt_display (tk.Text): TreeView component
    """    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.txt_display = tk.Text(self, width = 24, height = 13, wrap = "none", borderwidth = 1)
        self.txt_display.configure(state = 'disabled')
        self.txt_display.grid(row = 0, column = 0, sticky = "NSEW")
        self.txt_display.bind("<Button-1>", self.on_single_click)
        self.txt_display.bind("<Double-Button-1>", self.on_double_click)
        self.txt_display.configure(bg='white')
        self.file = ""


        # Scrollbars + attach scrollbars to Text
        sb_vertical = tk.Scrollbar(self, orient = "vertical", command = self.txt_display.yview)
        sb_horizontal = tk.Scrollbar(self, orient = "horizontal", command = self.txt_display.xview)
        self.txt_display.configure(yscrollcommand = sb_vertical.set, xscrollcommand = sb_horizontal.set)
        sb_vertical.grid(row = 0, column = 1, sticky = "NS")
        sb_horizontal.grid(row = 1, column = 0, sticky = "EW")

        # Configure and position grid for TreeView
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

    def insert_text(self, text: list[str]):
        """ Remarks:
            - We need to enable the widget to be able to insert text.
            - Clear the widget before a new insert
        """
        self.txt_display.configure(state = "normal")
        self.txt_display.delete('1.0',tk.END)

        for txt in text:
            self.txt_display.insert(tk.END, txt)        
                
        self.txt_display.configure(state = "disabled")

    def refresh(self):
        self.txt_display.configure(state='normal')
        self.txt_display.delete('1.0',tk.END)  
        self.txt_display.configure(state='disabled')

    def highlight_text(self, keyword: str):
        self.txt_display.tag_remove("found", '1.0', tk.END)
        
        idx = '1.0'
        while idx:
            idx = self.txt_display.search(keyword, idx, nocase = 1, stopindex = tk.END)
            if idx:
                lastidx = '%s+%dc' % (idx, len(keyword))
                self.txt_display.tag_add("found", idx, lastidx)
                idx = lastidx

        self.txt_display.tag_config("found", background="yellow", foreground="black")
        
    def get_current_line(self) -> (int, int):
        # Retrieve line based on cursor position
        begin_pos = self.txt_display.index("current linestart")
        end_pos = self.txt_display.index("current lineend")
        return (begin_pos, end_pos)
        
    def get_current_line_txt(self) -> str:
        # Retrieve text based on cursor position
        position = self.get_current_line()
        return self.txt_display.get(position[0], position[1])
        
    def on_single_click(self,key):
        # Highlight current selected line
        position = self.get_current_line()
        self.txt_display.tag_remove("current", '1.0', tk.END)
        self.txt_display.tag_add("current", position[0], "current lineend+1c")
        self.txt_display.tag_config("current", background="lightblue", foreground="black")
        
    def on_double_click(self, key):
        txt = self.get_current_line_txt()
        
        if txt:
            # Get line number (index before ':')
            colon_idx = txt.find(":")
            line_number = txt[0:colon_idx]            
            subprocess.Popen(["C:/myapps/wscite/SciTE.exe", self.file,"-goto:" + line_number])


# Main processing
if __name__ == "__main__":
	# Log everything to file
	logging.basicConfig(filename = 'error.log', encoding = 'utf-8', format = '%(asctime)s %(levelname)-8s %(message)s', datefmt = '%Y-%m-%d %H:%M:%S', level = logging.DEBUG)
	logger = logging.getLogger(__name__)
	
	#~ logger.debug("Main started")
		
	guiBuilder = GuiBuilder()
	guiBuilder.create()
