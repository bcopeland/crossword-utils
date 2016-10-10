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
    def __init__(self, x, y, d, pattern):
        self.x = x
        self.y = y
        self.d = d
        self.pattern = pattern
        self.possibles = []
        self.crosses = []

    def add_cross(self, a):
        self.crosses.append(a)


def load_corpus(fn):
    corpus = {}
    total_sum = 0
    for line in open(fn).readlines():
        ct, word = line.split()
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

    # y -> x -> [across, down]
    grid_to_answer = [[[None, None] for i in range(maxx)] for j in range(maxy)]

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
                answers.append(Answer(x, y, 'A', answer_at(grid, (x, y), 'A')))
                last_x_answer = answers[-1]
            if start_of_ylight:
                answers.append(Answer(x, y, 'D', answer_at(grid, (x, y), 'D')))
                last_y_answer = answers[-1]
            if light:
                grid_to_answer[y][x][0] = last_x_answer
                grid_to_answer[y][x][1] = last_y_answer

    # extract crosses
    for y in range(maxy):
        for x in range(maxx):
            if grid_to_answer[y][x][0] and grid_to_answer[y][x][1]:
                grid_to_answer[y][x][0].add_cross(grid_to_answer[y][x][1])
                grid_to_answer[y][x][1].add_cross(grid_to_answer[y][x][0])

    for a in answers:
        print 'answer: %s' % a.pattern

    # drop filled and empty words or 1-letter words
    words = [x.pattern for x in answers if len(x.pattern) > 1 and '.' in x.pattern]
    matches = map(lambda x: get_fill_matches(corpus, x), words)
    a_matches = zip(words, matches)

    sorted_matches = sorted(a_matches, key=lambda x: len(x[1]))
    return sorted_matches

if __name__ == "__main__":
    #corpus = load_corpus("nyt_corpus")
    corpus = load_corpus("google/gug_corpus")
    #corpus = load_corpus("google/bigrams/all_2009_bigrams_unsorted")
    grid = sys.stdin.read().split()
    results = check_fill(corpus, grid)
    print '\n\n'.join(['%s -> (%d) %s' % (x[0], len(x[1]), str(x[1][:30])) for x in results])
