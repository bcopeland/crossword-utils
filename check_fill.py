#!/usr/bin/python
#
# Extract all unfilled answers and find the hardest answers to
# fill based on corpus.
#
import sys
import math
import re
from score_grid import transpose_grid, score_word

smooth = .001

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

    # parse out the answers from the grid
    answers = []
    for g in [grid, transpose_grid(grid)]:
        lines = g.split()
        for line in lines:
            answers += line.split("#")

    # drop filled and empty words or 1-letter words
    answers = [x for x in answers if len(x) > 1 and '.' in x]
    matches = map(lambda x: get_fill_matches(corpus, x), answers)
    a_matches = zip(answers, matches)

    sorted_matches = sorted(a_matches, key=lambda x: len(x[1]))
    return sorted_matches

if __name__ == "__main__":
    #corpus = load_corpus("nyt_corpus")
    corpus = load_corpus("google/gug_corpus")
    #corpus = load_corpus("google/bigrams/all_2009_bigrams_unsorted")
    grid = sys.stdin.read()
    results = check_fill(corpus, grid)
    print '\n\n'.join(['%s -> (%d) %s' % (x[0], len(x[1]), str(x[1][:30])) for x in results])
