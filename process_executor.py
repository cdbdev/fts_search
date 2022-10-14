import threading
import glob
import queue
import logging

from process_result import ProcessResult

class PyProcessExecutor(threading.Thread):
    """ Execute the search in a separate Thread

    Attributes:
        _path (str): contains filename + path
        _file_type (str): search in files with specified file types only
        _txt (str): text to search for
        _q (queue.Queue): Object to share 'Thread-safe' data between threads
        _stop_event (threading.Event): used to indicate thread should be stopped
        logger (Logger)
    Args:
        input (tuple[str,str,str])
        q (queue.Queue)
    """

    SENTINEL = ProcessResult("_end", [])

    def __init__(self, input: tuple[str,str,str], q: queue.Queue):
        super(PyProcessExecutor, self).__init__(daemon = True)
        
        self._path = input[0]
        self._file_type = input[1]
        self._txt = input[2]

        self._q = q
        self._stop_event = threading.Event()

        # Logging config
        self.logger = logging.getLogger(__name__)

    def run(self):
        files = []
        
        #~ self.logger.debug("run started")

        # Split file types
        ftypes = self._file_type.split(",")        
        types = [self._path + "/**/" + ftype for ftype in ftypes]

        # Search files recursively based on filetype
        for type in types:
            if self.stopped(): # Handle STOP
                return
            
            for found in glob.glob(type, recursive = True):
                files.append(found)

        # Process found files
        for file in files:
            if self.stopped(): # Handle STOP
                return
            
            result = self._process_file(file)
            if result is not None:
                self._q.put(result)

        # Indicate end of result 
        self._q.put(PyProcessExecutor.SENTINEL)  

    def stop(self):
        self._stop_event.set()
    
    def stopped(self):
        return self._stop_event.is_set()

    def _process_file(self, file: str) -> ProcessResult:
        found_text = []        

        search_param = self._txt

        # If the specified filepath contains the search pattern, add it to the results
        if file.find(search_param) != -1:
            found_text.append("<<text found in path>>\n")
        
        linenumber = 0
        with open(file, "r", encoding = "utf8") as reader:
            while True:
                try:
                    line = reader.readline()
                    linenumber += 1
                    
                    if line == '':
                        break                        
                    
                    # Ignore case
                    if search_param.lower() in line.lower():
                        found_text.append(str(linenumber) + ": " + line)
                except UnicodeDecodeError as e:
                    # Log error for current file, but continue with the rest
                    self.logger.error(f"Error while reading file [{file}]: {e}")

        # Only return result if the file contains the search pattern in the text or filename
        if len(found_text) > 0:
            return ProcessResult(file, found_text)
        else:
            return None
