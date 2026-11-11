# 12. Drawing in the terminal

Two standard modules make the terminal fun: `std.console` (colours, cursor, keyboard
input) and `std.art` (a canvas to draw on and big letters). In this lesson we use the
plain-text form, `toString()`, so the pictures are the same everywhere. To see them in
colour use `show()` instead.

## A canvas

A `Canvas` is a grid of characters. Coordinates start at 0,0 in the top left corner;
x grows to the right and y grows downward. The last argument of each drawing call is a
colour; `-1` means "no colour".

```python
# course: runs
bring std.art

class Main:
    static def main():
        c = new Canvas(24, 8)
        c.frame(0, 0, 24, 8, -1)
        c.line(2, 6, 21, 1, "*", -1)
        c.text(4, 3, "Quill", -1)
        c.plot(12, 5, "@", -1)
        print(c.toString())
```

```text
+----------------------+
|                   ** |
|               ****   |
|   Quill   ****       |
|       ****           |
|   ****    @          |
| **                   |
+----------------------+
```

Shapes can hang over the edge; the part outside is simply not drawn.

## Shapes

```python
# course: runs
bring std.art

class Main:
    static def main():
        c = new Canvas(30, 11)
        c.fillEllipse(8, 5, 7, 4, "#", -1)
        c.ellipse(21, 5, 7, 4, "o", -1)
        c.rect(12, 3, 6, 5, "+", -1)
        print(c.toString())
```

```text

        #            o
    #########    ooooooooo
  ##########++++++       oo
  ##########+##o +         o
 ###########+#oo +         oo
  ##########+##o +         o
  ##########++++++       oo
    #########    ooooooooo
        #            o
```

A character cell is about twice as tall as it is wide, so a circle of radius 4 looks
round when you draw an ellipse that is 8 wide and 4 tall.

## Big letters

```python
# course: runs
bring std.art

class Main:
    static def main():
        print(Banner.render("Hi 5!"))
```

```text
#   # #####       #####   #   
#   #   #         #       #   
#####   #         ####    #   
#   #   #             #       
#   # #####       ####    #
```

## Colours and the console

With `std.console` you can colour any text. Colours are numbers (0 to 255), and
`Console.rgb(r, g, b)` finds the closest one:

```python
# course: runs
bring std.console

class Main:
    static def main():
        Console.init()        # switches colours on in the Windows console
        Console.writeln(Console.paint("error", Console.red()))
        Console.writeln(Console.bold("bold") + " and " + Console.underline("underlined"))
        Console.write("no newline, ")
        Console.writeln("then a newline")
```

Run it in a terminal to see a red word, bold and underlined text, and two writes on one line. The
colours are special control codes inside the text; if you send the output to a file the codes
are in the file too, so only use colour when a person is looking at a terminal.

## Exercises

1. Draw a house: a rectangle for the walls, lines for the roof, a small rectangle for the door.
2. Print your first name as big letters.
3. Draw a bar chart of your last five quiz scores with `bars`.
4. Run the colour program in your terminal and add a yellow warning line.
5. Make a ruler: `Art.rule(40, "-")` with tick marks drawn above it on a canvas.

Next: [Generics](13-generics.md).
