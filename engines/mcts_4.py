from engines import Engine
from cmath import sqrt, log
import timeit, sys

# sys.path.reverse()
import random

FULL_MASK = 0xFFFFFFFFFFFFFFFF
LSB_HASH = 0x07EDD5E59A4E28C2
BIT = [1 << n for n in range(64)]
LSB_TABLE = [0] * 64

bitmap = 1
for i in range(64):
    LSB_TABLE[(((bitmap & (~bitmap + 1)) * LSB_HASH) & FULL_MASK) >> 58] = i
    bitmap <<= 1


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


def move_gen_sub(P, mask, dir):
    dir2 = long(dir * 2)
    flip1 = mask & (P << dir)
    flip2 = mask & (P >> dir)
    flip1 |= mask & (flip1 << dir)
    flip2 |= mask & (flip2 >> dir)
    mask1 = mask & (mask << dir)
    mask2 = mask & (mask >> dir)
    flip1 |= mask1 & (flip1 << dir2)
    flip2 |= mask2 & (flip2 >> dir2)
    flip1 |= mask1 & (flip1 << dir2)
    flip2 |= mask2 & (flip2 >> dir2)
    return (flip1 << dir) | (flip2 >> dir)


def move_gen(P, O):
    mask = O & 0x7E7E7E7E7E7E7E7E
    return ((move_gen_sub(P, mask, 1) | move_gen_sub(P, O, 8) | move_gen_sub(P, mask, 7) | move_gen_sub(P, mask, 9)) & ~(P | O)) & FULL_MASK


def lsb(bitmap):
    return LSB_TABLE[(((bitmap & (~bitmap + 1)) * LSB_HASH) & FULL_MASK) >> 58]


def pop_lsb(bitmap):
    l = lsb(bitmap)
    bitmap &= bitmap - 1
    return l, bitmap & FULL_MASK


RADIAL_MAP = {}


def fill_radial_map():
    rad_map = {-1: (-1, 0), 1: (1, 0), -8: (0, -1), 8: (0, 1), -7: (1, -1), 7: (-1, 1), -9: (-1, -1), 9: (1, 1)}
    for dir, dirtup in rad_map.items():
        lis = [0] * 64
        for sqr in range(64):
            mask = 0
            sq = sqr
            x, y = to_move(sq)
            sq += dir
            x += dirtup[0]
            y += dirtup[1]
            while 0 <= x < 8 and 0 <= y < 8 and 0 <= sq < 64:
                mask |= BIT[sq]
                sq += dir
                x += dirtup[0]
                y += dirtup[1]
            lis[sqr] = mask
        RADIAL_MAP[dir] = lis


DIR = [
    [1, -7, -8],
    [-1, -9, -8],
    [1, 8, 9],
    [7, 8, -1],
    [8, 9, 1, -7, -8],
    [-1, 1, -7, -8, -9],
    [7, 8, -1, -9, -8],
    [7, 8, 9, -1, 1],
    [-1, 1, -7, 7, -8, 8, -9, 9]]
SQ_DIR = \
    [2, 2, 7, 7, 7, 7, 3, 3,
     2, 2, 7, 7, 7, 7, 3, 3,
     4, 4, 8, 8, 8, 8, 6, 6,
     4, 4, 8, 8, 8, 8, 6, 6,
     4, 4, 8, 8, 8, 8, 6, 6,
     4, 4, 8, 8, 8, 8, 6, 6,
     0, 0, 5, 5, 5, 5, 1, 1,
     0, 0, 5, 5, 5, 5, 1, 1]


def flip(W, B, mv):
    mask = 0
    for dir in DIR[SQ_DIR[mv]]:
        mvtmp = mv
        mvtmp += dir
        while 0 <= mvtmp < 64 and (BIT[mvtmp] & B != 0) and (BIT[mvtmp] & RADIAL_MAP[dir][mv] != 0):
            mvtmp += dir
        if (0 <= mvtmp < 64 and BIT[mvtmp] & W != 0) and (BIT[mvtmp] & RADIAL_MAP[dir][mv] != 0):
            mvtmp -= dir
            while mvtmp != mv:
                mask |= BIT[mvtmp]
                mvtmp -= dir

    return mask

# ugly implementation
treeNode = []
# C = 0.8
C = 1.125
# C = 1.1

# def countBit(num):
#     return sum([1 if num & bit != 0 else 0 for bit in BIT])


def count_bit(b):
    b -= (b >> 1) & 0x5555555555555555
    b = (((b >> 2) & 0x3333333333333333) + (b & 0x3333333333333333))
    b = ((b >> 4) + b) & 0x0F0F0F0F0F0F0F0F
    return ((b * 0x0101010101010101) & FULL_MASK) >> 56


# Node better be inner class of MctsEngin
class Node:
    def __init__(self, move=0, W=0, B=0, parent=None):
        # score = x_child + C * sqrt(log(N_parent) / N_child)
        self.score = 0
        self.N = 0
        self.reward = 0
        self.status = (W, B)
        self.move = move
        self.parent = parent
        self.parentN = -1
        # indiex of child node
        self.children = []
        self.priority = 1.0

    def initialize(self, move, W, B, parent):
        self.score = 0
        self.N = 0
        self.reward = 0
        self.status = (W, B)
        self.move = move
        self.parent = parent
        self.parentN = 0
        self.children = []
        self.priority = 1.0
        if self.move % 8 == 0 or self.move % 8 == 7 or self.move // 8 == 7 or self.move // 8 == 0:
            self.priority = 1.50
        if (self.move % 8 == 0 or self.move % 8 == 7) and (self.move // 8 == 7 or self.move // 8 == 0):
            self.priority = 1.575

    def update(self, reward):
        self.reward += reward
        self.N += 1
        # not the root node
        # if self.parent != -1:
        #     x_child = 1.0 * self.reward / self.N
        #     N_parent = treeNode[self.parent].N
        #     self.score = x_child + C * sqrt(log(N_parent) / self.N)

    def setChild(self, child):
        self.children.append(child)
        child.parent = self

    def getScore(self):
        if self.parentN != self.parent.N:
            self.parentN = self.parent.N
            x_child = 1.0 * self.reward / self.N
            self.score = (x_child * self.priority + C * sqrt(log(self.parentN) / self.N)).real
        return self.score


class NodePool:
    def __init__(self, NUM=250):
        self.NUM = NUM
        self.elements = [Node() for i in xrange(2000)]

    def free(self, nodeList):
        self.elements.extend(nodeList)

    def __extend__(self):
        self.elements = [Node() for i in xrange(self.NUM)]

    def pop(self):
        """:rtype: Node"""
        if not self.elements:
            self.__extend__()
        return self.elements.pop()


nodePool = NodePool()


class MctsEngine(Engine):
    def __init__(self):
        fill_radial_map()
        self.stepTime = 59.5

    def get_move(self, board, color, move_num=None,
                 time_remaining=None, time_opponent=None):
        W, B = to_bitboard(board)
        if color < 0:
            W, B = B, W

        global treeNode
        nodePool.free(treeNode)
        treeNode = [nodePool.pop()]
        treeNode[0].initialize(0, W, B, None)

        return self.montecarlo()

    def searchOnce(self):
        # get best child
        node = treeNode[0]
        path = [node]
        while node.children:
            node = max(node.children, key=lambda child: child.getScore())
            path.append(node)

        # expand
        W, B = node.status
        movemap = move_gen(W, B)
        mvlist = []
        while movemap != 0:
            mv, movemap = pop_lsb(movemap)
            mvlist.append(mv)
        if not mvlist:
            bitW = count_bit(W)
            bitB = count_bit(B)
            score = count_bit(W) - count_bit(B)
            if bitW + bitB != 64:
                score = -1
            if len(path) % 2 != 0:
                score = -score
            # reward = [1 if i % 2 == 0 and score > 0 or i % 2 != 0 and score < 0
            #           else 0 for i in xrange(len(path))]
            for i in xrange(len(path)):
                tmpNode = path[i]
                if i % 2 == 0 and score > 0 or i % 2 != 0 and score < 0:
                    tmpNode.update(1)
                else:
                    tmpNode.update(0)
            return
        for mv in mvlist:
            tmpW = W
            tmpB = B
            flipmask = flip(W, B, mv)
            tmpW ^= flipmask | BIT[mv]
            tmpB ^= flipmask
            childNode = nodePool.pop()
            childNode.initialize(mv, tmpB, tmpW, node)
            path.append(childNode)
            node.setChild(childNode)
            treeNode.append(childNode)

            for j in xrange(5):
                # childNode reward
                score = self.defaultPolicy(tmpB, tmpW)
                # get root score/reward
                if len(path) % 2 != 0:
                    score = -score
                # reward = [1 if i % 2 == 0 and score > 0 or i % 2 != 0 and score < 0
                #           else 0 for i in range(len(path))]
                for i in xrange(len(path)):
                    tmpNode = path[i]
                    # tmpNode.update(reward[i])
                    if i % 2 == 0 and score > 0 or i % 2 != 0 and score < 0:
                        tmpNode.update(1)
                    else:
                        tmpNode.update(0)

            path.pop()

    def defaultPolicy(self, W, B):
        movemap = move_gen(W, B)
        mvlist = []
        if movemap == 0:
            # return count_bit(W) - count_bit(B)
            bitW = count_bit(W)
            bitB = count_bit(B)
            # lose
            if bitW + bitB < 63:
                return -1
            return count_bit(W) - count_bit(B)
        while movemap != 0:
            mv, movemap = pop_lsb(movemap)
            mvlist.append(mv)
        mv = random.choice(mvlist)
        flipmask = flip(W, B, mv)
        W ^= flipmask | BIT[mv]
        B ^= flipmask
        return -self.defaultPolicy(B, W)

    def montecarlo(self):
        start_time = timeit.default_timer()
        end_time = timeit.default_timer()
        while end_time - start_time < self.stepTime:
            self.searchOnce()
            end_time = timeit.default_timer()
        child = max(treeNode[0].children, key=lambda child: child.getScore())
        # for i in treeNode[0].children:
        #     print i.N
        return to_move(child.move)


engine = MctsEngine
