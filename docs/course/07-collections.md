# 7. Lists and maps

## Lists

A `List` holds many values of one type, in order. The type goes in square brackets:

```python
# course: runs
class Main:
    static def main():
        names = new List[str]()
        names.add("Ada")
        names.add("Grace")
        names.add("Linus")
        print(names.size(), "names; the first is", names.get(0))

        names.set(1, "Hopper")
        for name in names:
            print("-", name)

        print(names.contains("Linus"), names.indexOf("Ada"))
        names.removeAt(0)
        print(names.size())
```

```text
3 names; the first is Ada
- Ada
- Hopper
- Linus
true 0
2
```

Positions start at 0. Asking for a position that does not exist stops the program with
an "index out of range" error rather than silently reading garbage.

You can also write a list directly, and sort it:

```python
# course: runs
class Main:
    static def main():
        nums = [5, 2, 9, 1]
        nums.sort()
        print(nums.get(0), nums.get(3))
        nums.reverse()
        total = 0
        for n in nums:
            total = total + n
        print("total", total)
```

```text
1 9
total 17
```

## Maps

A `Map` connects **keys** to **values**, like a dictionary: look up a word, find its
meaning. You name both types:

```python
# course: runs
class Main:
    static def main():
        ages = new Map[str, int]()
        ages.set("Ada", 36)
        ages.set("Grace", 85)
        ages.set("Ada", 37)          # setting again replaces the old value

        print(ages.get("Ada"))
        print(ages.has("Linus"), ages.getOr("Linus", -1))
        print(ages.size(), "entries")

        keys = ages.keys()
        keys.sort()
        for k in keys:
            print(k, "->", ages.get(k))
```

```text
37
false -1
2 entries
Ada -> 37
Grace -> 85
```

A map does not keep its entries in any particular order; sort the keys if you need one.

## Counting words

Lists and maps together solve real problems:

```python
# course: runs
class Main:
    static def main():
        text = "the cat and the hat and the bat"
        counts = new Map[str, int]()
        for word in text.split(" "):
            counts.set(word, counts.getOr(word, 0) + 1)

        words = counts.keys()
        words.sort()
        for w in words:
            print(w.padRight(5, " "), counts.get(w))
```

```text
and   2
bat   1
cat   1
hat   1
the   3
```

## Sets

A `Set` holds each value at most once.

```python
# course: runs
class Main:
    static def main():
        seen = new Set[int]()
        for n in [3, 1, 3, 2, 1]:
            seen.add(n)
        print(seen.size(), seen.has(2), seen.has(9))
```

```text
3 true false
```

## Exercises

1. Make a list of ten numbers and print the largest, without sorting.
2. Remove the duplicates from `[1, 2, 2, 3, 3, 3]` using a `Set`.
3. Read a sentence and print how many times each letter occurs. (Hint: `split("")` gives the letters.)
4. Make a `Map[str, List[str]]` of people to their hobbies and print it tidily.

Next: [Sharing behaviour](08-inheritance.md).
