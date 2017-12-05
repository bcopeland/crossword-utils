#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <ctype.h>
#include <limits.h>
#include <getopt.h>
#include <time.h>
#include "list.h"
#include "util.h"

/* longest length word we can support */
#define MAX_WORD_LEN 64

enum direction {
	ACROSS = 0,
	DOWN = 1
};

#define BIT(x) (1ULL << (x))

struct word
{
	char *word;
	int score;
	uint32_t bitmap[MAX_WORD_LEN];
};

struct wordlist
{
	size_t num_words;		/* number of words in dictionary */
	struct word *words;		/* array of words in alpha/score order */
	size_t words_capacity;		/* how big words array is */
	int len_idx[MAX_WORD_LEN + 1];	/* index of words by length */
};

struct cell
{
	int cell_id;
	uint32_t valid_letters;
};

struct valid_wordlist
{
	int *words;
	size_t index;
	size_t num_words;
};

struct stack_level
{
	struct cell *saved_cells;
	struct valid_wordlist *saved_valid;
	struct entry *entry;
	struct word *filled_word;
	struct list_head list;
	bool saved;
};


static struct valid_wordlist *valid_wordlist_copy(struct valid_wordlist *dest,
						  struct valid_wordlist *src)
{
	dest->words = xmemdup(src->words,
			      src->num_words * sizeof(src->words[0]));
	dest->index = src->index;
	dest->num_words = src->num_words;
	return dest;
}

static void cell_apply_mask(struct cell *cell, uint32_t bits) {
	cell->valid_letters &= bits;
}

struct entry
{
	int entry_id;
	struct wordlist *wordlist;
	struct cell *cells[MAX_WORD_LEN];
	size_t num_cells;

	struct valid_wordlist valid;

	struct list_head list;
};

struct fill_context
{
	struct wordlist *wordlist;
	struct cell *cells;
	size_t num_cells;

	struct list_head entries;
	struct list_head stack;
	int num_entries;

	int height;
	int width;
};

static bool is_one_bit_set(uint32_t bitmap)
{
	return bitmap && !(bitmap & (bitmap - 1));
}

static char bitmap_to_char(uint32_t bitmap)
{
	char ch;

	if (!bitmap)
		return '!';

	if (is_one_bit_set(bitmap)) {
		ch = 'A' + ffs(bitmap) - 1;
		if (ch == '[')
			ch = '#';
		return ch;
	}
	return '.';
}

static uint32_t char_to_bitmap(const unsigned char ch)
{
	int lch = tolower(ch);

	if (lch == '#')
		lch = '[';

	else if (lch == '.')
		return ~0;

	return BIT(toupper(lch) - 'A');
}

static void print_word(struct word *word)
{
	printf("%s -> %d\n", word->word, word->score);
}

static void print_grid(struct fill_context *ctx)
{
	size_t x, y;
	for (y = 0; y < ctx->height; y++) {
		for (x = 0; x < ctx->width; x++) {
			putchar(bitmap_to_char(ctx->cells[ctx->width * y + x].valid_letters));
		}
		putchar('\n');
	}
}

static void print_entry(struct entry *entry)
{
	printf("%d ", entry->entry_id);
	for (int i = 0; i < entry->num_cells; i++) {
		putchar(bitmap_to_char(entry->cells[i]->valid_letters));
	}
	putchar('\n');
	for (int i = 0; i < 10 && i < entry->valid.num_words; i++) {
		print_word(&entry->wordlist->words[entry->valid.words[i]]);
	}
	putchar('\n');
}

static void print_entries(struct fill_context *ctx)
{
	struct entry *entry;
	list_for_each_entry(entry, &ctx->entries, list)
	{
		print_entry(entry);
	}
}


static void cell_init(struct cell *cell,
		      int cell_id,
		      const char cell_template)
{
	cell->cell_id = cell_id;
	cell->valid_letters = char_to_bitmap(cell_template);
}

static void entry_init(struct entry *entry,
		       int entry_id,
		       struct wordlist *wordlist,
		       struct cell **cells,
		       size_t num_cells)
{
	size_t start_idx, end_idx;
	size_t i, j;

	entry->entry_id = entry_id;
	entry->valid.index = 0;
	entry->wordlist = wordlist;

	if (num_cells > MAX_WORD_LEN)
		num_cells = MAX_WORD_LEN;

	memcpy(entry->cells, cells, num_cells * sizeof(cells[0]));
	entry->num_cells = num_cells;

	start_idx = wordlist->len_idx[num_cells];
	end_idx = wordlist->len_idx[num_cells + 1];

	entry->valid.num_words = end_idx - start_idx;
	entry->valid.words = xmalloc(entry->valid.num_words * sizeof(entry->valid.words[0]));
	for (i = start_idx, j = 0; i < end_idx; i++, j++) {
		entry->valid.words[j] = i;
	}
}

static struct word *entry_fill(struct entry *entry)
{
	int i;
	struct word *word;

	if (entry->valid.index >= entry->valid.num_words)
		return NULL;

	word = &entry->wordlist->words[entry->valid.words[entry->valid.index++]];
	for (i = 0; i < entry->num_cells; i++) {
		entry->cells[i]->valid_letters = word->bitmap[i];
	}
	return word;
}

static void entry_recompute_valid_letters(struct entry *entry)
{
	size_t i, j;
	struct word *word;

	for (i = 0; i < entry->num_cells; i++) {
		uint32_t bitmask = 0;
		for (j = 0; j < entry->valid.num_words; j++) {
			word = &entry->wordlist->words[entry->valid.words[j]];
			bitmask |= word->bitmap[i];
		}
		cell_apply_mask(entry->cells[i], bitmask);
	}
}

static bool is_completed(struct entry *entry)
{
	for (int i = 0; i < entry->num_cells; i++) {
		if (!is_one_bit_set(entry->cells[i]->valid_letters))
			return false;
	}
	return true;
}

static bool satisfy(struct entry *entry)
{
	size_t i, j;
	size_t new_index;
	struct word *word;
	bool skip;

	if (is_completed(entry))
		return false;

	/* remove any words that don't match current cell bitmaps */
	for (i = 0, new_index = 0; i < entry->valid.num_words; i++) {
		word = &entry->wordlist->words[entry->valid.words[i]];

		/* TODO inuse check */

		skip = false;
		for (j = 0; j < entry->num_cells; j++) {
			if (!(entry->cells[j]->valid_letters & word->bitmap[j])) {
				skip = true;
				break;
			}
		}
		if (!skip)
			entry->valid.words[new_index++] = entry->valid.words[i];
	}
	/* no changes */
	if (entry->valid.num_words == new_index)
		return false;

	entry->valid.num_words = new_index;
	entry_recompute_valid_letters(entry);

	return true;
}

static void satisfy_all(struct fill_context *ctx)
{
	struct entry *entry;
	bool changed = true, this_changed;

	while (changed) {
		changed = false;
		list_for_each_entry(entry, &ctx->entries, list) {
			changed |= satisfy(entry);
		}
	}
}

static int compare_len_score_alpha(const void *p1, const void *p2)
{
	const struct word *w1 = p1;
	const struct word *w2 = p2;

	size_t len1 = strlen(w1->word);
	size_t len2 = strlen(w2->word);

	/* ascending length */
	if (len1 != len2)
		return (int)len1 - (int)len2;

	/* descending score */
	if (w1->score != w2->score)
		return w2->score - w1->score;

	/* ascending alphabetical */
	return strcmp(w1->word, w2->word);
}

static void compute_bitmap(uint32_t *bitmap, const char *str)
{
	while (*str)
		*bitmap++ = char_to_bitmap((unsigned char) *str++);
}

void load_wordlist(FILE *fp, struct wordlist *out)
{
	char *line = NULL;
	char *score;
	size_t line_size = 0;
	size_t len = 0, last_len;
	ssize_t read;
	int i;

	memset(out, 0, sizeof(*out));

	while ((read = getline(&line, &line_size, fp)) != -1) {

		score = strchr(line, ';');
		if (!score)
			continue;

		*score = '\0';
		score++;

		if (strlen(line) > MAX_WORD_LEN)
			continue;

		if (out->words_capacity <= out->num_words + 1) {
			out->words_capacity *= 2;
			if (!out->words_capacity)
				out->words_capacity = 1000;
			out->words = xrealloc(out->words,
				out->words_capacity * sizeof(struct word));
		}
		out->words[out->num_words].word = xstrdup(line);
		compute_bitmap(out->words[out->num_words].bitmap, line);
		out->words[out->num_words].score = atoi(score);
		out->num_words++;
	}
	free(line);

	if (!out->num_words)
		return;

	qsort(out->words, out->num_words, sizeof(out->words[0]),
	      compare_len_score_alpha);

	last_len = strlen(out->words[0].word);
	for (i = 0; i < out->num_words; i++) {
		len = strlen(out->words[i].word);
		if (len != last_len)
			out->len_idx[len] = i;
		last_len = len;
	}
	out->len_idx[len + 1] = out->num_words;
}

struct wordlist *wordlist_new()
{
	return xcalloc(1, sizeof(struct wordlist));
}

void wordlist_free(struct wordlist *wordlist)
{
	if (!wordlist)
		return;

	for (int i = 0; i < wordlist->num_words; i++) {
		free(wordlist->words[i].word);
	}

	free(wordlist->words);
	free(wordlist);
}

static bool bitmap_match(uint32_t *bitmap, uint32_t *mask, size_t len)
{
	int i;
	for (i = 0; i < len; i++) {
		if (!(bitmap[i] & mask[i]))
			return false;
	}
	return true;
}

static char *trim(char *s)
{
	while isspace(s[strlen(s)-1])
		s[strlen(s) - 1] = '\0';
	return s;
}

static void add_entry_at(struct fill_context *ctx, char **rows,
			 int x, int y, int dir,
			 size_t maxx, size_t maxy)
{
	int xinc = (dir == ACROSS) ? 1 : 0;
	int yinc = !xinc;
	struct cell *cells[MAX_WORD_LEN];
	size_t ncells = 0;
	struct entry *entry;

	for (; x < maxx && y < maxy ; x += xinc, y += yinc)
	{
		if (rows[y][x] == '#')
			break;
		cells[ncells++] = &ctx->cells[maxx * y + x];
	}
	entry = xcalloc(1, sizeof(*entry));
	entry_init(entry, ctx->num_entries++, ctx->wordlist, cells, ncells);
	list_add_tail(&entry->list, &ctx->entries);
}

static void parse_template(struct fill_context *ctx, const char *template)
{
	char *tmp = trim(xstrdup(template));
	char **rows = xcalloc(strlen(tmp), sizeof(char *));
	char *s = tmp;
	char *token;
	size_t maxy = 0, maxx = 0, i, y, x;
	int cell_id = 0;
	int dir;
	struct entry *entry;

	while (true) {
		token = strtok(s, "\n");
		if (!token)
			break;
		s = NULL;
		token = trim(token);
		rows[maxy++] = token;
	}

	if (!maxy)
		return;

	maxx = strlen(rows[0]);
	if (maxx > MAX_WORD_LEN)
		return;

	for (y = 0; y < maxy; y++) {
		if (maxx != strlen(rows[y]))
			return;
	}

	ctx->num_cells = maxx * maxy;
	ctx->cells = xcalloc(ctx->num_cells, sizeof(ctx->cells[0]));

	for (y = 0; y < maxy; y++) {
		for (x = 0; x < maxx && x < strlen(rows[y]); x++) {
			cell_init(&ctx->cells[cell_id], cell_id, rows[y][x]);
			cell_id++;
		}
	}

	for (dir = ACROSS; dir <= DOWN; dir++) {
		int xinc = (dir == ACROSS) ? 1 : 0;
		int yinc = !xinc;

		for (y = 0; y < maxy; y++) {
			for (x = 0; x < maxx; x++) {
				/* black? */
				if (rows[y][x] == '#')
					continue;

				/* not start of a word? */
				if (!((dir == ACROSS && x == 0) ||
				      (dir == DOWN && y == 0) ||
				      rows[y - yinc][x - xinc] == '#'))
					continue;

				add_entry_at(ctx, rows, x, y, dir, maxx, maxy);
			}
		}
	}

	ctx->height = maxy;
	ctx->width = maxx;

	free(tmp);
	free(rows);
}

static bool fill_is_completed(struct fill_context *ctx)
{
	struct entry *entry;
	list_for_each_entry(entry, &ctx->entries, list) {
		if (!is_completed(entry))
			return false;
	}
	return true;
}

static bool has_fills(struct fill_context *ctx)
{
	int i;

	for (i = 0; i < ctx->num_cells; i++) {
		if (!ctx->cells[i].valid_letters)
			return false;
	}
	return true;
}

static struct stack_level *stack_level_new(struct fill_context *ctx)
{
	struct stack_level *stack;

	stack = xcalloc(1, sizeof(*stack));
	stack->saved_cells = xmalloc(ctx->num_cells * sizeof(*stack->saved_cells));
	stack->saved_valid = xmalloc(ctx->num_entries * sizeof(*stack->saved_valid));
	return stack;
}

static struct stack_level *stack_level_free(struct fill_context *ctx,
					    struct stack_level *stack)
{
	int i;
	free(stack->saved_cells);
	if (stack->saved) {
		for (i = 0; i < ctx->num_entries; i++) {
			free(stack->saved_valid[i].words);
		}
	}
	free(stack->saved_valid);
	free(stack);
}

static struct stack_level *stack_pop(struct fill_context *ctx)
{
	struct stack_level *stack_level;

	if (list_empty(&ctx->stack))
		return NULL;

	stack_level = list_last_entry(&ctx->stack, struct stack_level, list);
	list_del(&stack_level->list);
	return stack_level;
}

static void stack_push(struct fill_context *ctx, struct stack_level *stack)
{
	list_add_tail(&stack->list, &ctx->stack);
}

static void fill_init(struct fill_context *ctx, const char *template,
		      struct wordlist *wordlist)
{
	memset(ctx, 0, sizeof(*ctx));
	INIT_LIST_HEAD(&ctx->entries);
	INIT_LIST_HEAD(&ctx->stack);
	ctx->wordlist = wordlist;
	parse_template(ctx, template);
}

static void fill_destroy(struct fill_context *ctx)
{
	struct entry *entry, *tmp;
	struct stack_level *stack, *stmp;

	list_for_each_entry_safe(entry, tmp, &ctx->entries, list) {
		list_del(&entry->list);
		free(entry->valid.words);
		free(entry);
	}

	list_for_each_entry_safe(stack, stmp, &ctx->stack, list) {
		list_del(&stack->list);
		stack_level_free(ctx, stack);
	}

	free(ctx->cells);
}

static struct entry *find_next_fill_victim(struct fill_context *ctx)
{
	struct entry *entry, *best_entry = NULL;
	int min_avail = INT_MAX;
	int this_avail;

	list_for_each_entry(entry, &ctx->entries, list) {
		if (is_completed(entry))
			continue;
		this_avail = entry->valid.num_words;
		if (this_avail < min_avail) {
			min_avail = this_avail;
			best_entry = entry;
		}
	}
	return best_entry;
}

static bool fill_step(struct fill_context *ctx)
{
	int i;
	struct entry *entry;
	struct word *word;

	struct stack_level *stack = stack_pop(ctx);
	if (stack->saved) {
		memcpy(ctx->cells, stack->saved_cells,
		       ctx->num_cells * sizeof(stack->saved_cells[0]));
		list_for_each_entry(entry, &ctx->entries, list) {
			i = entry->entry_id;
			memcpy(entry->valid.words, stack->saved_valid[i].words,
			       stack->saved_valid[i].num_words *
			       sizeof(stack->saved_valid[i].words[0]));
			entry->valid.num_words = stack->saved_valid[i].num_words;
		}
	}
	if (fill_is_completed(ctx))
		return true;

	if (!has_fills(ctx)) {
		stack_level_free(ctx, stack);
		return false;
	}

	if (!stack->saved) {
		memcpy(stack->saved_cells, ctx->cells,
		       ctx->num_cells * sizeof(stack->saved_cells[0]));
		list_for_each_entry(entry, &ctx->entries, list) {
			if (stack->saved)
				free(stack->saved_valid[entry->entry_id].words);
			valid_wordlist_copy(&stack->saved_valid[entry->entry_id], &entry->valid);
		}
		stack->saved = true;
	}

	word = entry_fill(stack->entry);
	if (!word) {
		stack_level_free(ctx, stack);
		return false;
	}

	stack->filled_word = word;
	stack_push(ctx, stack);
	satisfy_all(ctx);
	stack = stack_level_new(ctx);
	stack->entry = find_next_fill_victim(ctx);
	stack_push(ctx, stack);
	return false;
}

static void randomize(struct fill_context *ctx, float amt)
{
	int i, x, y, tmp;
	struct entry *entry;

	if (amt < 0.01 || amt > 1.0)
		return;

	srand48(time(NULL));
	list_for_each_entry(entry, &ctx->entries, list) {
		int num_swaps = amt * entry->valid.num_words;
		for (i = 0; i < num_swaps; i++) {
			x = drand48() * entry->valid.num_words;
			y = drand48() * entry->valid.num_words;
			tmp = entry->valid.words[x];
			entry->valid.words[x] = entry->valid.words[y];
			entry->valid.words[y] = tmp;
		}
	}
}

static bool fill(struct fill_context *ctx)
{
	struct stack_level *stack;
	int count = 0;

	satisfy_all(ctx);
	stack = stack_level_new(ctx);
	stack->entry = find_next_fill_victim(ctx);
	stack_push(ctx, stack);

	while (!list_empty(&ctx->stack) && count++ < 200000) {
		if (fill_step(ctx)) {
			return true;
		}
	}
	return false;
}

int main(int argc, char *argv[])
{
	struct fill_context ctx;
	struct wordlist *wordlist;
	char template[(MAX_WORD_LEN + 1) * MAX_WORD_LEN + 1];
	char *dictionary = "dictionary.txt";
	size_t read;
	int i;
	int option, option_index;
	float randomize_amt = 0.0;
	static struct option long_options[] = {
		{"dict", required_argument, NULL, 'd'},
		{"randomize", required_argument, NULL, 'r'},
		{0, 0, 0, 0}
	};

	while ((option = getopt_long(argc, argv, "d:r:", long_options,
		&option_index)) != -1) {

		switch (option) {
		case 'd':
			dictionary = optarg;
			break;
		case 'r':
			randomize_amt = strtof(optarg, NULL);
			break;
		}
	}

	FILE *fp = fopen(dictionary, "r");
	if (!fp) {
		fprintf(stderr, "Could not open dictionary `%s`", dictionary);
		exit(1);
	}

	read = fread(template, 1, sizeof(template)-1, stdin);
	if (!read)
		exit(1);

	template[read] = '\0';

	wordlist = wordlist_new();
	load_wordlist(fp, wordlist);
	fill_init(&ctx, template, wordlist);
	randomize(&ctx, randomize_amt);
	satisfy_all(&ctx);

	fill(&ctx);
	print_grid(&ctx);

	wordlist_free(wordlist);
	fill_destroy(&ctx);
}
