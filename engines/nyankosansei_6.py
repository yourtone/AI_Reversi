from __future__ import absolute_import

from copy import deepcopy
import math
import random

from engines import Engine
from multiprocessing import Process, Pool, TimeoutError, Queue

DEPTH = 5000

class MCTSEngine(Engine):
    def __init__(self):
        fill_bit_table()
        self.ACC = dict() 
        self.WIN = dict()  
        self.FULLT_EXTENED = [] 
        self.C = 1.96

    def get_move(self, board, color, move_num=None,
                 time_remaining=None, time_opponent=None):

        res = self.mcts(board, color, DEPTH)
        return res[1]

    def mcts(self, board, color, depth):
        W, B = to_bitboard(board)
        if not self.ACC.has_key((W, B)):
            self.ACC[(W, B)] = 0
            self.WIN[(W, B)] = 0

        movelist = board.get_legal_moves(color)
        best = - float("inf")
        bestmv = None if len(movelist) == 0 else movelist[0]

        for iter in range(20):
            self.simulation(board, color, depth)

        # print(movelist)
        for mv in movelist:
            new_board = deepcopy(board)
            new_board.execute_move(mv, color)
            new_W, new_B = to_bitboard(new_board)

            if (new_W, new_B) in self.ACC:
                v = self.WIN[(W, B)]
                N = self.ACC[(W, B)]
                Ni = self.ACC[(new_W, new_B)]

                uct = v + self.C * math.sqrt(math.log(N)/(Ni))

                if 0 in mv and 7 in mv:
                    uct = uct + 5
                elif 0 in mv or 7 in mv:
                    uct = uct + 3

                if uct > best:
                    best = uct
                    bestmv = mv

        return best, bestmv

    def simulation(self, board, color, depth):
        W, B = to_bitboard(board)
        if not self.ACC.has_key((W, B)):  
            self.ACC[(W, B)] = 0
            self.WIN[(W, B)] = 0

        self.ACC[(W, B)] += 1

        if depth == 0 or (W, B) in self.FULLT_EXTENED: 
            return True, False

        movelist = board.get_legal_moves(color)
        if len(movelist) == 0: 
            self.FULLT_EXTENED.append((W, B))
            if self.eval(board, color) == 1:
                if self.WIN[(W, B)] == 0:
                    self.WIN[(W, B)] = 1
                    return True, True
            return True, False

        unchecked_move = []
        for mv in movelist:
            new_board = deepcopy(board)
            new_board.execute_move(mv, color)
            new_W, new_B = to_bitboard(board)
            if (new_W, new_B) not in self.FULLT_EXTENED:
                unchecked_move.append(mv)

        if len(unchecked_move) > 0:  
            mv = random.choice(unchecked_move)
            new_board = deepcopy(board)
            new_board.execute_move(mv, color)
            ifFullyExtended, statusChange = self.simulation(new_board, color * -1, depth - 1)

            if statusChange:
                self.WIN[(W,B)] += 1

            if ifFullyExtended:
                unchecked_move.remove(mv)
                if len(unchecked_move) == 0:
                    self.FULLT_EXTENED.append((W, B))
                return ifFullyExtended, statusChange

        return False, statusChange

    def eval(self, board, color):
        num_pieces_op = len(board.get_squares(color*-1))
        num_pieces_me = len(board.get_squares(color))
        return 1 if (num_pieces_me > num_pieces_op) else 0


def fill_bit_table():
    global BIT
    BIT = [1 << n for n in range(64)]


def to_bitboard(board):
    W = 0
    B = 0
    for r in range(8):
        for c in range(8):
            if board[c][r] == -1:
                B |= BIT[8 * r + c]
            elif board[c][r] == 1:
                W |= BIT[8 * r + c]
    return W, B


def to_move(bitmove):
    return (bitmove % 8, bitmove / 8)

engine = MCTSEngine
