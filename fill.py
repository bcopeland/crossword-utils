#!/usr/bin/python -u
#
# fill test code

# todo
# - fix computed cross list after backtracking
# - drop used_words for this level of state
# - randomize selection

# some things filler.c does:
#  - update flag; only have to look at the changed parts of an entry
#
# if we fill words and letter map does not change, no need to also
# update crosses
#

#
# update:
#  - if we changed a word, obviously wordlist is now just that word
#    and all crosses must be updated
#  - _only_ if the update process changes valid letters do crosses
#    then need to be examined.
#
#  or, just have a per-cell dirty flag which indicates valid_letters
#  changed; any crosses then need to be evaluated for all entries,
#  propagate outwards...

#
# reset:
#  - is costly because we call revalidate all
#  - would be cheaper if we could just restore state to before the fill

# ... just implement like filler.c, basically just need:
# 1) upd flags for entries and cells
# 2) save entries and cells before fill changes; restore if needed

satisfy_ct = 0


from operator import itemgetter
import re
import string
import random
from optparse import OptionParser

class Wordlist(list):

    len_idx = {}
    scores = {}
    bmaps = []

    # problem with this indexing scheme: changing the dictionary
    # means invaliding all cached indexes among all the entries.
    # would be better if the dictionary kept the indexes internally.
    def __init__(self, fn, randomize=0.0, omit=[]):
        list.__init__(self)
        for l in open(fn).readlines():
            word, score = l.strip().split(';')
            if word in omit:
                continue
            self.append((word, int(score)))
            self.scores[word] = int(score)

        # alpha
        self.sort(key=itemgetter(0))
        # score
        self.sort(key=itemgetter(1), reverse=True)

        # random perturb
        r = random.Random()
        shufamt = randomize * r.randrange(len(self))
        print 'shuf: %f' % (randomize)
        for i in range(int(shufamt + 0.5)):
            x = r.randrange(len(self))
            y = r.randrange(len(self))
            tmp = self[x]
            self[x] = self[y]
            self[y] = tmp

        # length
        self.sort(key=lambda x: len(x[0]))

        for i, l in enumerate(self):
            word, score = l
            if len(word) not in self.len_idx:
                self.len_idx[len(word)] = i

            bmap = [1 << char_bitmap_table[ord(x)] for x in word]
            self.bmaps.append(bmap)

    def bitmap_at(self, i):
        return self.bmaps[i]

    def score(self, word):
        # incomplete pattern
        if '.' in word:
            return 0
        # any novel events assumed to be themers = 100 pts
        return self.scores.get(word, 100)

    def idx(self, length):
        return self.len_idx.get(length, len(self))

def char_to_bitmap(x):
    if x == '#':
        return 0
    return ord(x.lower()) - ord('a')

def bitmap_to_char(x):
    return chr(x + ord('a'))

char_bitmap_table = [0] * 256
for i in range(256):
    char_bitmap_table[i] = char_to_bitmap(chr(i))

def all_chars():
    return (1 << 27) - 1

class Cell:
    valid_letters = 0
    across_entry = None
    across_offset = 0
    down_entry = None
    down_offset = 0
    value = '.'
    cell_id = 0

    def __init__(self, cell_id, value):
        self.value = value
        self.cell_id = cell_id
        self._reset_valid()

    def __repr__(self):
        return self.value

    def _reset_valid(self):
        if self.value != '.':
            self.valid_letters = (1 << char_bitmap_table[ord(self.value)])
        else:
            self.valid_letters = all_chars()

    def set(self, value):
        self.value = value
        self._reset_valid()

    def valid_letters_str(self):
        valid = []
        for ch in string.ascii_lowercase:
            if (1 << char_to_bitmap(ch)) & self.valid_letters:
                valid.append(ch)
        return ''.join(valid)

    def checkpoint(self):
        return [self.value, self.valid_letters]

    def restore(self, state):
        self.value = state[0]
        self.valid_letters = state[1]

    def cross_entry(self, entry):
        if entry == self.across_entry:
            return self.down_entry
        return self.across_entry

    def valid_letters_bitmap(self):
        return self.valid_letters;

    def apply_letter_mask(self, valid):
        self.valid_letters &= valid

class Entry:

    def __init__(self, cells, length, direction, wordlist, grid):
        self.cells = cells
        self.wordlist = wordlist
        self.grid = grid
        self.length = length
        self.direction = None
        self.valid_words = None
        self.fill_idx = 0
        self.saved_valid_words = None

        self.reset_dict()
        self.satisfy()

    def reset_dict(self):
        start_pos = self.wordlist.idx(self.length)
        end_pos = self.wordlist.idx(self.length + 1)
        self.valid_words = range(start_pos, end_pos)

    def set(self, word):
        self.reset_dict()
        for i, c in enumerate(self.cells):
            c.set(word[i])
        self.satisfy()

    def score(self):
        return self.wordlist.score(self.cell_pattern())

    def cell_pattern(self):
        return ''.join([x.value for x in self.cells]).lower()

    def bitmap_pattern(self):
        return [x.valid_letters_bitmap() for x in self.cells]

    def completed(self):
        pattern = self.cell_pattern()
        return '.' not in pattern

    def checkpoint(self):
        return [self.valid_words[:], self.fill_idx]

    def restore(self, state):
        self.valid_words = state[0]
        self.fill_idx = state[1]

    def _recompute_valid_letters(self):
        if self.completed():
            pattern = self.cell_pattern()
            fills = [[ 1 << char_bitmap_table[ord(x)] for x in pattern ]]
        else:
            fills = [self.wordlist.bitmap_at(i) for i in self.valid_words]

        for i in range(self.length):
            valid_letters = 0
            for fill in fills:
                valid_letters |= fill[i]
            self.cells[i].apply_letter_mask(valid_letters)

    def est_fills(self, word):
        values = [v.value for v in self.cells]
        for i, cell in enumerate(self.cells):
            cell.value = word[i]

        self.satisfy()
        count = self.num_fills()

        for i, cell in enumerate(self.cells):
            cell.value = values[i]
        return count

    def has_fill(self):
        return self.fill_idx < len(self.valid_words) and len(self.valid_words)

    def fill(self, offs):
        if self.fill_idx >= len(self.valid_words):
            return None

        if offs:
            self.valid_words = [self.valid_words[offs]] + self.valid_words[0:offs] + self.valid_words[offs+1:]

        fill = self.wordlist[self.valid_words[self.fill_idx]][0]
        self.fill_idx += 1

        for i, cell in enumerate(self.cells):
            cell.value = fill[i]

        return fill

    def satisfy(self):
        global satisfy_ct
        satisfy_ct += 1

        pattern = self.bitmap_pattern()

        orig_len = len(self.valid_words)
        valid_words = []
        for i in self.valid_words:
            word_score = self.wordlist[i]
            word, score = word_score

            if word in self.grid.used_words:
                continue

            if len(word) != len(pattern):
                continue

            skip = False
            bitmap = self.wordlist.bitmap_at(i)
            for j, x in enumerate(pattern):
                if not (x & bitmap[j]):
                    skip = True
                    break
            if skip:
                continue

            valid_words.append(i)

        self.valid_words = valid_words
        self._recompute_valid_letters()
        return orig_len != len(self.valid_words)


    def num_fills(self):
        if self.completed():
            return 1
        return len(self.valid_words)

    def fills(self):
        return [self.wordlist[i][0] for i in self.valid_words]

    def __repr__(self):
        fills = [self.wordlist[i][0] for i in self.valid_words]
        pattern = self.cell_pattern()
        count = len(fills)
        if '.' not in pattern:
            count = 1
        disp_fills = fills[self.fill_idx:self.fill_idx + 10]
        if pattern == 'b.s..':
            disp_fills = fills
        return '<%s, %d, %d, %s>' % (pattern, count, self.fill_idx, disp_fills)


class Grid:

    def __init__(self, tmpl, wordlist):
        rows = tmpl.strip().split()
        self.height = len(rows)
        self.width = len(rows[0])
        self.cells = [None] * self.height
        self.entries = []
        self.used_words = set()

        for y in range(self.height):
            self.cells[y] = []
            for x in range(self.width):
                cell = Cell(y * self.width + x, rows[y][x])
                self.cells[y].append(cell)

        for y in range(self.height):
            for x in range(self.width):

                is_black = rows[y][x] == '#'

                start_of_xentry = ((not is_black) and
                               (x == 0 or rows[y][x-1] == '#') and
                               (x + 1 < self.width and rows[y][x+1] != '#'))
                start_of_yentry = ((not is_black) and
                               (y == 0 or rows[y-1][x] == '#') and
                               (y + 1 < self.height and rows[y+1][x] != '#'))

                if start_of_xentry:
                    for l in range(x, self.width):
                        if rows[y][l] == '#':
                            break
                    if rows[y][l] != '#':
                        l += 1
                    cell_list = []
                    for i in range(x, l):
                        cell_list.append(self.cells[y][i])
                    entry = Entry(cell_list, l - x, 'A', wordlist, self)
                    self.entries.append(entry)
                    for i in range(x, l):
                        self.cells[y][i].across_entry = entry
                        self.cells[y][i].across_offset = i - x

                if start_of_yentry:
                    for l in range(y, self.height):
                        if rows[l][x] == '#':
                            break
                    if rows[l][x] != '#':
                        l += 1
                    cell_list = []
                    for i in range(y, l):
                        cell_list.append(self.cells[i][x])

                    entry = Entry(cell_list, l - y, 'D', wordlist, self)
                    self.entries.append(entry)
                    for i in range(y, l):
                        self.cells[i][x].down_entry = entry
                        self.cells[i][x].down_offset = i - y

    def copy(self, wordlist=None):
        if not wordlist:
            wordlist = self.entries[0].wordlist
        return Grid(self.__repr__(), wordlist)

    def num_fills(self):
        count_fills = [x.num_fills() for x in self.entries]
        if 0 in count_fills:
            return 0
        num = sum(count_fills)
        if num == len(self.entries):
            return 1
        return num

    def satisfy_all(self):
        ct = 0
        changed = True
        while changed:
            ct += 1
            changed = False
            for entry in self.entries:
                this_changed = entry.satisfy()
                changed = changed or this_changed

    def get_next_fill_victim(self):

        # find first unfilled down
        if False:
            for row in self.cells:
                for cell in row:
                    if cell.down_entry and not cell.down_entry.completed():
                        # pick across or down, whichever has least fills
                        afills = cell.across_entry.num_fills()
                        dfills = cell.down_entry.num_fills()
                        return cell.down_entry if (dfills < afills or cell.across_entry.completed()) else cell.across_entry

        # find longest entry with fewest fills
        nfills = -1
        best = self.entries[0]
        for entry in self.entries:
            this_fills = entry.num_fills()
            if entry.completed():
                continue
            if nfills == -1 or this_fills < nfills:
            # if (entry.length > best.length or
            #    (entry.length == best.length and (nfills == -1 or this_fills < nfills))):
                best = entry
                nfills = entry.num_fills()

        if best.completed() or best.num_fills() == 0:
            return None
        return best

    def completed(self):
        for entry in self.entries:
            if not entry.completed():
                return False
        return True

    def __repr__(self):
        s = ''
        for y in range(self.height):
            for x in range(self.width):
                s += str(self.cells[y][x])
            s += '\n'
        return s

    def scored_entries(self):
        return sorted(self.entries, key = lambda x: x.score())

    def score(self):
        return sum([e.score() for e in self.entries])

    def find_entry(self, text):
        for x in self.entries:
            if text == x.cell_pattern():
                return x
        return None

    def fill(self, interactive=False):

        stack = []

        entry = self.get_next_fill_victim()
        if not entry:
            return 0

        self.satisfy_all()

        stack.append([entry, [], [], None])

        while stack:

            entry, saved_entries, saved_cells, fill = stack.pop()

            if fill:
                self.used_words.remove(fill)
                for y, row in enumerate(saved_cells):
                    for x, v in enumerate(row):
                        self.cells[y][x].restore(v)

                    for i, e in enumerate(self.entries):
                        e.restore(saved_entries[i])
                entry.fill_idx += 1

            if not entry.has_fill():
                # no words left, unwind
                stack.pop()
                print 'no fills, trying again for %s' % stack[-1][0]
                continue

            # fill next best word
            print 'filling %s...' % entry

            # save snapshot of entries and cells (wordlist, bitmaps)
            saved_entries = [x.checkpoint() for x in self.entries]

            saved_cells = [None] * self.height
            for y in range(self.height):
                saved_cells[y] = [x.checkpoint() for x in self.cells[y]]

            # get next best word, increment internal pointer
            fill = entry.fill(0)

            # mark this word used
            print 'selected %s...' % fill
            self.used_words.add(fill)
            print 'grid:\n%s' % self

            # save a copy in case we have to unwind
            stack.append([entry, saved_entries, saved_cells, fill])

            self.satisfy_all()

            # and fill next level down
            entry = self.get_next_fill_victim()
            if not entry:
                if self.completed():
                    return 1

                print 'no fills, trying again for %s' % stack[-1][0]
                continue

            stack.append([entry, [], [], None])

            # num_fills == 0, try next word in the list
            #print '\n'.join([str(x) for x in self.entries])

        # tried all stack levels, quit
        return 0


def main(tmpl, opts):
    words = Wordlist('XwiWordList.txt')
    print words[0:10]
    grid = Grid(tmpl, words)
    print grid.num_fills()
    print '\n'.join([str(x) for x in grid.entries])

    grid.fill(interactive=opts.interactive)
    print 'grid:\n%s' % grid
    print 'score:\n%d' % grid.score()
    print 'sat: %d' % satisfy_ct

if __name__ == "__main__":
    parser = OptionParser(usage="%prog [--interactive] template")
    parser.add_option('-i', '--interactive', action='store_true')
    (opts, args) = parser.parse_args()
    tmpl = open(args[0]).read()
    main(tmpl, opts)
