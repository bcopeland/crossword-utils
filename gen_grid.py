#!/usr/bin/python
#
# Find a grid that has a good possibility of working with qxw-cli filler
#
import re
import sys
import random

MAX_X=15

def is_valid_row(r):
    l_run = black = light = 0
    min_run = MAX_X

    for i in range(0, MAX_X):
        if r & (1<<i):
            black += 1
            if l_run and min_run > l_run:
                min_run = l_run
            l_run = 0
        else:
            light += 1
            l_run += 1

    if l_run and min_run > l_run:
        min_run = l_run

    # require this much grid in play
    if light < 10:
        return False

    # smallest run must be at least 3
    if min_run < 3:
        return False

    return True

def is_valid_grid(grid):
    for row in grid:
        if not is_valid_row(row):
            return False

    for x in range(MAX_X):
        col = 0
        for y in range(MAX_X):
            row = grid[y]
            if row & (1 << x):
                col |= (1 << y)
        if not is_valid_row(col):
            return False
    return True

def str_to_rowval(x):
    val = 0
    x = x.strip()
    for i, c in enumerate(x):
        if c == '#':
            val |= (1 << i)
    return val

def row_flip(x):
    flipped = 0
    for i in range(MAX_X):
        if x & (1 << i):
            flipped |= (1 << (MAX_X - i - 1))
    return flipped

def row_str(r):
    x = ['.'] * MAX_X
    for i in range(0, MAX_X):
        if r & (1 << i):
            x[i] = '#'
    return ''.join(x)

def grid_str(rows):
    return '\n'.join(row_str(x) for x in rows)

def rand_grid(rows, template=None):
    if not template:
        grid = [0] * MAX_X
    else:
        grid = template[:]

    perm = list(range(len(rows)))
    for i in range(MAX_X/2):
        if template[i]:
            continue

        random.shuffle(perm)
        # try to find a compatible row shape...
        for j in perm:
            grid[i] = rows[j]
            grid[MAX_X - i - 1] = row_flip(rows[j])
            if is_valid_grid(grid):
                break

        if not is_valid_grid(grid):
            raise ValueError, "Exhausted attempts, partial grid:\n%s" % grid_str(grid)

    return grid


def enumerate_grids(template):
    valid_rows = []
    for i in range(0, 2**MAX_X):
        row = i
        if is_valid_row(i):
            valid_rows.append(i)

    tmpl_lines = template.strip().split()
    while True:
        tmpl_v = [str_to_rowval(x) for x in tmpl_lines]

        grid = rand_grid(valid_rows, tmpl_v)
        if is_valid_grid(grid):
            break

    v = grid_str(grid)
    lines = v.split()
    for i, l in enumerate(tmpl_lines):
        if re.search(r'[A-Z#]', l):
            lines[i] = l

    v = '\n'.join(lines)

    l = ['#' for x in v if x == '#']
    print v

if __name__ == "__main__":
    template = sys.stdin.read()
    MAX_X = len(template.split()[0])
    try:
        enumerate_grids(template)
    except:
        print template
