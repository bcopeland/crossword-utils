#!/usr/bin/python
from xdfile import xdfile
import sys
import json

def number_grid(grid):
    # number grid: if there are lights in either direction then
    # we mark the x/y of the cell as needing a number, after that
    # we can number them in order.

    maxx = len(grid[0])
    maxy = len(grid)

    next_n = 0
    number_index = []
    for y in range(0, maxy):
        for x in range(0, maxx):
            if grid[y][x] == '#':
                continue

            start_of_xlight = ((x == 0 or grid[y][x-1] == '#') and
                               (x + 1 < maxx and grid[y][x+1] != '#'))
            start_of_ylight = ((y == 0 or grid[y-1][x] == '#') and
                               (y + 1 < maxy and grid[y+1][x] != '#'))

            if start_of_xlight or start_of_ylight:
                number_index.append((x,y))
                next_n += 1

    return number_index

def main(filename):
    xd = xdfile(open(filename).read())

    title = 'unknown'
    author = 'unknown'

    for h in xd.headers:
        if h[0] == 'Title':
            title = h[1]
        elif h[0] == 'Author':
            author = h[1]

    puzzle = {
        'title': title,
        'by': author
    }

    number_index = number_grid(xd.grid)

    cluelist = []
    for xdc_tuple in xd.clues:
        dnum, c, a = xdc_tuple
        d, n = dnum
        n = int(n)

        xy = number_index[n-1]
        clue = {
            'd': d,
            'n': n,
            'x': xy[0],
            'y': xy[1],
            'a': a,
            'c': c
        }
        cluelist.append(clue)

    puzzle['clues'] = cluelist
    print json.dumps(puzzle)

if __name__ == "__main__":
    main(sys.argv[1])
