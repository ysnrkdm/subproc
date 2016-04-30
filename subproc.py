import game_runner
import sys
import config


def get_game_recorder(conf):
    mod = __import__(conf['game_recorder_from'], fromlist=[conf['game_recorder_class']])
    class_def = getattr(mod, conf['game_recorder_class'])
    obj = class_def()
    return obj


def do_match(conf):
    proc_a_path = conf['proc_a_path']
    proc_b_path = conf['proc_b_path']

    # text_output_path = parser.get('textrecorder', 'output_path')
    # recorder = game_recorder.FlatFileRecorder()
    # recorder.configure('', '', {'output_path': text_output_path})

    recorder = get_game_recorder(conf)
    recorder.configure('', '', {
        'host': conf['redis_hostname'], 'port': conf['redis_port'], 'db': conf['redis_db_book'],
        'password': conf['redis_password'],
        'dbkeyprefix': 'othellobook'
    })

    gr = game_runner.GameRunner(proc_a_path, proc_b_path, recorder)

    won = gr.play_a_game()

    print "Game Over! " + won + " won!\n"


def main():
    filename = sys.argv[1]
    conf = config.config_by_filename(filename)
    do_match(conf)


if __name__ == '__main__':
    main()