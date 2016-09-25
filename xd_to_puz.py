#!/usr/bin/python
from xdfile import xdfile
from optparse import OptionParser
import crossword

def xd_to_puz(filename, filename_out):
    xd = xdfile(open(filename).read())

    grid = xd.grid
    maxx = len(grid[0])
    maxy = len(grid)

    puzzle = crossword.Crossword(maxx, maxy)

    title = 'unknown'
    author = 'unknown'

    for h in xd.headers:
        if h[0] == 'Title':
            title = h[1]
        if h[0] == 'Author':
            author = h[1]

    puzzle.meta.creator = author
    puzzle.meta.title = title

    for xdc_tuple in xd.clues:
        dnum, c, a = xdc_tuple
        d, n = dnum

        if d == 'A':
            puzzle.clues.across[int(n)] = c
        else:
            puzzle.clues.down[int(n)] = c

    for direction, number, clue in puzzle.clues.all():
        print(direction, number, clue)

    for y in range(0, maxy):
        for x in range(0, maxx):
            ch = grid[y][x]
            if ch != '#':
                puzzle[y][x].cell = " "
                puzzle[y][x].solution = grid[y][x]
            else:
                puzzle[y][x].cell = "."
                puzzle[y][x].block = None
                puzzle[y][x].solution = None

    puz = crossword.to_puz(puzzle)
    puz.fill = ''.join([x if x == '.' else '-' for x in puz.solution])
    puz.save(filename_out)

if __name__ == "__main__":
    usage="Usage: %prog xdfile puzfile"
    parser = OptionParser(usage=usage)
    (opts, args) = parser.parse_args()
    xd_to_puz(args[0], args[1])
