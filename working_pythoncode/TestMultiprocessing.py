from multiprocessing import Process, Queue


def f(q):
    print ("")
    q.put([1])
    print (q.empty())

if __name__ == '__main__':
    q = Queue()
    p = Process(target=f, args=(q,))
    p.start()
    # if q.empty() != False:
    #     print (q.get())    # prints "[42, None, 'hello']"
    # print (q.get())
    p.join()
