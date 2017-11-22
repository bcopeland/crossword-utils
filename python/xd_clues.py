#!/usr/bin/python
from xdfile import xdfile
from optparse import OptionParser

def answer_at(grid, startxy, direction):
    x, y = startxy
    maxx = len(grid[0])
    maxy = len(grid)

    word = ''
    if direction == 'A':
        for x in range(x, maxx):
            if grid[y][x] == '#':
                break
            word += grid[y][x]
    else:
        for y in range(y, maxy):
            if grid[y][x] == '#':
                break
            word += grid[y][x]
    return word

def xd_clues(filename):
    xd = xdfile(open(filename).read())

    grid = xd.grid
    maxx = len(grid[0])
    maxy = len(grid)

    next_n = 1
    across = []
    down = []
    for y in range(0, maxy):
        for x in range(0, maxx):
            light = grid[y][x] != '#'

            start_of_xlight = (light and
                               (x == 0 or grid[y][x-1] == '#') and
                               (x + 1 < maxx and grid[y][x+1] != '#'))
            start_of_ylight = (light and
                               (y == 0 or grid[y-1][x] == '#') and
                               (y + 1 < maxy and grid[y+1][x] != '#'))

            num = ""
            if start_of_xlight or start_of_ylight:
                num = next_n
                if start_of_xlight:
                    across.append((num, answer_at(grid, (x, y), 'A')))
                if start_of_ylight:
                    down.append((num, answer_at(grid, (x, y), 'D')))
                next_n += 1

    for n, ans in across:
        print 'A%d. xxx ~ %s' % (n, ans)
    for n, ans in down:
        print 'D%d. xxx ~ %s' % (n, ans)

if __name__ == "__main__":
    usage="Usage: %prog xdfile"
    parser = OptionParser(usage=usage)
    (opts, args) = parser.parse_args()
    xd_clues(args[0])
