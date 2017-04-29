from __future__ import absolute_import
from copy import deepcopy
from engines import Engine
import random
import timeit


class AntonioEngine(Engine):
    def get_move(self, board, color, move_num=None,
                 time_remaining=None, time_opponent=None):
        start_time = end_time = timeit.default_timer()
        v0 = Node(board, color, None, None)  # create root node
        while end_time - start_time < 57:
            vl = v0.tree_policy()  # choose the most valuable node
            delta = vl.default_policy()  # simulate the whole game
            vl.back_up_negative_max(delta)  # store reward backwards
            end_time = timeit.default_timer()
        mv = v0.best_child(0)  # choose the child with max average reward
        return mv.get_action()


class Node:
    def __init__(self, board=None, color=None,
                 parent=None, action=None):
        self.__board = board  # store the board
        self.__color = color  # who is to execute next move
        self.__parent = parent  # parent node
        self.__action = action  # how parent goes here
        self.__n = 0  # test times
        self.__q = 0  # sum of reward
        self.__consecutive = False  # __color is the same as the parent
        self.__legal_moves = board.get_legal_moves(color)
        self.__legal_moves_count = self.__legal_moves.__len__()
        if self.__legal_moves_count == 0:  # cannot alternate because no possible move
            self.__color = -color
            self.__consecutive = True
            self.__legal_moves = board.get_legal_moves(-color)
            self.__legal_moves_count = self.__legal_moves.__len__()
        self.__expanded = []  # store the nodes already expanded
        self.__expanded_count = self.__expanded.__len__()  # how many nodes are expanded

    def is_fully_expanded(self):
        return self.__legal_moves_count == self.__expanded_count

    def expand(self):
        ec = self.__expanded_count
        assert self.__legal_moves_count > ec  # assure that there indeed has an unexpanded node
        new_board = deepcopy(self.__board)
        new_move = self.__legal_moves[ec]
        new_board.execute_move(new_move, self.__color)
        v_prime = Node(new_board, -self.__color, self,
                       self.__legal_moves[ec])  # create this new child node
        self.__expanded.append(v_prime)  # add this node to the parent's __expanded
        self.__expanded_count += 1
        return v_prime

    def back_up_negative_max(self, delta):
        v = self
        while v is not None:
            v.__n += 1
            v.__q += delta
            if not v.__consecutive:  # when we change our view to our opponent, reward should be negated
                delta = -delta
            v = v.__parent

    def best_child(self, c):
        assert (self.__expanded.__len__() > 0)
        max_score = -64  # any score calculated will be larger than this
        max_action = None
        for move in self.__expanded:
            (x, y) = move.test_best(c, self.__color)
            this_score = x + y
            if this_score > max_score:  # update
                max_score = this_score
                max_action = move
        return max_action

    def test_best(self, c, stand):
        exploit_score = stand * self.__color * self.__q * 1.0 / self.__n
        explore_score = c * self.__parent.__n * 1.0 / self.__n / self.__n
        return exploit_score, explore_score

    def tree_policy(self):
        v = self
        c = 8
        while v.__legal_moves_count > 0:
            if not v.is_fully_expanded():
                return v.expand()
            else:
                v = v.best_child(c)
        return v

    def default_policy(self):
        new_board = deepcopy(self.__board)
        color = self.__color
        while new_board.get_legal_moves(color) + new_board.get_legal_moves(-color) > 0:  # not finished
            if new_board.get_legal_moves(color).__len__() > 0:  # alternate
                new_board.execute_move(
                    random.choice(new_board.get_legal_moves(color)),
                    color)
                color = -color
            elif new_board.get_legal_moves(-color).__len__() > 0:  # consecutive
                new_board.execute_move(
                    random.choice(new_board.get_legal_moves(-color)),
                    -color)
            else:
                break
        return reward(new_board, self.__color)

    def get_action(self):
        return self.__action

    def get_expanded(self):
        return self.__expanded

    def get_q(self):
        return self.__q

    def get_n(self):
        return self.__n


def reward(board, color):
    return len(board.get_squares(color)) - len(board.get_squares(-color))


engine = AntonioEngine
