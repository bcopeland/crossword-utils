#!/usr/bin/python
from xdfile import xdfile
from optparse import OptionParser
import sys

def xd_lint(filename):
    """
    Check some rules about xd files:
        - Filling in the grid using answers alone results in the same grid
        - All numbered locations have corresponding clues
        - All clues have answers
    """
    error = False
    xd = xdfile(open(filename).read())

    title = 'unknown'
    author = 'unknown'

    for h in xd.headers:
        if h[0] == 'Title':
            title = h[1]
        if h[0] == 'Author':
            author = h[1]

    grid = xd.grid
    maxx = len(grid[0])
    maxy = len(grid)

    filled = []
    for i in range(0, maxy):
        filled.append(['#'] * maxx)

    direction = {'A' : 'across', 'D': 'down'}

    across = {}
    down = {}
    for xdc_tuple in xd.clues:
        dnum, c, a = xdc_tuple
        d, n = dnum
        if d == 'A':
            across[int(n)] = (c, a)
        else:
            down[int(n)] = (c, a)

        if not c:
            print '%s: error: no clue provided for %s %s' % (
                filename, n, direction[d])
            error = True
        if not a:
            print '%s: error: no answer provided for %s %s' % (
                filename, n, direction[d])
            error = True

    number_index = {}
    next_n = 1
    for y in range(0, maxy):
        for x in range(0, maxx):
            light = grid[y][x] != '#'

            start_of_xlight = (light and
                               (x == 0 or grid[y][x-1] == '#') and
                               (x + 1 < maxx and grid[y][x+1] != '#'))
            start_of_ylight = (light and
                               (y == 0 or grid[y-1][x] == '#') and
                               (y + 1 < maxy and grid[y+1][x] != '#'))

            if start_of_xlight and not across.get(next_n):
                print '%s: error: missing clue for %d %s' % (
                    filename, next_n, direction['A'])
                error = True

            if start_of_ylight and not down.get(next_n):
                print '%s: error: missing clue for %d %s' % (
                    filename, next_n, direction['D'])
                error = True

            if start_of_xlight or start_of_ylight:
                number_index[next_n] = (x, y)
                next_n += 1

    for xdc_tuple in xd.clues:
        dnum, c, a = xdc_tuple
        d, n = dnum
        n = int(n)

        if n not in number_index:
            print '%s: error: clue %s %s does not correspond to a grid location' % (
                filename, n, direction[d])
            error = True
            continue

        x, y = number_index[n]
        for i, letter in enumerate(a):
            xp, yp = x, y
            if d == 'A':
                xp = x + i
            else:
                yp = y + i
            if xp >= maxx or yp >= maxy:
                print '%s: error: clue %s %s extends beyond the grid' % (
                    filename, n, direction[d])
            else:
                filled[yp][xp] = letter

    filled = [''.join(x) for x in filled]

    for i, line in enumerate(filled):
        if line != grid[i]:
            print '%s: error: grids do not match on line %d' % (filename, i+1)
            print 'line: %s' % line
            print 'grid: %s' % grid[i]
            error = True
            break

    if error:
        sys.exit(1)

    print 'All checks passed.'
    sys.exit(0)

if __name__ == "__main__":
    xd_lint(sys.argv[1])
