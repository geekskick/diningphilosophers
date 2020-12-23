import threading
import time
import random
import tkinter as tk
import logging

end = threading.Event()


class Logger(logging.Handler):
    def __init__(self, text):
        logging.Handler.__init__(self)
        self._text = text
        self.createLock()

    def emit(self, record):
        s = self.format(record)
        if threading.main_thread():
            self.append(s)

    def append(self, msg):
        self.acquire()
        self._text.configure(state='normal')
        self._text.insert(tk.END, msg + "\n")
        self._text.configure(state='disabled')
        self._text.yview(tk.END)
        self.release()


class DiningFork(object):
    def __init__(self, name: str):
        self.name = name
        self.lock = threading.Lock()


class TableSpace(object):
    THINKING = 'green'
    EATING = 'red'
    ACQUIRING = 'cyan'
    GOT = 'blue'

    def __init__(self, label: tk.Label, detail: tk.Label):
        self._label = label
        self._detail = detail
        self._count = 0
        self.thinking()

    def acquiringFirst(self):
        if not end.is_set():
            self._label.config(bg=self.ACQUIRING)
            self._updateLabel("Waiting on first fork")

    def gotFirst(self):
        if not end.is_set():
            self._label.config(bg=self.GOT)
            self._updateLabel("Waiting on second fork")

    def eating(self):
        self._count += 1
        self._label.config(bg=self.EATING)
        self._detail['text'] = str(self._count)
        self._updateLabel("Eating")

    def thinking(self):
        self._label.config(bg=self.THINKING)
        self._updateLabel("Thinking")

    def _updateLabel(self, text: str):
        text = f"({text})"
        orig = self._label['text']
        parts = orig.split('\n')
        self._label['text'] = "\n".join((parts[0], text))


def philosopher(name: str, left: DiningFork, right: DiningFork, space: TableSpace):
    # Use djikstra method:
    #   Get the forks in their low-high priority order, this
    #   means that the final philosopher will have their forks 'swapped' so they wont be
    #   able to pick up the first fork
    logging.getLogger(__name__).info(
        f"{name} - Passed the left {left.name}, and right {right.name}")
    sorted_forks = sorted((left, right), key=lambda x: int(x.name))
    logging.getLogger(__name__).info(
        f"{name} - Sorted[0] = {sorted_forks[0].name}, Sorted[1] = {sorted_forks[1].name}")

    while not end.is_set():
        space.acquiringFirst()
        sorted_forks[0].lock.acquire()

        space.gotFirst()
        sorted_forks[1].lock.acquire()

        # If the GUI has ended then I don't want to try to do anything, I want to release the locks
        if not end.is_set():
            t = random.randint(1, 5)
            logging.getLogger(__name__).info(
                f"{name} - {name} is eating for {t}s")
            space.eating()
            time.sleep(t)

        for fork in sorted_forks:
            fork.lock.release()

        if not end.is_set():
            t = random.randint(1, 5)
            logging.getLogger(__name__).info(
                f"{name} - {name} is thinking for {t}s")
            space.thinking()
            time.sleep(t)
        else:
            break


PHILOSOPHERS = ("Pat", "John", "Becky", "Lauren", "Emily")
forks = [DiningFork(str(i)) for i in range(len(PHILOSOPHERS))]

root = tk.Tk()
root.wm_title("Dining Philosophers")
root.resizable(height=False, width=False)
spaces = {}
threads = []

logger = tk.Text(root)
logger.grid(row=2, columnspan=len(PHILOSOPHERS))
logger = Logger(logger)

logging.basicConfig(level=0)
logging.getLogger(__name__).addHandler(logger)


for c, p in enumerate(PHILOSOPHERS):
    l = tk.Label(root, text=p,  width=20, height=5)
    l.grid(row=0, column=c)

    d = tk.Label(root, text='0')
    d.grid(row=1, column=c)

    spaces[p] = TableSpace(l, d)

for n in range(len(forks)):
    t = threading.Thread(target=philosopher, args=(
        PHILOSOPHERS[n], forks[n], forks[(n+1) % len(forks)], spaces[PHILOSOPHERS[n]]))
    logging.getLogger(__name__).info(f"Starting {PHILOSOPHERS[n]}")
    threads.append(t)


[x.start() for x in threads]

root.mainloop()

end.set()
for t in threads:
    t.join()
