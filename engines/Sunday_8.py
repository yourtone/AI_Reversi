from __future__ import absolute_import
from engines import Engine
from copy import deepcopy
import math
import random
import timeit


class AlphaBeta_Engine(Engine):
    def __init__(self):
        self.target_color = None
        self.eval_engine = Eval()
        self.depth = 5

    def get_move(self, board, color, move_num=None,
                 time_remaining=None, time_opponent=None):
        self.target_color = color
        return self.alpha_beta_search(board, color)

    def max_value(self, board, alpha, beta, depth, color):
        if depth == 0 or (not board.get_legal_moves(color) and not board.get_legal_moves(-color)):
            return self.eval(board, color)*1e7, None
        v, current_board, best_mv = -float('inf'), deepcopy(board), None
        legal_moves = current_board.get_legal_moves(color)
        if not legal_moves:
            tmp_v = self.min_value(current_board, alpha, beta, depth-1, -color)
            if tmp_v > v:
                v, best_mv = tmp_v, None
            if v >= beta:
                return v, best_mv
            if v > alpha:
                alpha = v
        else:
            for move in legal_moves:
                tmp_board = deepcopy(current_board)
                tmp_board.execute_move(move, color)
                tmp_v = self.min_value(tmp_board, alpha, beta, depth-1, -color)
                if tmp_v > v:
                    v, best_mv = tmp_v, move
                if v >= beta:
                    return v, best_mv
                if v > alpha:
                    alpha = v
        return v, best_mv

    def min_value(self,board, alpha, beta, depth, color):
        if depth == 0 or (not board.get_legal_moves(color) and not board.get_legal_moves(-color)):
            return self.eval(board, color)*1e7
        v, current_board = float('inf'), deepcopy(board)
        legal_moves = current_board.get_legal_moves(color)
        if not legal_moves:
            tmp_v, _ = self.max_value(current_board, alpha, beta, depth-1, -color)
            if tmp_v < v:
                v = tmp_v
            if v <= alpha:
                return v
            if v < beta:
                beta = v
        else:
            for move in legal_moves:
                tmp_board = deepcopy(current_board)
                tmp_board.execute_move(move, color)
                tmp_v, _ = self.max_value(tmp_board, alpha, beta, depth-1, -color)
                if tmp_v < v:
                    v = tmp_v
                if v <= alpha:
                    return v
                if v < beta:
                    beta = v
        return v

    def eval(self, board, color=1):
        # res = 0
        # for i in range(8):
        #     for j in range(8):
        #         if board[i][j] == self.target_color:
        #             res += 1
        #         elif board[i][j] == -self.target_color:
        #             res -= 1
        # corner_list = [(0,0),(0,7),(7,0),(7,7)]
        # sub_corner_list = [(0,1),(1,0),(1,1),
        #                    (0,6),(1,7),(1,6),
        #                    (6,0),(7,1),(6,1),
        #                    (6,7),(7,6),(6,6),
        #                    ]
        # for (x,y) in corner_list:
        #     if board[x][y] == self.target_color:
        #         res += 5
        #     elif board[x][y] == -self.target_color:
        #         res -= 5

        # another eval engine
        w, b = self.eval_engine.to_bitboard(board)
        if self.target_color < 0:
            (w, b) = (b, w)
        if color != self.target_color:
            (w, b) = (b, w)
        res = self.eval_engine.eval(w, b)
        if color != self.target_color:
            res = -res
        return res

    def alpha_beta_search(self, board, color):
        v, best_mv = self.max_value(board, -float('inf'), float('inf'), self.depth, color)
        return best_mv


class Eval(object):
    WEIGHTS = \
    [-3, -7, 11, -4, 8, 1, 2]
    P_RINGS = [0x4281001818008142,
               0x42000000004200,
               0x2400810000810024,
               0x24420000422400,
               0x1800008181000018,
               0x18004242001800,
               0x3C24243C0000]
    P_CORNER = 0x8100000000000081
    P_SUB_CORNER = 0x42C300000000C342
    FULL_MASK = 0xFFFFFFFFFFFFFFFF
    BIT = [1 << n for n in range(64)]

    def eval(self, W, B):
        w0 = W & self.BIT[0] != 0
        w1 = W & self.BIT[7] != 0
        w2 = W & self.BIT[56] != 0
        w3 = W & self.BIT[63] != 0
        b0 = B & self.BIT[0] != 0
        b1 = B & self.BIT[7] != 0
        b2 = B & self.BIT[56] != 0
        b3 = B & self.BIT[63] != 0

        # stability
        wunstable = bunstable = 0
        if w0 != 1 and b0 != 1:
            wunstable += (W & self.BIT[1] != 0) + (W & self.BIT[8] != 0) + (W & self.BIT[9] != 0)
            bunstable += (B & self.BIT[1] != 0) + (B & self.BIT[8] != 0) + (B & self.BIT[9] != 0)
        if w1 != 1 and b1 != 1:
            wunstable += (W & self.BIT[6] != 0) + (W & self.BIT[14] != 0) + (W & self.BIT[15] != 0)
            bunstable += (B & self.BIT[6] != 0) + (B & self.BIT[14] != 0) + (B & self.BIT[15] != 0)
        if w2 != 1 and b2 != 1:
            wunstable += (W & self.BIT[48] != 0) + (W & self.BIT[49] != 0) + (W & self.BIT[57] != 0)
            bunstable += (B & self.BIT[48] != 0) + (B & self.BIT[49] != 0) + (B & self.BIT[57] != 0)
        if w3 != 1 and b3 != 1:
            wunstable += (W & self.BIT[62] != 0) + (W & self.BIT[54] != 0) + (W & self.BIT[55] != 0)
            bunstable += (B & self.BIT[62] != 0) + (B & self.BIT[54] != 0) + (B & self.BIT[55] != 0)

        scoreunstable = - 30.0 * (wunstable - bunstable)

        # piece difference
        wpiece = (w0 + w1 + w2 + w3) * 100.0
        for i in range(len(self.WEIGHTS)):
            wpiece += self.WEIGHTS[i] * self.count_bit(W & self.P_RINGS[i])
        bpiece = (b0 + b1 + b2 + b3) * 100.0
        for i in range(len(self.WEIGHTS)):
            bpiece += self.WEIGHTS[i] * self.count_bit(B & self.P_RINGS[i])
        scorepiece = wpiece - bpiece

        # mobility
        wmob = self.count_bit(self.move_gen(W, B))
        scoremob = 20 * wmob

        return scorepiece + scoreunstable + scoremob

    def to_bitboard(self, board):
        W = 0
        B = 0
        for r in range(8):
            for c in range(8):
                if board[c][r] == -1:
                    B |= self.BIT[8 * r + c]
                elif board[c][r] == 1:
                    W |= self.BIT[8 * r + c]
        return (W, B)

    def count_bit(self, b):
        b -=  (b >> 1) & 0x5555555555555555
        b  = (((b >> 2) & 0x3333333333333333) + (b & 0x3333333333333333))
        b  = ((b >> 4) + b)  & 0x0F0F0F0F0F0F0F0F
        return ((b * 0x0101010101010101) & self.FULL_MASK) >> 56

    def move_gen_sub(self, P, mask, dir):
        dir2 = long(dir * 2)
        flip1  = mask & (P << dir)
        flip2  = mask & (P >> dir)
        flip1 |= mask & (flip1 << dir)
        flip2 |= mask & (flip2 >> dir)
        mask1  = mask & (mask << dir)
        mask2  = mask & (mask >> dir)
        flip1 |= mask1 & (flip1 << dir2)
        flip2 |= mask2 & (flip2 >> dir2)
        flip1 |= mask1 & (flip1 << dir2)
        flip2 |= mask2 & (flip2 >> dir2)
        return (flip1 << dir) | (flip2 >> dir)

    def move_gen(self, P, O):
        mask = O & 0x7E7E7E7E7E7E7E7E
        return ((self.move_gen_sub(P, mask, 1)
                | self.move_gen_sub(P, O, 8)
                | self.move_gen_sub(P, mask, 7)
                | self.move_gen_sub(P, mask, 9)) & ~(P|O)) & self.FULL_MASK


class TreeNode:
    def __init__(self):
        self.board = None
        self.color = None
        self.father = None
        self.moves_to_run = None
        self.children = None
        self.prev_moves = None
        self.terminal = None
        self.reward = None
        self.try_times = None
        self.first_expand = None


class TreeNodeFactory:
    def __init__(self):
        pass

    def gen_ordinary_node(self, board, color):
        node = TreeNode()
        node.board = board
        node.color = color
        node.father = None
        node.moves_to_run = set(node.board.get_legal_moves(node.color))
        node.first_expand = True
        node.children = []
        node.prev_moves = []
        node.terminal = False
        if len(node.moves_to_run) == 0:
            moves = node.board.get_legal_moves(-node.color)
            if len(moves) == 0:
                node.terminal = True
            else:
                node.color = -node.color
                node.prev_moves.append(None)
                node.moves_to_run = moves
        node.reward = 0.0
        node.try_times = 0
        return node

    def gen_child_node(self, father, move):
        new_board = deepcopy(father.board)
        new_board.execute_move(move, father.color)
        child = self.gen_ordinary_node(new_board, -father.color)
        child.father = father
        child.prev_moves[:0] = [move]
        return child


class Sunday_8Engine(Engine):
    def __init__(self):
        self.node_factory = TreeNodeFactory()
        self.another_5 = AlphaBeta_Engine()
        self.another_3 = AlphaBeta_Engine()
        self.another_3.depth = 3

    def get_move(self, board, color, move_num=None,
                 time_remaining=None, time_opponent=None):
        if move_num < 8:
            return self.another_5.get_move(deepcopy(board), color, move_num, time_remaining, time_opponent)
        self.root = self.node_factory.gen_ordinary_node(board, color)
        start = timeit.default_timer()
        # cnt = 0
        while timeit.default_timer() - start < 59:
            # cnt += 1
            node = self.__tree_policy(self.root)
            # for i in range(1):
            winner, win_reward = self.__default_policy((node.board), node.color)
            self.__back_up(node, winner, 1, -1, 0)
        # print "try times: " + str(cnt)
        if len(self.root.prev_moves) > 0:
            return self.root.prev_moves[0]
        else:
            return self.__best_child(self.root, 1.0).prev_moves[0]

    def __expand(self, node):
        next_move = node.moves_to_run.pop()
        node.children.append(self.node_factory.gen_child_node(node, next_move))
        return node.children[-1]


    def __update(self, node, winner, win_reward, lose_reward, tie_reward):
        node.try_times += 1
        if node.father is None:
            pass
        elif node.father.color == winner:
            node.reward += win_reward
        elif -node.father.color == winner:
            node.reward += lose_reward
        else:
            node.reward += tie_reward
        return


    def __evaluate(self, father, child, mix):
        exploration = 1.0 * child.reward / child.try_times
        exploitation = 1.0 * math.sqrt(2.0 * math.log(father.try_times) / child.try_times)
        value = exploration + mix * exploitation
        return value


    def __best_child(self, node, mix):
        index = 0
        max_value = self.__evaluate(node, node.children[0], mix)
        for i in range(1, len(node.children)):
            tmp_value = self.__evaluate(node, node.children[i], mix)
            if tmp_value > max_value:
                max_value = tmp_value
                index = i
        return node.children[index]


    def __tree_policy(self, node):
        while not node.terminal:
            if len(node.moves_to_run) != 0:
                return self.__expand(node)
            else:
                node = self.__best_child(node, 1.0)
        return node


    def __default_policy(self, board, color):
        no_move = 0
        while no_move < 2:
            legal_moves = board.get_legal_moves(color)
            if len(legal_moves) > 0:
                next_move = self.another_3.get_move(board, color)
                board.execute_move(next_move, color)
                no_move = 0
            else:
                no_move += 1
            color = -color
        result = board.count(1) - board.count(-1)
        if result > 0:
            return 1, result
        elif result < 0:
            return -1, -result
        else:
            return 0, 0


    def __back_up(self, node, winner, win_reward, lose_reward, tie_reward):
        while node is not None:
            self.__update(node, winner, win_reward, lose_reward, tie_reward)
            node = node.father


engine = Sunday_8Engine
