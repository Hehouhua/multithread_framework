import Queue
import re,sys,time,datetime,os.path
import threading
from optparse import OptionParser
from lib.consle_width import getTerminalSize
import file
ext=['jpg','png','gif','tar','gzip','rar','zip','7z','gz','bz2','doc','docx','pdf','py','pyc','pyo','ppt','pptx','mp3','mp4','avi','wav']
result_file="./search_log"
class Search:
    def __init__(self,target,threads_count,regex):
        self.target=target.split(',')
        self.result_file=result_file
        self.data_files=[]
        self.thread_count = threads_count
        self.regex=regex
        self.scan_count = self.found_count = 0
        self.STOP_ME = False
        self.queue = Queue.Queue()
        self.start_time=time.time()
        self.lock = threading.Lock()
        self._load_data_files()
        self._gen_task_queue()
        self.console_width =getTerminalSize()[0]-2 #Cal terminal width when starts up

    #get file extension
    def _file_extension(self,path): 
        return os.path.splitext(path)[1][1:] 

    def _update_scan_count(self):
        self.lock.acquire()
        self.scan_count += 1
        self.lock.release()
        
    def _update_found_count(self):
        self.lock.acquire()
        self.found_count += 1
        self.lock.release()
        
    def _print_progress(self):
        msg = '%s found | %s remaining | %s files scanned in %.2f seconds' % (self.found_count, self.queue.qsize(), self.scan_count, time.time() - self.start_time)
        self._print_msg(msg)
    
    def _print_progress_daemo(self):
        while True:
            if self.queue.qsize()==0:
                break
            self._print_progress()
            time.sleep(1)
            
    def _print_msg(self,msg):
        self.lock.acquire()
        sys.stdout.write('\r' + '' * (self.console_width -len(msg)) + msg)
        sys.stdout.flush()
        self.lock.release()
    
    def _println_msg(self,msg):
        self.lock.acquire()
        sys.stdout.write('\r' + '' * (self.console_width -len(msg)) + msg+"\n\r")
        sys.stdout.flush()
        self.lock.release()
    
    def _write_msg(self,filename,msg):
        self.lock.acquire()
        with open(filename,'a') as f:
            f.write(msg)
        self.lock.release()
        
    def _writeln_msg(self,filename,msg):
        self._write_msg(filename,msg+'\n')
        
    def _load_data_files(self):
        f=file.printPath(1, '.')
        self.data_files=file.getPlainList(f)
        
    def _gen_task_queue(self):
        for data_file in self.data_files:
            if self._file_extension(data_file) in ext:
                continue
            if data_file==self.result_file:
                continue
            else:
                self.queue.put((data_file,))
    
    def _scan(self):
        while self.queue.qsize() > 0 and not self.STOP_ME:
            try:
                vector = self.queue.get(timeout=1.0)
            except:
                break
            self._update_scan_count()
            self._searchName(vector[0],self.target)
        self.lock.acquire()
        self.thread_count -= 1
        self.lock.release()
        
    #Search text in a file
    def _searchName(self,filename,search):
        f=open(filename)
        iter_f=iter(f)
        for line in iter_f:
            for searchText in search:
                find=False
                if self.regex:
                    m=re.compile(searchText)
                    if m.search(line):
                        find=True
                elif line.find(searchText) != -1:
                    find=True
                if find==True:                    
                    self._update_found_count()
                    msg="[+]"+filename+": "+line.strip()
                    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._writeln_msg(self.result_file,now+msg)
                    self._println_msg(msg)
    
    def run(self):
        argv = " ".join(sys.argv)
        now = datetime.datetime.now().strftime('################ %Y-%m-%d %H:%M:%S ################')
        self._writeln_msg(self.result_file,now)
        self._writeln_msg(self.result_file,"  "+argv)
        t = threading.Thread(target=self._print_progress_daemo)
        t.setDaemon(True)
        t.start()
        for i in range(self.thread_count):
            t = threading.Thread(target=self._scan, name=str(i))
            t.setDaemon(True)
            t.start()
        while self.thread_count >= 1:
            try:
                time.sleep(1.0)
            except KeyboardInterrupt,e:
                msg = '[WARNING] User aborted, wait all slave threads to exit...'
                sys.stdout.write('\r' + msg + ' ' * (self.console_width- len(msg)) + '\n\r')
                sys.stdout.flush()
                self.STOP_ME = True
        
def main():
    options = OptionParser(usage='%prog [options] people_infos_to_search', description='A multi-thread tiny social engineering databases searching tool.')
    options.add_option('-T', '--thread', dest='thread', type='int', default=2, help='Threads number (default: 2)')
    options.add_option('-s', '--search', dest='search', type='string', help='Text(MUST Wrapped with "" NOT '') to search,seperated with ,')
    options.add_option('-r', '--regex' , dest='regex' , action='store_true', default=False, help='Use regex match(default: False)')
    opts, args = options.parse_args()
    search=Search(target=opts.search,threads_count=opts.thread,regex=opts.regex)
    search.run()
    
if __name__ == '__main__':
    main()