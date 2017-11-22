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

used_answers = set()

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

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '%s,%s %s pat: %s, top: %s (%s)' % (
            self.x, self.y, self.d,
            self.pattern, self.possibles[0][0], self.possibles[0][1])


class Cell(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.amap = {}
        self.dmap = {}
        self.a_answer = None
        self.d_answer = None
        self.is_black = False

    def set_black(self, is_black):
        self.is_black = is_black

    def set_answer(self, answer):
        if answer.d == 'A':
            self.amap = {}
            m = self.amap
            self.a_answer = answer
        else:
            self.dmap = {}
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
        entries_to_delete = used_answers
        for key in keys_to_delete:
            if key in self.amap:
                entries = self.amap.pop(key)
            else:
                entries = self.dmap.pop(key)
            entries_to_delete = entries_to_delete.union(set(entries))

        for a in (self.a_answer, self.d_answer):
            if a:
                a.possibles = [x for x in a.possibles if x not in entries_to_delete]

    def __str__(self):
        return repr(self)

    def __repr__(self):
        ok_letters = [x for x in set(self.amap.keys()).intersection(set(self.dmap.keys()))]
        if len(ok_letters) == 1:
            return ok_letters[0]
        return '#' if self.is_black else '.'

def load_corpus(fn):
    print 'Loading corpus...'
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


def build_cell_array(corpus, grid):
    print 'Constructing possible sets...'
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

            if not light:
                cells[y][x].set_black(True)

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

    return (cells, answers)

def check_fill(cells, answers):
    print 'Eliminating...'
    maxy = len(cells)
    maxx = len(cells[0])
    # elimination
    for y in range(maxy):
        for x in range(maxx):
            cells[y][x].eliminate()

    a_matches = [ans for ans in answers if '.' in ans.pattern]
    sorted_matches = sorted(a_matches, key=lambda x: len(x.possibles))
    return sorted_matches


def set_answer_at(cells, answer, value):
    xinc = 1 if answer.d == 'A' else 0
    yinc = 1 if answer.d == 'D' else 0

    new_answer = Answer(None, answer.x, answer.y, answer.d, value)
    x, y = answer.x, answer.y

    for i in range(len(value)):
        cell = cells[y + yinc * i][x + xinc * i]
        cell.set_answer(new_answer)

def grid_str(cells):
    maxy = len(cells)
    maxx = len(cells[0])

    grid = ''
    for y in range(maxy):
        line = ''
        for x in range(maxx):
            line += str(cells[y][x])
        grid += line + "\n"
    return grid

def do_fill(corpus, grid):

    cells, answers = build_cell_array(corpus, grid)
    while True:
        results = check_fill(cells, answers)
        if not results or not len(results[0].possibles):
            break

        # fill hardest guy first
        print 'results: %s' % results
        choice = results[0].possibles[0][0]
        set_answer_at(cells, results[0], choice)
        answers.remove(results[0])
        used_answers.add(results[0].possibles[0])

        print 'New grid:\n%s' % (grid_str(cells))
    return grid_str(cells)


if __name__ == "__main__":
    #corpus = load_corpus("all_corpus")
    corpus = load_corpus("nyt_corpus")
    #corpus = load_corpus("google/gug_corpus")
    #corpus = load_corpus("google/bigrams/all_2009_bigrams_unsorted")
    grid = sys.stdin.read().split()
    print do_fill(corpus, grid)
