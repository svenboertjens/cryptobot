import threading
import logger
import os


# This file allows access to files, with safety over threads.


class Queue():
    entries = {}
    
    # Dict of extensions and their basic content
    extensions = {
        "json": "{\n\t\n}",
        # Add more file types here later
    }
    
    def _get_standard_text(self, ext: str):
        if ext == "" or ext not in self.extensions:
            return ""
    
    def _add_entry(self, file_path: str, full_path: str):
        try:
            # Check whether the entry exists. If not, add it
            if full_path not in self.entries:
                self.entries[full_path] = []
            # Check whether the file exists. If not, create it
            if not os.path.exists(file_path):
                with open(file_path, "w") as file:
                    _, ext = os.path.splitext(file_path)
                    ext = ext[1:]
                    if ext != "" and ext in self.extensions:
                        file.write(self.extensions[ext])
                        
        except Exception as e:
            logger.log(f"An exception occurred while trying to add a file entry. Error message: {str(e)}", "error")
            
    def _queue_entry(self, file_path: str, event: threading.Event):
        try:
            # Create a function to be called when the queue position is 0
            def queue():
                # Set the threading event
                event.set()
                
            # Create and return a function to be called when file operations are done
            def finished():
                # Remove self, which is position 0
                self.entries[file_path].pop(0)
                # Call the function that's queued at 0 now, if exists
                if len(self.entries[file_path]) > 0:
                    self.entries[file_path][0]()
                
            # Add the function to the queue
            self.entries[file_path].append(queue)
            
            # Automatically set the event if there's no others in line
            if len(self.entries[file_path]) == 1:
                event.set()
            
            return finished
        except Exception as e:
            logger.log(f"An exception occurred while trying to queue a file entry. Error message: {str(e)}", "error")
            
    def attempt_entry(self, file_path: str, timeout: float = 10):
        try:
            # Get the full path
            full_path = os.path.abspath(file_path)
            # Add the entry if it doesn't exist yet
            if full_path not in self.entries:
                self._add_entry(file_path, full_path)
                
            # Create a threading event and send it along
            event = threading.Event()
            finished = self._queue_entry(full_path, event)
            # Wait until the event is set and continue
            event.wait(timeout)
            # Return the function to be called when finished
            return finished
        except Exception as e:
            logger.log(f"An exception occurred while trying to verify a file entry queue. Error message: {str(e)}", "error")


queue = Queue()

