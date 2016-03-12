import game_runner
import game_recorder
from ConfigParser import SafeConfigParser
import sys


def main():
    filename = sys.argv[1]
    parser = SafeConfigParser()
    parser.read(filename)

    proc_a_path = parser.get('proc', 'a_path')
    proc_b_path = parser.get('proc', 'b_path')

    text_output_path = parser.get('textrecorder', 'output_path')

    recorder = game_recorder.FlatFileRecorder()
    recorder.configure('', '', {'output_path': text_output_path})

    recorder = game_recorder.RedisRecorder()
    recorder.configure('', '', {
        'host': 'localhost', 'port': 6379, 'db': 0,
        'hostcount': 'localhost', 'portcount': 6379, 'dbcount': 1,
        'dbkeyprefix': 'othellobook'
    })

    gr = game_runner.GameRunner(proc_a_path, proc_b_path, recorder)

    won = gr.play_a_game()

    print "Game Over! " + won + " won!\n"

if __name__ == '__main__':
    main()