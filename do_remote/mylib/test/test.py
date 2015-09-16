foo = """
this is 
a multi-line string.
"""

def f1(foo=foo): return iter(foo.splitlines())

def f2(foo=foo):
    retval = ''
    for char in foo:
        retval += char if not char == '\n' else ''
        if char == '\n':
            yield retval
            retval = ''
    if retval:
        yield retval

def f3(foo=foo):
    prevnl = -1
    while True:
      nextnl = foo.find('\n', prevnl + 1)
      if nextnl < 0: break
      yield foo[prevnl + 1:nextnl]
      prevnl = nextnl

if __name__ == '__main__':
  for f in f1, f2, f3:
    print list(f())