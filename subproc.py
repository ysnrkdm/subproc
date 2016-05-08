import game_runner
import sys
import config


def get_game_recorder(conf):
    mod = __import__(conf['game_recorder_from'], fromlist=[conf['game_recorder_class']])
    class_def = getattr(mod, conf['game_recorder_class'])
    obj = class_def()
    obj.configure('', '', conf)
    return obj


def do_match(conf):
    proc_a_path = conf['proc_a_path']
    proc_b_path = conf['proc_b_path']

    with get_game_recorder(conf) as recorder:
        gr = game_runner.GameRunner(proc_a_path, proc_b_path, recorder)
        won = gr.play_a_game()
        print "Game Over! " + won + " won!\n"


def main():
    filename = sys.argv[1]
    conf = config.config_by_filename(filename)
    do_match(conf)


if __name__ == '__main__':
    main()