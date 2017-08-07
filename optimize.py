#!/usr/bin/python -u
#
# Optimize a completed puzzle:
#
# 1) score all the words and sort by score
# 2) repeat:
#    a) blank out a word
#    b) blank out words intersecting that word
#    c) blank out words intersecting those words, and so on
#    d) do the fill again
#
from fill import Wordlist, Grid
import random

do_not_change = ['pacificave','theodyssey','caravanroute','siennamiller','tearfulness','standsalone']

def clear_entry(e, branch):

    pattern = ''
    xentries = []
    for cell in e.cells:
        xe = cell.cross_entry(e)

        # don't clear out themers
        if xe.cell_pattern() in do_not_change:
            pattern += cell.value
        else:
            xentries.append(xe)
            pattern += '.'
    e.set(pattern)
    for xe in xentries:
        xe.reset_dict()
        if branch > 0:
            clear_entry(xe, branch-1)

def main(tmpl):
    words = Wordlist('XwiWordList.txt', randomize=1.0, omit=['anitra'])
    orig_grid = Grid(tmpl, words)
    orig_score = orig_grid.score()

    grid = orig_grid.copy()
    best_grid = grid.copy()
    best_score = None

    print 'orig: %s' % orig_grid.score()
    print 'new: %s' % grid.score()
    print 'newnew: %s' % best_grid.score()

    while True:
        newwordlist = Wordlist('XwiWordList.txt', randomize=0.2, omit=['anitra'])
        grid = best_grid.copy(wordlist=newwordlist)
        entries = grid.scored_entries()

        e = random.choice(entries)
        if e.cell_pattern() in do_not_change:
            continue

        branch = random.randint(0,3)
        print 'clearing: %s branch %d' % (e, branch)
        clear_entry(e, branch)

        grid.fill()

        print 'grid:\n%s' % grid
        print 'initial score: %d' % orig_score
        print 'current score: %d' % grid.score()
        print 'best score: %d' % best_grid.score()
        print 'best grid:\n%s' % best_grid

        if not best_score or grid.score() >= best_score:
            best_score = grid.score()
            best_grid = grid.copy()


if __name__ == "__main__":
    import sys
    tmpl = open(sys.argv[1]).read()
    main(tmpl)
