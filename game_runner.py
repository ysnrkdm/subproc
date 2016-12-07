import subprocess
import re
import board


class Player:

    def __init__(self, path, default_name):
        self.proc = subprocess.Popen(path, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.name = default_name
        self.default_name = default_name
        self.debug = False

    def go(self):
        self.proc.stdin.write('go\n')
        output = self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output = re.sub(r'[\r\n]+', "", output)
        print output.rstrip()
        # X plays XX
        b = re.findall(r">(.+) plays [WB]?([a-zA-Z][0-9]|PS)", output.rstrip())
        # If self.name is unset, extract name from answer by engine and set it
        if len(self.name) == 0 or self.name == self.default_name:
            self.name = b[0][0]
        if self.debug:
            print b
        return b[0][1]

    def init(self):
        self.proc.stdin.write('init\n')
        output = self.proc.stdout.readline()
        if self.debug:
            print output.rstrip()

    def play(self, hand):
        if self.debug:
            print hand
        self.proc.stdin.write(hand + '\n')
        output = self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        if self.debug:
            print output.rstrip()
        # X play XX
        a = re.findall(r"(.+) play ([a-zA-Z][0-9]|PS|ps)", output.rstrip())
        if self.debug:
            print a
        return a[0][1]

    def end_process(self):
        self.proc.stdin.write('quit\n')
        output = self.proc.stdout.readline()
        if self.debug:
            print output.rstrip()
        remainder = self.proc.communicate()[0]
        if self.debug:
            print remainder
        # The proc should not be used after calling quit

    def show_hamlet_param(self):
        self.proc.stdin.write('verbose p\n')
        output = self.proc.stdout.readline()

        b = output.rstrip()
        self.proc.stdin.write('verbose 0\n')

        return b

    def show(self, verbose):
        self.proc.stdin.write('verbose 1\n')
        output = self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        output += self.proc.stdout.readline()
        if verbose:
            print output.rstrip()

        b = re.findall(r'.*(Black|White|black|white) won.*', output.rstrip())
        self.proc.stdin.write('verbose 0\n')
        output = self.proc.stdout.readline()
        a = re.findall(r'.*(Game Over).*', output.rstrip())
        won = "None"
        if len(b):
            if len(b[0]):
                won = b[0]

        return len(a) > 0, won


class GameRunner:

    def __init__(self, proc_black_path, proc_white_path, game_recorder, debug):
        print 'Starting engines...'
        proc_black = Player(proc_black_path, 'proc_black')
        proc_black.debug = debug
        proc_white = Player(proc_white_path, 'proc_b')
        proc_white.debug = debug
        print 'Engines started. Game starting:'

        self.proc_black = proc_black
        self.proc_white = proc_white
        self.recorder = game_recorder

    def extract_hamlet_param(self):
        if self.proc_black.name == 'Hamlet':
            return self.proc_black.show_hamlet_param()
        elif self.proc_white.name == 'Hamlet':
            return self.proc_white.show_hamlet_param()
        else:
            return 'No Hamlet'

    def play_a_game(self):
        self.proc_black.init()
        self.proc_white.init()

        game_board = board.Board()
        self.recorder.add(game_board)
        print game_board

        is_game_over = game_board.is_game_over()

        while not is_game_over:
            # Process A's turn
            ha = self.proc_black.go().lower()
            game_board.put_s(ha)
            print game_board
            self.recorder.add(game_board)
            self.proc_white.play(ha)

            is_game_over = game_board.is_game_over()
            if is_game_over:
                break

            # Process B's turn
            hb = self.proc_white.go().lower()
            game_board.put_s(hb)
            print game_board
            self.recorder.add(game_board)
            self.proc_black.play(hb)

            is_game_over = game_board.is_game_over()
            if is_game_over:
                break

        self.recorder.add_meta({'proc_a': self.proc_black.name, 'prob_b': self.proc_white.name,
                                'hamletparam': self.extract_hamlet_param()})

        self.proc_black.end_process()
        self.proc_white.end_process()

        self.recorder.store()

        if game_board.n_black() > game_board.n_white():
            won = "Black"
        elif game_board.n_black() < game_board.n_white():
            won = "White"
        else:
            won = "None"

        return won
