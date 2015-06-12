import multiprocessing


def testfunction():
    print ("in function")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    startaudiooutput = multiprocessing.Process(target=testfunction)
    startaudiooutput.start()
    print ("end skript")
    # startaudiooutput.join()


