import game_runner
import game_recorder


def main():
    black_won = 0
    white_won = 0

    for i in range(1):
        proc_a_path = '/Users/Yoshinori/Documents/OneDrive/projects/othello/edax/4.3.2/bin/mEdax -q -l 1'
        proc_b_path = '/Users/Yoshinori/Documents/OneDrive/codes/FlatReversi/Hamlet/dist/build/Hamlet/Hamlet'
        recorder = game_recorder.FlatFileRecorder()
        recorder.configure('', '', {'output_path': '/Users/Yoshinori/Documents/OneDrive/codes/FlatReversi/subproc'})
        gr = game_runner.GameRunner(proc_a_path, proc_b_path, recorder)

        won = gr.play_a_game()

        print "Game Over! " + won + " won!\n"
        if won == "Black":
            black_won += 1
        else:
            white_won += 1

    print "Result:\n"
    print "Black wons: " + str(black_won) + ", White wons: " + str(white_won) + "\n"


if __name__ == '__main__':
    main()