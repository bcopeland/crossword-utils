#!/usr/bin/python
#
# Find a grid that has a good possibility of working with qxw-cli filler
#
import sys
import math

smooth = .001

def load_corpus(fn):
    corpus = {}
    total_sum = 0
    for line in open(fn).readlines():
        word, ct = line.split()
        corpus.setdefault(word, 0)
        corpus[word] += int(ct)
        total_sum += int(ct)
    corpus['__denom'] = total_sum + (len(corpus.keys()) + 1) * smooth
    return corpus

def score_word(corpus, w):
    p_word = math.log((corpus.get(w, 0) + smooth) / corpus['__denom'])
    print 'word: %s, score: %f' % (w, p_word)
    return p_word

def transpose_grid(grid):
    xgrid = []
    lines = grid.split()
    width = len(lines[0])
    height = len(lines)
    for x in range(width):
        line = ''
        for y in range(height):
            line += lines[y][x]
        xgrid.append(line)
    return '\n'.join(xgrid)

def score_grid(corpus, grid):

    # parse out the answers from the grid
    answers = []
    for g in [grid, transpose_grid(grid)]:
        lines = g.split()
        for line in lines:
            answers += line.split("#")

    # drop empty words or 1-letter words
    answers = [x for x in answers if len(x) > 1]
    p = 0.0
    for a in answers:
       p += score_word(corpus, a)

    return p

if __name__ == "__main__":
    corpus = load_corpus("all_dict")
    grid = sys.stdin.read()
    print score_grid(corpus, grid)
