import subprocess
import re
import board
import random

N_RAND_HAND_UNTIL = 10


class Player:

    def __init__(self, path, default_name):
        self.proc = subprocess.Popen(path, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.name = default_name
        self.default_name = default_name
        self.debug = False
        self.n_rand_hands = 0
        self.n_rand_rest = 0

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

    def __init__(self, proc_black_path, proc_white_path, game_recorder, debug, n_rand_hands_for_black, n_rand_hands_for_white):
        print 'Starting engines...'
        proc_black = Player(proc_black_path, 'proc_black')
        proc_black.debug = debug
        proc_white = Player(proc_white_path, 'proc_white')
        proc_white.debug = debug
        print 'Engines started. Game starting:'

        # Randomization - done in first 10 hands.
        proc_black.n_rand_hands = n_rand_hands_for_black
        proc_white.n_rand_hands = n_rand_hands_for_white
        proc_black.n_rand_rest = min(n_rand_hands_for_black, N_RAND_HAND_UNTIL)
        proc_white.n_rand_rest = min(n_rand_hands_for_white, N_RAND_HAND_UNTIL)

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

    def go_for(self, game_board, proc):
        if proc.n_rand_rest > 0:
            if random.randrange(proc.n_rand_rest) == 0:
                # Puttables
                puttables = game_board.puttables(game_board.turn)
                n_puttables = len(puttables)
                if n_puttables > 0:
                    ha_x, ha_y = puttables[random.randrange(n_puttables)]
                    hand = game_board.handstr_from_coord(ha_x, ha_y)
                    proc.n_rand_rest -= 1
                    print '>> subproc plays %s in place of %s (%d/%d)' % (
                        hand,
                        proc.name,
                        proc.n_rand_hands - proc.n_rand_rest,
                        proc.n_rand_hands
                    )
                    proc.play(hand)
                    return hand

        return proc.go().lower()

    def play_a_turn(self, game_board, proc_attacker, proc_defender):
        # Process Black's turn
        ha = self.go_for(game_board, proc_attacker)
        game_board.put_s(ha)
        print game_board
        self.recorder.add(game_board)
        proc_defender.play(ha)

        is_game_over = game_board.is_game_over()
        return is_game_over

    def play_a_game(self):
        self.proc_black.init()
        self.proc_white.init()

        game_board = board.Board()
        self.recorder.add(game_board)
        print game_board

        is_game_over = game_board.is_game_over()

        while not is_game_over:
            # Process Black's turn
            is_game_over = self.play_a_turn(game_board, self.proc_black, self.proc_white)
            if is_game_over:
                break

            # Process White's turn
            is_game_over = self.play_a_turn(game_board, self.proc_white, self.proc_black)
            if is_game_over:
                break

        self.recorder.add_meta({'proc_a': self.proc_black.name, 'proc_b': self.proc_white.name,
                                'hamletparam': self.extract_hamlet_param()})

        self.proc_black.end_process()
        self.proc_white.end_process()

        self.recorder.store()

        if game_board.n_black() > game_board.n_white():
            won = ("Black", self.proc_black.name)
        elif game_board.n_black() < game_board.n_white():
            won = ("White", self.proc_white.name)
        else:
            won = ("None", '')

        return won
