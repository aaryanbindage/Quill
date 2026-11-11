# 10. A small project: a to-do list

Time to combine everything. We will build a to-do list manager with classes, a list, a
map, errors, and a text menu driven by commands. We build it in pieces.

## Step 1: the Task class

```python
# course: runs
class Task:
    id: int
    title: str
    done: bool

    def init(self, id: int, title: str):
        self.id = id
        self.title = title
        self.done = false

    def toString(self) -> str:
        mark = " "
        if self.done:
            mark = "x"
        return "[" + mark + "] " + str(self.id) + ". " + self.title

class Main:
    static def main():
        t = new Task(1, "Learn Quill")
        print(t)
        t.done = true
        print(t)
```

```text
[ ] 1. Learn Quill
[x] 1. Learn Quill
```

## Step 2: the list that owns the tasks

The `TodoList` class hides how tasks are stored and reports mistakes by throwing:

```python
# course: runs
class Task:
    id: int
    title: str
    done: bool
    def init(self, id: int, title: str):
        self.id = id
        self.title = title
        self.done = false
    def toString(self) -> str:
        mark = " "
        if self.done:
            mark = "x"
        return "[" + mark + "] " + str(self.id) + ". " + self.title

class TodoList:
    private tasks: List[Task]
    private next: int

    def init(self):
        self.tasks = new List[Task]()
        self.next = 1

    def add(self, title: str) -> Task:
        if title.trim().isEmpty():
            throw new Error("a task needs a title")
        t = new Task(self.next, title.trim())
        self.next = self.next + 1
        self.tasks.add(t)
        return t

    def find(self, id: int) -> Task:
        for t in self.tasks:
            if t.id == id:
                return t
        throw new Error("no task number " + str(id))

    def finish(self, id: int):
        self.find(id).done = true

    def remaining(self) -> int:
        n = 0
        for t in self.tasks:
            if not t.done:
                n = n + 1
        return n

    def show(self):
        for t in self.tasks:
            print(t)
        print(self.remaining(), "left")

class Main:
    static def main():
        todo = new TodoList()
        todo.add("Write a program")
        todo.add("Read lesson 11")
        todo.add("  Take a break  ")
        todo.finish(1)
        todo.show()
        try:
            todo.finish(9)
        catch Error as e:
            print("error:", e.message)
```

```text
[x] 1. Write a program
[ ] 2. Read lesson 11
[ ] 3. Take a break
2 left
error: no task number 9
```

## Step 3: a command loop

Last, read commands from the keyboard with `std.console`. The program stops at the
`quit` command or when the input ends (`readLine` then gives `null`).

```python
# course: runs
# input: add Buy milk\nadd Call home\ndone 1\ndone 7\nlist\nquit
bring std.console

class Task:
    id: int
    title: str
    done: bool
    def init(self, id: int, title: str):
        self.id = id
        self.title = title
        self.done = false
    def toString(self) -> str:
        mark = " "
        if self.done:
            mark = "x"
        return "[" + mark + "] " + str(self.id) + ". " + self.title

class TodoList:
    private tasks: List[Task]
    private next: int
    def init(self):
        self.tasks = new List[Task]()
        self.next = 1
    def add(self, title: str):
        if title.trim().isEmpty():
            throw new Error("a task needs a title")
        self.tasks.add(new Task(self.next, title.trim()))
        self.next = self.next + 1
    def finish(self, id: int):
        for t in self.tasks:
            if t.id == id:
                t.done = true
                return
        throw new Error("no task number " + str(id))
    def show(self):
        for t in self.tasks:
            print(t)

class Main:
    static def run(todo: TodoList, line: str) -> bool:
        space = line.indexOf(" ")
        command = line
        argument = ""
        if space >= 0:
            command = line.substring(0, space)
            argument = line.substring(space + 1, len(line))
        if command == "add":
            todo.add(argument)
        elif command == "done":
            todo.finish(argument.toInt())
        elif command == "list":
            todo.show()
        elif command == "quit":
            return false
        else:
            throw new Error("unknown command: " + command)
        return true

    static def main():
        todo = new TodoList()
        while true:
            line = Console.readLine()
            if line == null:
                break
            try:
                if not Main.run(todo, line):
                    break
            catch Error as e:
                print("error:", e.message)
        print("bye")
```

```text
error: no task number 7
[x] 1. Buy milk
[ ] 2. Call home
bye
```

(The first line of the program above feeds those commands in automatically for this
page. When you run it yourself, you type them.)

## Where to go next

- Add a `remove` command and a `clear` command.
- Save tasks to a file when you quit (the standard library has no files yet; this is a
  good thing to design).
- Show tasks in colour with `Console.paint` and draw a border with `std.art`.
- Read the [language guide](../language-guide.md) for modules (`bring`), packages,
  threads, generics and calling C libraries.

Congratulations: you have written a real program.
