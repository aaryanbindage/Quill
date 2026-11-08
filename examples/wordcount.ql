# Counts words with Map[str, int] and List[str].

class Counter:
    counts: Map[str, int]

    def init(self):
        self.counts = new Map[str, int]()

    def add(self, word: str):
        self.counts[word] = self.counts.getOr(word, 0) + 1

class Main:
    static def main():
        words = new List[str]()
        words.add("the")
        words.add("quick")
        words.add("fox")
        words.add("the")
        words.add("lazy")
        words.add("fox")
        words.add("the")

        c = new Counter()
        for w in words:
            c.add(w)

        for w in c.counts.keys():
            print(w, "->", c.counts[w])
        print("distinct:", c.counts.size(), "total:", words.size())
