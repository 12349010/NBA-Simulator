# check_indent.py – prints first 40 bytes of app.py
with open("app.py", "rb") as f:
    print(repr(f.read(40)))
