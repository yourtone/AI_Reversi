from __future__ import absolute_import
from engines import Engine
import time
import random
import copy
import math


class MCTSengine(Engine):
    def __init__(self):
        self.initialized = False

    def get_move(self, board, color, move_num=None,
                 time_remaining=None, time_opponent=None):

        if not self.initialized:
            self.color = color
            self.sim_time = 1
            self.tree_manager = TreeManager(board)
            self.initialized = True

        legal_moves = board.get_legal_moves(color)
        if not legal_moves:
            return None

        game_state = (board, color)
        move = self.UCTsearch(game_state)
        return move

    def UCTsearch(self, game_state):
        root = self.tree_manager.get_node(game_state)
        root.parent = None

        sim_count = 0
        now = time.time()
        while time.time() - now < self.sim_time:
            picked_node = self.tree_policy(root)
            result = self.simulate(picked_node.game_state)
            self.back_prop(picked_node, result)
            sim_count += 1

        return self.best_child(root, 0).move


    def tree_policy(self, root):
        legal_moves = root.legal_moves
        if len(legal_moves) == 0:
            return root

        elif legal_moves == [None]:
            next_state = (root.game_state[0], -root.game_state[1])
            pass_node = self.tree_manager.add_node(next_state, None, root)
            return pass_node

        elif len(root.children) < len(legal_moves):
            untried = [
                move for move in legal_moves
                if move not in root.moves_tried
            ]

            # assert len(untried) > 0

            move = random.choice(untried)

            next_state = copy.deepcopy(root.game_state)
            next_state[0].execute_move(move, next_state[1])

            root.moves_tried.add(move)
            return self.tree_manager.add_node(next_state, move, root)

        else:
            return self.tree_policy(self.best_child(root, 1))


    def best_child(self, node, C):
        enemy_turn = (node.game_state[1] != self.color)

        # C = 1  # 'exploration' value
        values = {}
        _, parent_plays = node.get_wins_plays()
        for child in node.children:
            wins, plays = child.get_wins_plays()
            if enemy_turn:
                wins = plays - wins
            assert parent_plays > 0
            values[child] = (wins / plays) + C * math.sqrt(math.log(parent_plays) / plays)

        best_choice = max(values, key=values.get)
        return best_choice


    def simulate(self, game_state):
        WIN_PRIZE = 1
        LOSS_PRIZE = 0
        state = copy.deepcopy(game_state)
        while True:
            winner = get_winner(state[0]) 
            if winner is not False:
                if winner == self.color:
                    return WIN_PRIZE
                else:
                    return LOSS_PRIZE
            moves = state[0].get_legal_moves(state[1])
            if not moves:
                state = (state[0], -state[1])
                moves = state[0].get_legal_moves(state[1])

            #? Shall we randomly pick one ?
            picked = random.choice(moves)
            state[0].execute_move(picked, state[1])
            

    @staticmethod
    def back_prop(node, delta):
        while node is not None:
            node.plays += 1
            node.wins += delta
            node = node.parent
#-----------------------------------------------------------------
class TreeManager:

    def __init__(self, board):
        self.state_node = {}

    def add_node(self, game_state, move, parent=None):
        board, color = game_state

        legal_moves = board.get_legal_moves(color)
        is_game_over = get_winner(board) is not False

        if len(legal_moves) == 0 and not is_game_over:
            legal_moves = [None]

        n = Node(game_state, move, legal_moves)
        n.parent = parent

        if parent is not None:
            parent.add_child(n)

        self.state_node[game_state] = n
        return n

    def get_node(self, game_state):
        if game_state in self.state_node:
            return self.state_node[game_state]
        else:
            return self.add_node(game_state, None)

#-----------------------------------------------------------------
class Node:

    def __init__(self, game_state, move, legal_moves):
        self.game_state = game_state

        self.plays = 0
        self.wins = 0

        self.children = []  # child Nodes
        self.parent = None

        self.move = move  # action from its parent to it

        self.legal_moves = legal_moves # [None] for pause
        self.moves_tried = set()

    def add_child(self, child_node):
        self.children.append(child_node)
        child_node.parent = self

    def has_children(self):
        return len(self.children) > 0

    def get_wins_plays(self):
        return self.wins, self.plays
"""
    def __hash__(self):
        return hash(self.game_state)

    def __repr__(self):
        return 'move: {} wins: {} plays: {}'.format(self.move, self.wins, self.plays)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.game_state == other.game_state

"""

#-----------------------------------------------------------------
def get_winner(board):
    """
    return:
        -1: black wins
        1:  white wins
        0:  tie
        FALSE: not yet
    """
    black_count = board.count(-1)
    white_count = board.count(1)

    if black_count + white_count == 64:
        if black_count > white_count:
            return -1
        elif black_count < white_count:
            return 1
        else:
            return 0

    # a non-full board can still be game-over if neither player can move.
    black_legal = board.get_legal_moves(-1)
    if black_legal:
        return False

    white_legal = board.get_legal_moves(1)
    if white_legal:
        return False

    # neither black nor white has valid moves
    if black_count > white_count:
        return -1
    elif black_count < white_count:
        return 1
    else:
        return 0
#-------------------------------------
engine = MCTSengine
