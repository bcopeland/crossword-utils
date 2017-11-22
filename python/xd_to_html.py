#!/usr/bin/python
from xdfile import xdfile
from optparse import OptionParser

def xd_to_html(filename, answers=False):
    xd = xdfile(open(filename).read())

    title = 'unknown'
    author = 'unknown'

    filename_noext = filename.split(".")[0]

    for h in xd.headers:
        if h[0] == 'Title':
            title = h[1]

    html = '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN"
  "http://www.w3.org/TR/REC-html40/loose.dtd">
<html>
<head>
  <title>''' + title + '''</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
  <script type="text/javascript" src="lib/jquery.min.js"></script>
  <script type="text/javascript" src="lib/jquery.hotkeys.js"></script>
  <script type="text/javascript" src="lib/jquery.cookie.js"></script>
  <script type="text/javascript" src="xd.js"></script>
  <script type="text/javascript" src="crossword.js"></script>
  <script type="text/javascript">
  $(function() {
    var crossword;
    crossword = new Crossw1rd('container');
    crossword.init("''' + filename_noext + '''");
  });
  </script>
</head>
<body>
<div id="container">
'''
    grid = xd.grid
    maxx = len(grid[0])
    maxy = len(grid)

    html += '''<div id="cross1wrd" style="height:%spx;width:%spx">''' % (maxy * 28 + 6, 200 + maxx * 28 + 20)

    html += '''<div class="clues" style="height:%spx;width:%spx;">''' % (maxy * 28, 200)
    html += '''<h4 class="cluelabel">Across</h4>'''
    html += '''<div class="across scroll-pane" style="height:%spx;">''' % (maxy * 28 / 2 - 20)
    for xdc_tuple in xd.clues:
        dnum, c, a = xdc_tuple
        d, n = dnum
        if d == 'A':
            html += '''<p class="c%s%s">%s. %s</p>''' % (d, n, n, c)
    html += '''</div>'''
    html += '''<h4 class="cluelabel">Down</h4>'''
    html += '''<div class="down scroll-pane" style="height:%spx;">''' % (maxy * 28 / 2 - 20)
    for xdc_tuple in xd.clues:
        dnum, c, a = xdc_tuple
        d, n = dnum
        if d == 'D':
            html += '''<p class="c%s%s">%s. %s</p>''' % (d, n, n, c)
    html += '''</div>'''
    html += '''</div>'''

    html += '''<div class="grid" style="height:%spx;width:%spx;">\n''' % (
        maxy * 28, maxx * 28)

    next_n = 1
    for y in range(0, maxy):
        html += '''<div class="row">'''
        for x in range(0, maxx):
            light = grid[y][x] != '#'

            start_of_xlight = (light and
                               (x == 0 or grid[y][x-1] == '#') and
                               (x + 1 < maxx and grid[y][x+1] != '#'))
            start_of_ylight = (light and
                               (y == 0 or grid[y-1][x] == '#') and
                               (y + 1 < maxy and grid[y+1][x] != '#'))

            num = ""
            if start_of_xlight or start_of_ylight:
                num = next_n
                next_n += 1

            letter_span = ""
            if answers and light:
                letter_span = '''<span class="letter">%s</span>''' % (
                              grid[y][x])

            html += '''<div%s><span class="num">%s</span>%s</div>''' % (
                    ' class="blank"' if not light else "", num, letter_span)
        html += '''</div>\n'''

    html += '''</div>'''
    html += '''</div></div></body></html>'''
    print html

if __name__ == "__main__":
    usage="Usage: %prog [--solution] xdfile"
    parser = OptionParser(usage=usage)
    parser.add_option('-s', '--solution', action='store_true')
    (opts, args) = parser.parse_args()
    xd_to_html(args[0], answers=opts.solution)
