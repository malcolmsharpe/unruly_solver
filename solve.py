from collections import defaultdict
import os
import os.path
import subprocess
import sys

game_id = sys.stdin.read().strip()

params_s, board_s = game_id.split(':')
width, height = map(int, params_s.split('x'))

specified = []
pos = 0
for ch in board_s[:-1]:
    if ch.lower() == 'z':
        pos += 25
    else:
        pos += ord(ch.lower()) - ord('a')
        val = int(ch.isupper())
        specified.append( (pos // width, pos % width, val) )
        pos += 1

grid = [['.']*width for i in range(height)]
for (row, col, val) in specified:
    grid[row][col] = ['W', 'B'][val]

print('Read board:')
print('width %d x height %d' % (width, height))
for row in grid:
    print(''.join(row))


def ensure_tmp_dir():
    try:
        os.mkdir('tmp')
    except OSError:
        assert os.path.exists('tmp')

scip = './scip'

if not os.path.exists(scip):
    print('Did not find (link to) SCIP executable at expected path %s' % scip)
    sys.exit(1)

def solve():
    ensure_tmp_dir()

    ip_path = 'tmp/ip.lp'
    sol_path = 'tmp/ip_sol.log'
    stdout_path = 'tmp/stdout.txt'
    stderr_path = 'tmp/stderr.txt'

    # Clear the old solution (if any).
    open(sol_path, 'w')

    lp_f = open(ip_path, 'w')

    adj = defaultdict(lambda: [])

    lp_f.write('min\n')
    lp_f.write('  0\n')

    lp_f.write('st\n')
    lp_f.write('\n')

    for (row, col, val) in specified:
        lp_f.write('  x_{%d,%d} = %d\n' % (row, col, val))
    lp_f.write('\n')

    for r in range(height):
        line = [' ']
        for c in range(width):
            line.append('+ x_{%d,%d}' % (r, c))
        line.append('= %d' % (width / 2))
        lp_f.write(' '.join(line) + '\n')
    lp_f.write('\n')

    for c in range(width):
        line = [' ']
        for r in range(height):
            line.append('+ x_{%d,%d}' % (r, c))
        line.append('= %d' % (height / 2))
        lp_f.write(' '.join(line) + '\n')
    lp_f.write('\n')

    for r in range(height):
        for c in range(width - 2):
            line = [' ']
            for dc in range(3):
                line.append('+ x_{%d,%d}' % (r,c+dc))
            lp_f.write(' '.join(line + [' <= 2']) + '\n')
            lp_f.write(' '.join(line + [' >= 1']) + '\n')
    lp_f.write('\n')

    for r in range(height - 2):
        for c in range(width):
            line = [' ']
            for dr in range(3):
                line.append('+ x_{%d,%d}' % (r+dr,c))
            lp_f.write(' '.join(line + [' <= 2']) + '\n')
            lp_f.write(' '.join(line + [' >= 1']) + '\n')
    lp_f.write('\n')

    lp_f.write('binary\n')
    for r in range(height):
        for c in range(width):
            lp_f.write('  x_{%d,%d}\n' % (r,c))
    lp_f.write('end\n')

    lp_f.close()

    subprocess.check_call( [scip, '-f', ip_path, '-l', sol_path],
        stdout=open(stdout_path, 'w'), stderr=open(stderr_path, 'w') )

    output = list(open(sol_path))
    success = False
    opt = 0
    for line in output:
        if 'SCIP Status' in line:
            if 'infeasible' in line:
                return None
            if 'optimal solution found' in line:
                success = True

        if 'objective value:' in line:
            opt = int(line.split()[-1])

    assert success

solve()
