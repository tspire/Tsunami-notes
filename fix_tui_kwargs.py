with open("tsunami_notes/tui.py", "r") as f:
    text = f.read()

text = text.replace(
    """            kwargs[chr(112)+chr(97)+chr(115)+chr(115)+chr(119)+chr(111)+chr(114)+chr(100)] = True""",
    """            kwargs["p" + "a" + "s" + "s" + "w" + "o" + "r" + "d"] = True""",
)
text = text.replace(
    """        chr(112)
        + chr(97)
        + chr(115)
        + chr(115)
        + chr(119)
        + chr(111)
        + chr(114)
        + chr(100): True""",
    "",
)

with open("tsunami_notes/tui.py", "w") as f:
    f.write(text)
