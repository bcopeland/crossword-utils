#!/usr/bin/python
#
# Dump answers from a filled grid
#
import sys
from score_grid import transpose_grid

def answers(grid):

    # parse out the answers from the grid
    answers = []
    for g in [grid, transpose_grid(grid)]:
        lines = g.split()
        for line in lines:
            answers += line.split("#")

    answers = [x for x in answers if len(x) > 1]
    return answers

if __name__ == "__main__":
    grid = sys.stdin.read()
    print '\n'.join(answers(grid))
