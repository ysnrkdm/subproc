import game_runner
import game_recorder
import sys
import config


def do_match(conf):
    proc_a_path = conf['proc_a_path']
    proc_b_path = conf['proc_b_path']

    # text_output_path = parser.get('textrecorder', 'output_path')
    # recorder = game_recorder.FlatFileRecorder()
    # recorder.configure('', '', {'output_path': text_output_path})

    recorder = game_recorder.RedisRecorder()
    recorder.configure('', '', {
        'host': conf['redis_hostname'], 'port': conf['redis_port'], 'db': conf['redis_db_book'],
        'password': conf['redis_password'],
        # 'hostcount': conf['redis_hostname'], 'portcount': conf['redis_port'], 'dbcount': conf['redis_db_book'],
        # 'passwordcount': conf['redis_password'],
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