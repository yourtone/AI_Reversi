import argparse, copy, signal, sys, timeit, imp, traceback
from board import Board, move_string, print_moves

player = {-1 : "Black", 1 : "White"}

def game(black_engine, white_engine, game_time=60.0, verbose=False):
    """ Run a single game. Raise RuntimeError in the event of time expiration.
    Raise LookupError in the case of a bad move. The tournament engine must
    handle these exceptions. """

    # Initialize variables
    board = Board()
    totaltime = { -1 : game_time*60, 1 : game_time*60 }
    engine = { -1 : black_engine, 1 : white_engine }

    if verbose:
        print "INITIAL BOARD\n--\n"
        board.display(totaltime)

    # Do rounds
    for move_num in range(60):
        moves = []
        for color in [-1, 1]:
            start_time = timeit.default_timer()
            move = get_move(board, engine[color], color, move_num, totaltime)
            end_time = timeit.default_timer()
            # Update user totaltime
            time = round(end_time - start_time, 1)
            totaltime[color] -= time

            if time > game_time or totaltime[color] < 0:
                raise RuntimeError(color)

            # Make a move, otherwise pass
            if move is not None:
                board.execute_move(move, color)
                moves.append(move)

                if verbose:
                    print(("--\n\nRound {}: {} plays in {}\n"
                        ).format(str(move_num + 1), player[color], move_string(move)))
                    board.display(totaltime)

        if not moves:
            # No more legal moves. Game is over.
            break

    print "FINAL BOARD\n--\n"
    board.display(totaltime)

    return board

def get_move(board, engine, color, move_num, time, **kwargs):
    """ Get the move for the given engine and color. Check validity of the
    move. """
    legal_moves = board.get_legal_moves(color)

    if not legal_moves:
        return None
    elif len(legal_moves) == 1:
        return legal_moves[0]
    else:
        try:
            move = engine.get_move(copy.deepcopy(board), color, move_num, time[color], time[-color])
        except Exception, e:
            print traceback.format_exc()
            raise SystemError(color)

        if move not in legal_moves:
            print "legal list", [move_string(m) for m in legal_moves]
            print "illegal", move_string(move), "=", move
            raise LookupError(color)

        return move

def winner(board):
    """ Determine the winner of a given board. Return the points of the two
    players. """
    black_count = board.count(-1)
    white_count = board.count(1)
    if black_count > white_count:
        #if black_count + white_count != 64:
        #    black_count += (64 - black_count - white_count)
        return (-1, black_count, white_count)
    elif white_count > black_count:
        #if black_count + white_count != 64:
        #    white_count += (64 - black_count - white_count)
        return (1, black_count, white_count)
    else:
        return (0, black_count, white_count)

def signal_handler(signal, frame):
    """ Capture SIGINT command. """
    print '\n\n- You quit the game!'
    sys.exit()

TRIAL = 2
def main(player_engine_1, player_engine_2, game_time, verbose):
    try:
        wins_1 = wins_2 = ties = 0

        #player[-1] = player[-1][:-8]
        #player[1] = player[1][:-8]

        for i in range(int(TRIAL/2)):
            print(("NEW GAME\nBlack: {}\nWhite: {}").format(player[-1], player[1]))
            board = game(player_engine_2, player_engine_1, game_time, verbose)
            stats = winner(board)
            bscore = str(stats[1])
            wscore = str(stats[2])
            if stats[0] == -1:
                wins_2 += 1
                print(("- {} wins the game! ({}-{})").format(player[-1], bscore, wscore))
            elif stats[0] == 1:
                wins_1 += 1
                print(("- {} wins the game! ({}-{})").format(player[1], wscore, bscore))
            else:
                ties += 1
                print(("- {} and {} are tied! ({}-{})").format(player[-1], player[1], bscore, wscore))
            print(('{:<10}{:d}\n{:<10}{:d}\n{:<10}{:d}'
                ).format(player[-1], wins_2, player[1], wins_1, "Ties", ties))

        player[-1], player[1] = player[1], player[-1]
        for i in range(int(TRIAL/2), TRIAL):
            print(("NEW GAME\nBlack: {}\nWhite: {}").format(player[-1], player[1]))
            board = game(player_engine_1, player_engine_2, game_time, verbose)
            stats = winner(board)
            bscore = str(stats[1])
            wscore = str(stats[2])
            if stats[0] == -1:
                wins_1 += 1
                print(("- {} wins the game! ({}-{})").format(player[-1], bscore, wscore))
            elif stats[0] == 1:
                wins_2 += 1
                print(("- {} wins the game! ({}-{})").format(player[1], wscore, bscore))
            else:
                ties += 1
                print(("- {} and {} are tied! ({}-{})").format(player[-1], player[1], bscore, wscore))
            print(('{:<10}{:d}\n{:<10}{:d}\n{:<10}{:d}'
                ).format(player[1], wins_2, player[-1], wins_1, "Ties", ties))

        player[-1], player[1] = player[1], player[-1]
        print(('\n========== FINAL REPORT ==========\n{:<10}{:d}\n{:<10}{:d}\n{:<10}{:d}'
            ).format(player[-1], wins_2, player[1], wins_1, "Ties", ties))

        return None

    except RuntimeError, e:
        print(("\n- {} ran out of time!\n{} wins the game! (64-0)"
            ).format(player[e[0]], player[e[0]*-1]))
        if e[0] == -1:
            return (1, 0, 64)
        else:
            return (-1, 64, 0)

    except LookupError, e:
        print(("\n- {} made an illegal move!\n{} wins the game! (64-0)"
            ).format(player[e[0]], player[e[0]*-1]))
        if e[0] == -1:
            return (1, 0, 64)
        else:
            return (-1, 64, 0)

    except SystemError, e:
        print(("\n- {} ended prematurely because of an error!\n{} wins the game! (64-0)"
            ).format(player[e[0]], player[e[0]*-1]))
        if e[0] == -1:
            return (1, 0, 64)
        else:
            return (-1, 64, 0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    # Automatically generate help and usage messages.
    # Issue errors when users gives the program invalid arguments.
    parser = argparse.ArgumentParser(description="Play the Othello game with different engines.")
    parser.add_argument("-black_engine", type=str, nargs=1, help="black engine (human, eona, greedy, nonull, random)")
    parser.add_argument("-white_engine", type=str, nargs=1, help="white engine (human, eona, greedy, nonull, random)")
    parser.add_argument("-mB", action="store_true", help="turn on alpha-beta pruning for the black player")
    parser.add_argument("-mW", action="store_true", help="turn on alpha-beta pruning for the white player")
    parser.add_argument("-t", type=int, action="store", help="adjust time limit", default=60)
    parser.add_argument("-v", action="store_true", help="display the board on each turn")
    args = parser.parse_args();

    engine_name_1 = args.white_engine[0]
    engine_name_2 = args.black_engine[0]
    player[1] = engine_name_1
    player[-1] = engine_name_2

    try:
        engines_1 = __import__('engines.' + engine_name_1)
        engines_2 = __import__('engines.' + engine_name_2)
        engine_1 = engines_1.__dict__[engine_name_1].__dict__['engine']()
        engine_2 = engines_2.__dict__[engine_name_2].__dict__['engine']()

        if (engine_name_1 != "greedy" and engine_name_1 != "human" and engine_name_1 != "random"):
            engine_1.alpha_beta = not args.mW
        if (engine_name_2 != "greedy" and engine_name_2 != "human" and engine_name_2 != "random"):
            engine_2.alpha_beta = not args.mB

        #print(("{} vs. {}\n").format(player[-1], player[1]))
        v = (args.v or engine_name_1 == "human" or engine_name_2 == "human")
        main(engine_1, engine_2, game_time=args.t, verbose=v)

    except ImportError, e:
        print(('Unknown engine -- {}').format(e[0].split()[-1]))
        sys.exit()
