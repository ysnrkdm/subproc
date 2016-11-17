import subprocess
import re
import board


class GameRunner:

    def __init__(self, proc_a_path, proc_b_path, game_recorder):
        print 'Starting engines...'
        proc_a = subprocess.Popen(proc_a_path, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        proc_b = subprocess.Popen(proc_b_path, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        print 'Engines started. Game starting:'

        self.proc_a = proc_a
        self.proc_b = proc_b
        self.recorder = game_recorder
        self.proc_a_name = 'proc_a'
        self.proc_b_name = 'proc_b'
        self.hamletparam = ''

    def go(self, proc):
        proc.stdin.write('go\n')
        output = proc.stdout.readline()
        output += proc.stdout.readline()
        output += proc.stdout.readline()
        output = re.sub(r'[\r\n]+', "", output)
        print output.rstrip()
        # X plays XX
        a = re.findall(r">(.+) plays ([a-zA-Z][0-9]|PS)", output.rstrip())
        if len(self.proc_a_name) == 0 or self.proc_a_name == 'proc_a':
            self.proc_a_name = a[0][0]
        if len(a) > 0:
            # print a
            return a[0][1]
        b = re.findall(r">(.+) plays [WB]([a-zA-Z][0-9]|PS)", output.rstrip())
        if len(self.proc_b_name) == 0 or self.proc_b_name == 'proc_b':
            self.proc_b_name = b[0][0]
        # print b
        return b[0][1]

    def init(self, proc):
        proc.stdin.write('init\n')
        output = proc.stdout.readline()
        # print output.rstrip()

    def play(self, proc, hand):
	# print hand
        proc.stdin.write(hand + '\n')
        output = proc.stdout.readline()
        output += proc.stdout.readline()
        output += proc.stdout.readline()
        # print output.rstrip()
        # X play XX
        a = re.findall(r"(.+) play ([a-zA-Z][0-9]|PS|ps)", output.rstrip())
        # print a
        return a[0][1]

    def end_process(self, proc):
        proc.stdin.write('quit\n')
        output = proc.stdout.readline()
        # print output.rstrip()
        remainder = proc.communicate()[0]
        # print remainder
        # The proc should not be used after calling quit

    def hamlet_param(self, proc):
        proc.stdin.write('verbose p\n')
        output = proc.stdout.readline()

        b = output.rstrip()
        proc.stdin.write('verbose 0\n')

        return b

    # Returns true if it's game over, if not game over, returns false
    def show(self, proc, verbose):
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

    def play_a_game(self):
        self.init(self.proc_a)
        self.init(self.proc_b)

        game_board = board.Board()
        self.recorder.add(game_board)

        is_game_over = game_board.is_game_over()

        while not is_game_over:
            # Process A's turn
            ha = self.go(self.proc_a).lower()
            game_board.put_s(ha)
            print game_board
            # self.show(self.proc_a, True)
            self.recorder.add(game_board)
            self.play(self.proc_b, ha)

            is_game_over = game_board.is_game_over()
            if is_game_over:
                break

            # Process B's turn
            hb = self.go(self.proc_b).lower()
            game_board.put_s(hb)
            print game_board
            self.recorder.add(game_board)
            self.play(self.proc_a, hb)

            is_game_over = game_board.is_game_over()
            if is_game_over:
                break

        self.recorder.add_meta({'proc_a': self.proc_a_name, 'prob_b': self.proc_b_name,
                                'hamletparam': self.hamlet_param(self.proc_b)})

        self.end_process(self.proc_a)
        self.end_process(self.proc_b)

        self.recorder.store()

        if game_board.n_black() > game_board.n_white():
            won = "Black"
        elif game_board.n_black() < game_board.n_white():
            won = "White"
        else:
            won = "None"

        return won
