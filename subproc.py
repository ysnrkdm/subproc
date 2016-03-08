import subprocess
import re
import board


def go(proc):
    proc.stdin.write('go\n')
    output = proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    print output.rstrip()
    # X plays XX
    a = re.findall(r"(.+) plays ([a-zA-Z][0-9]|PS)", output.rstrip())
    if len(a) > 0:
        # print a
        return a[0][1]
    b = re.findall(r"(.+) plays [WB]([a-zA-Z][0-9]|PS)", output.rstrip())
    # print b
    return b[0][1]


def init(proc):
    proc.stdin.write('init\n')
    output = proc.stdout.readline()
    print output.rstrip()


def play(proc, hand):
    proc.stdin.write(hand + '\n')
    output = proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    # print output.rstrip()
    # X play XX
    a = re.findall(r"(.+) play ([a-zA-Z][0-9]|PS)", output.rstrip())
    # print a
    return a[0][1]


def quit(proc):
    proc.stdin.write('quit\n')
    output = proc.stdout.readline()
    print output.rstrip()
    remainder = proc.communicate()[0]
    print remainder
    # The proc should not be used after calling quit


# Returns true if it's game over, if not game over, returns false
def show(proc, verbose):
    proc.stdin.write('verbose 1\n')
    output = proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    output += proc.stdout.readline()
    if verbose:
        print output.rstrip()

    b = re.findall(r'.*(Black|White|black|white) won.*', output.rstrip())
    proc.stdin.write('verbose 0\n')
    output = proc.stdout.readline()
    a = re.findall(r'.*(Game Over).*', output.rstrip())
    won = "None"
    if len(b):
        if len(b[0]):
            won = b[0]

    return len(a) > 0, won


def play_a_game():
    init(proc_a)
    init(proc_b)

    is_game_over = False

    game_board = board.Board()

    while not is_game_over:
        # Ask show boards to process A and B
        # and checks if game is over
        # (is_game_over, won) = show(proc_a, True)
        # if is_game_over:
        #     break
        # (is_game_over, won) = show(proc_b, False)
        # if is_game_over:
        #     break

        is_game_over = game_board.is_game_over()
        if is_game_over:
            break

        # Play hands of process A and B

        # Play process A
        ha = go(proc_a).lower()
        game_board.put_s(ha)
        # print game_board

        play(proc_b, ha)
        # (is_game_over, won) = show(proc_a, False)
        # if is_game_over:
        #     break
        # (is_game_over, won) = show(proc_b, False)
        # if is_game_over:
        #     break

        is_game_over = game_board.is_game_over()
        if is_game_over:
            break

        # Play process A
        hb = go(proc_b).lower()
        game_board.put_s(hb)
        print game_board

        play(proc_a, hb)

    quit(proc_a)
    quit(proc_b)

    if game_board.n_black() > game_board.n_white():
        won = "Black"
    elif game_board.n_black() < game_board.n_white():
        won = "White"
    else:
        won = "None"

    return won

black_won = 0
white_won = 0

for i in range(0,1):
    print 'Starting engines...'
    proc_a = subprocess.Popen('/Users/Yoshinori/Documents/OneDrive/projects/othello/edax/4.3.2/bin/mEdax -q -l 1', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    proc_b = subprocess.Popen('/Users/Yoshinori/Documents/OneDrive/codes/FlatReversi/Hamlet/dist/build/Hamlet/Hamlet', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    # proc_b = subprocess.Popen('/Users/Yoshinori/Documents/OneDrive/codes/FlatReversi/Hamlet/dist/build/HamletProf/HamletProf +RTS -p -RTS', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    print 'Engines started. Game starting:'

    won = play_a_game()

    print "Game Over! " + won + " won!\n"
    if won == "Black":
        black_won += 1
    else:
        white_won += 1

print "Result:\n"
print "Black wons: " + str(black_won) + ", White wons: " + str(white_won) + "\n"

