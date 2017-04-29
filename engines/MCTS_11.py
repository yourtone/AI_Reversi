import random
import time
import math
import copy
import pickle
from engines import Engine
from board import Board
import cProfile
import multiprocessing
from multiprocessing import Process, Pool, Manager


class MCTS_engine(Engine):
    def __init__(self):
        self.tree = tree()
        self.sim_time = 57  # change this attribute according to game time limit
        # self.sim_round = 1  # change this attribute according to game time limit
        self.cpu_num = 1  # the number of cpu used, useless for now
        self.num_per_process = 1
        # self.cpu_num = multiprocessing.cpu_count()

    def get_move(self, board, color, move_num=None,
                 time_remaining=None, time_opponent=None):
        self.color = color
        my_board = MyBoard()
        my_board._MyBoard__pieces = board._Board__pieces
        state = (my_board, color)  # wrap the board and color into a tuple
        # cProfile.runctx('move = self.MCS(state=copy.deepcopy(state))', globals(), locals())  # used for analysising the time used
        move = self.MCS(state=copy.deepcopy(state))  # start MC searching
        # cProfile.runctx('self.test1(board, move, self.color)', globals(), locals())  # used for analysising the time used
        return move

    def MCS(self, state):
        root = self.tree.getNode(state=state)
        root.parent = None
        sim_num = 0
        start_time = time.time()
        while time.time() - start_time < self.sim_time:  # you can choose to use simulating time limit or simulating rounds limit
            # while sim_num < self.sim_round:
            sim_num += 1
            result = 0
            selected_node = self.treePolicy(root)  # tree policy, select one node to simulate
            # cProfile.runctx('result = self.simulate(selected_node.state)', globals(), locals())

            #########without multicore########
            for non_sense in range(self.num_per_process):  # simulate num_per_process times for the particular node
                result += self.simulate(selected_node.state)  # total result for the simulation
            # print result
            self.BP(base_node=selected_node, gain=result)  # back propagation
            #########without multicore########

            ##########multi core with pool###########
            # pool = multiprocessing.Pool(processes=self.cpu_num)
            # th_result = []
            # # manager = Manager()
            # # th_list = manager.list()
            # for non_sense in range(self.cpu_num):
            #     th_result.append(pool.apply_async(wrap, args=(self, selected_node.state, self.num_per_process)))
            #     # pool.apply_async(wrap, args=(self, root, th_list, ))
            # pool.close()
            # pool.join()
            #
            # for res in th_result:
            #     # print res.get()
            #     result = result + res.get()
            #
            # print result
            # # for index in range(self.cpu_num):
            # #     self.BP(base_node=th_list[index][0], gain=th_list[index][1])
            # self.BP(base_node=selected_node, gain=result)
            ##########multi core with pool###########

        print sim_num, "simulations performed."
        # print selected_node.moveToSelf, "selected"
        self.display_wins_and_plays(root)  # useless for now

        selected_action = self.bestAction(root)  # select the best action for the root node
        # print selected_action, "selected."
        end_time = time.time()
        time_dur = end_time - start_time
        # print "time used: ", time_dur,"s"
        return selected_action

    def bestAction(self, node):  # just implement it according to the discription in the slides
        legal_moves = node.legal_moves
        most_plays = -float('inf')
        best_wins = -float('inf')
        best_actions = []
        for child in node.children:
            wins, plays = child.getWinsAndPlays()
            if plays > most_plays:
                most_plays = plays
                best_actions = [child.moveToSelf]
                best_wins = wins
            elif plays == most_plays:
                # break ties with wins
                if wins > best_wins:
                    best_wins = wins
                    best_actions = [child.moveToSelf]
                elif wins == best_wins:
                    best_actions.append(child.moveToSelf)

        return random.choice(best_actions)

    def treePolicy(self, root):
        legal_moves = root.legal_moves

        if len(legal_moves) == 0:  # no way to go
            return root
        elif legal_moves == [None]:  # pass turn
            next_state = (root.state[0], -1 * root.state[1])
            # pass_node = self.tree.addNode(state=next_state, moveToSelf=root.moveToSelf, parent=root)
            pass_node = self.tree.addNode(state=next_state, moveToSelf=root,
                                          parent=root)  # TODO:check if moveToSelf = None is right
            return pass_node

        elif len(root.children) < len(legal_moves):  # TODO:check if explore with some probablity will be better
            untried = [
                move for move in legal_moves
                if move not in root.triedMoves
            ]
            assert len(untried) > 0
            move = random.choice(untried)  # exploration
            # temp_board = copy.deepcopy(root.state[0])
            # temp_board.execute_move(move=move, color=(root.state[1]))
            temp_board = MCTS_engine.apply_move(copy.deepcopy(root.state), move)
            next_state = (temp_board, -1 * root.state[1])
            # next_state[0].execute_move(move=move, color=next_state[1])
            root.triedMoves.add(move)
            return self.tree.addNode(state=next_state, moveToSelf=move, parent=root)
        else:
            # print "11111111111111111"
            # return self.treePolicy(self.bestChild(root))
            root = self.bestChild(root)
            while len(root.legal_moves) != 0 and root.legal_moves != [None] and len(root.children) >= len(
                    root.legal_moves):
                root = self.bestChild(root)
            return self.treePolicy(root)

    def BP(self, base_node, gain):  # backpropagation the number of play-out and number of wins to the root
        while base_node is not None:
            # base_node.plays += 1
            base_node.plays += self.cpu_num * self.num_per_process
            base_node.wins += gain
            base_node = base_node.parent

    def bestChild(self, node):  # just implement it according to the description in the slides
        enemy_turn = (node.state[1] != self.color)
        C = 1  # 'exploration' value
        values = {}
        _, parent_plays = node.getWinsAndPlays()
        for child in node.children:
            wins, plays = child.getWinsAndPlays()
            if enemy_turn:
                # the enemy will play against us, not for us
                wins = plays - wins
            assert parent_plays > 0
            values[child] = (wins / plays) + C * \
                                             math.sqrt(2 * math.log(parent_plays) / plays)

        best_choice = max(values, key=values.get)
        return best_choice

    def simulate(self, state):
        WIN_PRIZE = 1
        LOSS_PRIZE = 0
        state = copy.deepcopy(state)
        while True:
            # cProfile.runctx('self.test(state)', globals(), locals())
            # winner = MCTS_engine.winner(state[0])
            winner = MCTS_engine.quick_winner(state)
            if winner[0] is not None:    # if game is over
                # print "color: ", self.color
                if winner[0] == 0:  # ties is not what we want
                    return LOSS_PRIZE
                elif winner[0] == self.color:
                    return WIN_PRIZE
                else:
                    return LOSS_PRIZE
            else:
                # moves = MCTS_engine.my_get_legal_move(state)
                moves = winner[1]
                if len(moves) == 0:  # pass turn
                    state = (state[0], -1 * state[1])
                    # moves = MCTS_engine.my_get_legal_move(state)
                    moves = winner[2]

                # temp_12 = []
                temp_corner = []
                # temp_other = []
                for move in moves:  # the four corners is the best choice
                    if move in [(0, 0), (7, 0), (0, 7), (7, 7)]:
                        temp_corner.append(move)
                # break
                #     elif (move[0] >=2 and move[0] <= 5) and (move[1] >=2 and move[1] <= 5):
                #         if self.count <= 12:
                #             temp_12.append(move)
                #             break
                #         else:
                #             temp_other.append(move)
                #     else:
                #         if move not in [(1, 6), (6, 1), (1, 1), (6, 6)]:
                #             temp_other.append(move)
                if len(temp_corner) != 0:
                    selected_move = random.choice(temp_corner)
                else:
                    selected_move = random.choice(moves)  # TODO: improve
                # elif len(temp_12) != 0:
                #     selected_move = random.choice(temp_12)
                # elif len(temp_other) != 0:
                #     selected_move = random.choice(temp_other)
                # else:
                #     selected_move = random.choice(moves)


                # state[0].execute_move(selected_move, state[1])
                my_board = MCTS_engine.apply_move(state, selected_move)
                state = (my_board, -1 * state[1])

    @staticmethod
    def apply_move(game_state, move):  # apply the action we choose
        # if move is None, then the player simply passed their turn
        if move is None:
            pass_state = (game_state[0], -1 * game_state[1])
            return pass_state

        x, y = move
        color = game_state[1]
        board = game_state[0]
        board[x][y] = color

        # now flip all the stones in every direction
        enemy_color = -1 * game_state[1]

        # now check in all directions, including diagonal
        to_flip = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dy == 0 and dx == 0:
                    continue

                # there needs to be >= 1 opponent piece
                # in this given direction, followed by 1 of player's piece
                distance = 1
                yp = (distance * dy) + y
                xp = (distance * dx) + x

                flip_candidates = []
                while ((0 <= xp and xp < 8) and (0 <= yp and yp < 8)) and board[xp][yp] == enemy_color:
                    flip_candidates.append((xp, yp))
                    distance += 1
                    yp = (distance * dy) + y
                    xp = (distance * dx) + x

                if distance > 1 and ((0 <= xp and xp < 8) and (0 <= yp and yp < 8)) and board[xp][
                    yp] == color:
                    to_flip.extend(flip_candidates)

        for each in to_flip:
            board[each[0]][each[1]] *= -1

        # game_state = (board, opponent[color])
        return board

    @staticmethod
    def my_count(state):
        board = state[0]
        array = board._MyBoard__pieces
        num = 0
        for i in range(8):
            num += array[i].count(state[1])
        return num

    @staticmethod
    def quick_winner(state):  # decide who is the winner
        board, color = state
        # black_count = board.count(-1)
        # white_count = board.count(1)
        black_count = MCTS_engine.my_count((state[0], -1))
        white_count = MCTS_engine.my_count((state[0], 1))
        my_moves = MCTS_engine.my_get_legal_move(state)
        enemy_moves = MCTS_engine.my_get_legal_move((state[0], -1 * state[1]))
        if len(my_moves) != 0 or len(enemy_moves) != 0:
            # if len(board.get_legal_moves(-1)) != 0 or len(board.get_legal_moves(1)) != 0:
            return [None, my_moves, enemy_moves]
        else:
            if black_count > white_count:
                # if black_count + white_count != 64:
                #    black_count += (64 - black_count - white_count)
                return (-1, black_count, white_count)
            elif white_count > black_count:
                # if black_count + white_count != 64:
                #    white_count += (64 - black_count - white_count)
                return (1, black_count, white_count)
            else:
                return (0, black_count, white_count)

    @staticmethod
    def winner(board):  # TODO: optimize this func
        """ Determine the winner of a given board. Return the points of the two
        players. """
        black_count = board.count(-1)
        white_count = board.count(1)
        if len(board.get_legal_moves(-1)) != 0 or len(board.get_legal_moves(1)) != 0:
            return None
        else:
            if black_count > white_count:
                # if black_count + white_count != 64:
                #    black_count += (64 - black_count - white_count)
                return (-1, black_count, white_count)
            elif white_count > black_count:
                # if black_count + white_count != 64:
                #    white_count += (64 - black_count - white_count)
                return (1, black_count, white_count)
            else:
                return (0, black_count, white_count)

    def display_wins_and_plays(self, node):    # useless for now
        # legal_moves = node.state[0].get_legal_moves(node.state[1])
        child = node.children
        win_sum = 0
        play_sum = 0
        for i in child:
            wins, plays = i.getWinsAndPlays()
            win_sum += wins
            play_sum += plays
            # print i.moveToSelf, ":", wins, "/", plays
            # print "win / plays:",win_sum,"/",play_sum

    def test(self, state):  # useless for now
        for i in xrange(20):
            winner = MCTS_engine.quick_winner(state)

    def test1(self, board, move, color):  # useless for now
        for i in xrange(200):
            # winner = board.execute_move(move, color)
            winner = MCTS_engine.apply_move((board, color), move)

    @staticmethod
    def my_get_legal_move(state):   # get valid moves
        moves = []  # list of x,y positions valid for color

        for y in xrange(8):
            for x in xrange(8):
                if MCTS_engine.my_is_valid_move(state, x, y):
                    moves.append((x, y))
        return moves

    @staticmethod
    def my_is_valid_move(state, x, y):  # check if x,y is a valid move
        board, color = state
        piece = board[x][y]  # TODO:x y or y x
        if piece != 0:
            return False

        enemy = -1 * color

        # now check in all directions, including diagonal
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dy == 0 and dx == 0:
                    continue

                # there needs to be >= 1 opponent piece
                # in this given direction, followed by 1 of player's piece
                distance = 1
                yp = (distance * dy) + y
                xp = (distance * dx) + x

                while ((0 <= xp and xp < 8) and (0 <= yp and yp < 8)) and board[xp][yp] == enemy:
                    distance += 1
                    yp = (distance * dy) + y
                    xp = (distance * dx) + x

                if distance > 1 and ((0 <= xp and xp < 8) and (0 <= yp and yp < 8)) and board[xp][
                    yp] == color:
                    return True
        return False


class tree:  # a tree for storing all states and relationships
    def __init__(self):
        self.stateNode = {}
        self.hit = 0

    def getNode(self, state):
        if state in self.stateNode:
            self.hit += 1
            # print "hit"
            return self.stateNode[state]
        else:
            return self.addNode(state=state, moveToSelf=None)

    def addNode(self, state, moveToSelf, parent=None):
        # legal_moves = state[0].get_legal_moves(color=state[1])
        legal_moves = MCTS_engine.my_get_legal_move(state)
        # assert legal_moves > 1

        # isGameOver = MCTS_engine.winner(state[0]) is not None
        isGameOver = (MCTS_engine.quick_winner(state))[0] is not None
        if (not isGameOver) and (len(legal_moves) == 0):  # pass turn
            legal_moves = [None]
        child = node(state=state, moveToSelf=moveToSelf, legal_moves=legal_moves)
        child.parent = parent
        if parent is not None:
            parent.addChild(child)
        self.stateNode[state] = child
        return child


class node:  # node for the tree
    def __init__(self, state, moveToSelf, legal_moves):
        self.state = state
        self.moveToSelf = moveToSelf
        self.legal_moves = legal_moves
        self.plays = 0
        self.wins = 0
        self.children = []
        self.parent = None
        self.triedMoves = set()

    def addChild(self, child):
        self.children.append(child)
        child.parent = self

    def getWinsAndPlays(self):
        return self.wins, self.plays


#################### you can skip reading all the following codes ###################
class MyBoard():
    # List of all 8 directions on the board, as (x,y) offsets
    __directions = [(1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)]

    def __init__(self):
        """ Set up initial board configuration. """
        # Create the empty board array
        self.__pieces = [None] * 8
        # self.size = 8
        for i in range(8):
            self.__pieces[i] = [0] * 8

        # Set up the initial 4 pieces
        self.__pieces[3][4] = 1
        self.__pieces[4][3] = 1
        self.__pieces[3][3] = -1;
        self.__pieces[4][4] = -1;

    # Add [][] indexer syntax to the Board
    def __getitem__(self, index):
        return self.__pieces[index]

    def display(self, time):
        """" Display the board and the statistics of the ongoing game. """
        print "    A B C D E F G H"
        print "    ---------------"
        for y in range(7, -1, -1):
            # Print the row number
            print str(y + 1) + ' |',
            for x in range(8):
                # Get the piece to print
                piece = self[x][y]
                if piece == -1:
                    print "B",
                elif piece == 1:
                    print "W",
                else:
                    print ".",
            print '| ' + str(y + 1)

        print "    ---------------"
        print "    A B C D E F G H\n"

        print "STATISTICS (score / remaining time):"
        print "Black: " + str(self.count(-1)) + ' / ' + str(time[-1])
        print "White: " + str(self.count(1)) + ' / ' + str(time[1]) + '\n'

    def count(self, color):
        """ Count the number of pieces of the given color.
        (1 for white, -1 for black, 0 for empty spaces) """
        count = 0
        for y in range(8):
            for x in range(8):
                if self[x][y] == color:
                    count += 1
        return count

    def get_squares(self, color):
        """ Get the coordinates (x,y) for all pieces on the board of the given color.
        (1 for white, -1 for black, 0 for empty spaces) """
        squares = []
        for y in range(8):
            for x in range(8):
                if self[x][y] == color:
                    squares.append((x, y))
        return squares

    def get_legal_moves(self, color):
        """ Return all the legal moves for the given color.
        (1 for white, -1 for black) """
        # Store the legal moves
        moves = set()
        # Get all the squares with pieces of the given color.
        for square in self.get_squares(color):
            # Find all moves using these pieces as base squares.
            newmoves = self.get_moves_for_square(square)
            # Store these in the moves set.
            moves.update(newmoves)
        return list(moves)

    def get_moves_for_square(self, square):
        """ Return all the legal moves that use the given square as a base
        square. That is, if the given square is (3,4) and it contains a black
        piece, and (3,5) and (3,6) contain white pieces, and (3,7) is empty,
        one of the returned moves is (3,7) because everything from there to
        (3,4) can be flipped. """
        (x, y) = square
        # Determine the color of the piece
        color = self[x][y]

        # Skip empty source squares
        if color == 0:
            return None

        # Search all possible directions
        moves = []
        for direction in self.__directions:
            move = self._discover_move(square, direction)
            if move:
                moves.append(move)
        # Return the generated list of moves
        return moves

    def execute_move(self, move, color):
        """ Perform the given move on the board, and flips pieces as necessary.
        color gives the color of the piece to play (1 for white, -1 for black) """
        # Start at the new piece's square and follow it on all 8 directions
        # to look for pieces allowing flipping

        # Add the piece to the empty square
        flips = (flip for direction in self.__directions for flip in self._get_flips(move, direction, color))

        # print '11111111111111'
        for x, y in flips:
            # print x,y
            self[x][y] = color

    def _discover_move(self, origin, direction):
        """ Return the endpoint of a legal move, starting at the given origin,
        and moving in the given direction. """
        x, y = origin
        color = self[x][y]
        flips = []

        for x, y in Board._increment_move(origin, direction):
            if self[x][y] == 0 and flips:
                return (x, y)
            elif (self[x][y] == color or (self[x][y] == 0 and not flips)):
                return None
            elif self[x][y] == -color:
                flips.append((x, y))

    def _get_flips(self, origin, direction, color):
        """ Get the list of flips for a vertex and a direction to use within
        the execute_move function. """
        # Initialize variable
        flips = [origin]

        for x, y in Board._increment_move(origin, direction):
            if self[x][y] == -color:
                flips.append((x, y))
            elif (self[x][y] == 0 or (self[x][y] == color and len(flips) == 1)):
                break
            elif self[x][y] == color and len(flips) > 1:
                return flips
        return []

    @staticmethod
    def _increment_move(move, direction):
        """ Generator expression for incrementing moves """
        move = map(sum, zip(move, direction))
        while all(map(lambda x: 0 <= x < 8, move)):
            yield move
            move = map(sum, zip(move, direction))

    def __hash__(self):  # TODO: should add __hash__ and __eq__ func
        # return hash(str(self.board))
        hash = 5138

        for y in range(8):
            for x in range(8):
                hash += self.__pieces[y][x]
                hash += (hash << 10)
                hash ^= (hash >> 6)

        hash += (hash << 3)
        hash ^= (hash >> 11)
        hash += (hash << 15)
        return hash

    def __eq__(self, other):
        myBlackNum = self.count(-1)
        myWhiteNum = self.count(1)
        yourBlackNum = other.count(-1)
        yourWhiteNum = other.count(1)
        if myBlackNum != yourBlackNum:
            return False
        if myWhiteNum != yourWhiteNum:
            return False
            # if self.__hash__() != other.__hash__():
            # return False
        # return np.array_equal(self.board, other.board)
        return self.__pieces == other.__pieces


engine = MCTS_engine


def wrap(worker, selected_node, num):
    # print selected_node
    result = 0
    for i in range(num):
        result += worker.simulate(selected_node)
    # print result

    return result
