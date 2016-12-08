import game_runner
import sys
import config
import random


def get_game_recorder(conf):
    mod = __import__(conf['game_recorder_from'], fromlist=[conf['game_recorder_class']])
    class_def = getattr(mod, conf['game_recorder_class'])
    obj = class_def()
    obj.configure('', '', conf)
    return obj


def do_match(conf):
    proc_a = {
        "path": conf['proc_a_path'],
        "n_rand_hands": int(conf.get('proc_n_rand_hands_for_a', '0')),
    }
    proc_b = {
        "path": conf['proc_b_path'],
        "n_rand_hands": int(conf.get('proc_n_rand_hands_for_b', '0')),
    }

    debug = conf.get('proc_debug', '0') == '1'
    randomize_black_white = conf.get('proc_randomize_black_white', '0') == '1'

    if randomize_black_white and random.randrange(2) == 1:
        proc_a, proc_b = proc_b, proc_a

    with get_game_recorder(conf) as recorder:
        gr = game_runner.GameRunner(proc_a['path'], proc_b['path'],
                                    recorder, debug,
                                    proc_a['n_rand_hands'], proc_b['n_rand_hands'])
        won, player_name = gr.play_a_game()
        print "Game Over! " + won + ':' + player_name + " won!\n"


def main():
    filename = sys.argv[1]
    conf = config.config_by_filename(filename)
    do_match(conf)


if __name__ == '__main__':
    main()