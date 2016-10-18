import multiprocessing
 
q = multiprocessing.Queue()
 
def writer_proc():
    q.put(100)
 
def reader_proc():
    print q.get()
 
reader = multiprocessing.Process(target=reader_proc)
reader.start()
writer = multiprocessing.Process(target=writer_proc)
writer.start()
 
reader.join()
writer.join()
