#!/usr/bin/python
#
# Extract all unfilled answers and find the hardest answers to
# fill based on corpus.
#
import sys
import math
import re
from score_grid import transpose_grid, score_word
from xd_clues import answer_at

smooth = .001

class Answer(object):
    def __init__(self, corpus, x, y, d, pattern):
        self.x = x
        self.y = y
        self.d = d
        self.pattern = pattern
        self.possibles = []

        if len(pattern) > 1 and '.' in pattern:
            self.possibles = get_fill_matches(corpus, pattern)
        else:
            self.possibles = [(pattern, 100)]


class Cell(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.amap = {}
        self.dmap = {}
        self.a_answer = None
        self.d_answer = None


    def set_answer(self, answer):
        if answer.d == 'A':
            m = self.amap
            self.a_answer = answer
        else:
            m = self.dmap
            self.d_answer = answer

        offs = max(self.x - answer.x, self.y - answer.y)
        for s in answer.possibles:
            cand, score = s
            l = cand[offs]
            entries = m.setdefault(l, [])
            entries.append(s)

    def eliminate(self):
        akeys = set(self.amap.keys())
        dkeys = set(self.dmap.keys())
        keys_to_delete = akeys.symmetric_difference(dkeys)
        for key in keys_to_delete:
            if key in self.amap:
                entries = self.amap.pop(key)
                answer = self.a_answer
            else:
                entries = self.dmap.pop(key)
                answer = self.d_answer
            to_delete = set(entries)
            answer.possibles = [x for x in answer.possibles if x not in to_delete]

def load_corpus(fn):
    corpus = {}
    total_sum = 0
    for line in open(fn).readlines():
        ct, word = line.split()
        word = word.upper()
        corpus.setdefault(word, 0)
        corpus[word] += int(ct)
        total_sum += int(ct)
    corpus['__denom'] = total_sum + (len(corpus.keys()) + 1) * smooth
    return corpus

def get_fill_matches(corpus, word):
    regex = re.compile("^" + word + "$")
    denom = corpus['__denom']
    possibles = []
    for cand, ct in corpus.iteritems():
        if not regex.match(cand):
            continue
        p_word = math.log(ct + smooth) / denom
        possibles.append((cand, p_word))

    best_matches = sorted(possibles, key=lambda x: x[1], reverse=True)
    return best_matches

def check_fill(corpus, grid):

    maxx = len(grid[0])
    maxy = len(grid)

    cells = [[None for i in range(maxx)] for j in range(maxy)]
    for y in range(maxy):
        for x in range(maxx):
            cells[y][x] = Cell(x, y)

    answers = []
    # extract answers
    last_x_answer = last_y_answer = None
    for y in range(maxy):
        for x in range(maxx):
            light = grid[y][x] != '#'

            start_of_xlight = (light and
                               (x == 0 or grid[y][x-1] == '#') and
                               (x + 1 < maxx and grid[y][x+1] != '#'))
            start_of_ylight = (light and
                               (y == 0 or grid[y-1][x] == '#') and
                               (y + 1 < maxy and grid[y+1][x] != '#'))

            if start_of_xlight:
                pat = answer_at(grid, (x, y), 'A')
                answers.append(Answer(corpus, x, y, 'A', pat))
                for i in range(len(pat)):
                    cells[y][x+i].set_answer(answers[-1])

            if start_of_ylight:
                pat = answer_at(grid, (x, y), 'D')
                answers.append(Answer(corpus, x, y, 'D', pat))
                for i in range(len(pat)):
                    cells[y+i][x].set_answer(answers[-1])

    # elimination
    for y in range(maxy):
        for x in range(maxx):
            cells[y][x].eliminate()

    a_matches = [(ans.pattern, ans.possibles) for ans in answers if '.' in ans.pattern]
    sorted_matches = sorted(a_matches, key=lambda x: len(x[1]))
    return sorted_matches

if __name__ == "__main__":
    #corpus = load_corpus("all_corpus")
    corpus = load_corpus("nyt_corpus")
    #corpus = load_corpus("google/gug_corpus")
    #corpus = load_corpus("google/bigrams/all_2009_bigrams_unsorted")
    grid = sys.stdin.read().split()
    results = check_fill(corpus, grid)
    print '\n\n'.join(['%s -> (%d) %s' % (x[0], len(x[1]), str(x[1][:30])) for x in results])
