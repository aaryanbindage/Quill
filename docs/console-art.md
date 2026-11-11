# Printing to the console and text art

Two standard modules: `std.console` for talking to the terminal and `std.art` for
drawing in it. Both work on Windows, Linux and macOS and need no extra libraries.

```python
bring std.console
bring std.art
```

## std.console

| Call | What it does |
|---|---|
| `Console.write(s)` / `Console.writeln(s)` | print without / with a newline |
| `Console.flush()` | send buffered output now (`readLine` and `sleep` do it for you) |
| `Console.init()` | call once if you use colours; switches the Windows console to ANSI colours and UTF-8 |
| `Console.paint(text, color)` / `paintOn(text, fg, bg)` | text in a colour, followed by a reset |
| `Console.bold / dim / underline / invert(text)` | styles |
| `Console.rgb(r, g, b)` | the nearest of the 256 palette colours |
| `Console.red() green() yellow() blue() magenta() cyan() white() gray() black()` | colour numbers 0 to 8 (0..15 normal and bright, 16..255 palette) |
| `Console.clear()`, `moveTo(row, col)`, `clearLine()` | screen and cursor |
| `Console.hideCursor()` / `showCursor()` / `enterScreen()` / `leaveScreen()` | full-screen programs |
| `Console.sleep(ms)` | pause (animations) |
| `Console.readLine()` / `Console.ask(prompt)` | one line of input; `null` at the end of the input |

Colour codes are escape sequences, so they appear as junk if the output is not a
terminal. Test for that yourself if you need to; nothing is stripped automatically.

## std.art

`Canvas(width, height)` is a grid of characters with an optional colour per cell.
Coordinates start at 0,0 in the top left. Anything drawn outside the grid is ignored.

```python
c = new Canvas(40, 12)
c.frame(0, 0, 40, 12, Console.gray())
c.fillEllipse(12, 6, 8, 4, "#", Console.red())
c.line(1, 1, 38, 10, "*", Console.yellow())
c.text(15, 5, "hello", Console.white())
c.show()                      # colour; c.toString() gives plain text
```

`plot`, `line`, `rect`, `fillRect`, `frame` (`+ - |`), `circle`, `ellipse`, `fillCircle`,
`fillEllipse`, `text`, `floodFill`, `draw(other, x, y)` (stamp one canvas on another),
`bars(values, ch, color)`, `fill`, `clear`, `get`, `render(colour)`, `show()`.
Terminal cells are about twice as tall as wide, so for round circles use `ellipse(cx, cy, 2 * r, r)`.

Also in `std.art`:

- `Banner.render("Hello 42!")` or `Banner.show(text, color)`: five-row block letters (letters,
  digits, space and `! . - ? : + * / =`).
- `Art.shade(0.0..1.0)`: a brightness ramp character; `Art.rainbow(text)`; `Art.rule(n, ch)`;
  `Art.boxed(lines)`.

Limits: strings are bytes, so characters outside ASCII count as several columns; the
sine used for ellipses is an integer approximation (good to about a cell); there are no
images or fonts, only characters.

See `examples/art.ql`.
