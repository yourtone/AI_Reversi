from __future__ import absolute_import
from __future__ import division
from engines import Engine
import random
import time
import copy
from math import log, sqrt
#This class is used to note a node
class Stat(object):
    __slots__ = ('value', 'visits')

    def __init__(self, value=0, visits=0):
        self.value = value      #to note how many times the game via this node wins
        self.visits = visits    #to note how many times the engine has searched
class BetaDonkeyEngine(Engine):
    def __init__(self):
        self.BIT = [1 << n for n in range(64)]
        self.visited_states = {}
        self.stats = {}
        self.calculation_time = 58
        self.stats = {}                         #This value is used to note the states have been expanded
        self.FULL_MASK = 0xFFFFFFFFFFFFFFFF
        self.LSB_HASH = 0x07EDD5E59A4E28C2      #These are used for evaluation
        self.LSB_TABLE = [0] * 64
        self.bitmap = 1
        self.WEIGHTS = [-3, -7, 11, -4, 8, 1, 2]
        self.P_RINGS = [0x4281001818008142,
                        0x42000000004200,
                        0x2400810000810024,
                        0x24420000422400,
                        0x1800008181000018,
                        0x18004242001800,
                        0x3C24243C0000]
        self.P_CORNER = 0x8100000000000081
        self.P_SUB_CORNER = 0x42C300000000C342
        for i in range(64):
            self.LSB_TABLE[(((self.bitmap & (~self.bitmap + 1)) * self.LSB_HASH) & self.FULL_MASK) >> 58] = i
            self.bitmap <<= 1
        self.BIT = [1 << n for n in range(64)]          #The values below are used for bitmap which represents a board
        self.end_values = {}
        self.legalmoves = []
        self.DIR = [
            [1, -7, -8],
            [-1, -9, -8],
            [1, 8, 9],
            [7, 8, -1],
            [8, 9, 1, -7, -8],
            [-1, 1, -7, -8, -9],
            [7, 8, -1, -9, -8],
            [7, 8, 9, -1, 1],
            [-1, 1, -7, 7, -8, 8, -9, 9]]

        self.SQ_DIR = \
            [2, 2, 7, 7, 7, 7, 3, 3,
             2, 2, 7, 7, 7, 7, 3, 3,
             4, 4, 8, 8, 8, 8, 6, 6,
             4, 4, 8, 8, 8, 8, 6, 6,
             4, 4, 8, 8, 8, 8, 6, 6,
             4, 4, 8, 8, 8, 8, 6, 6,
             0, 0, 5, 5, 5, 5, 1, 1,
             0, 0, 5, 5, 5, 5, 1, 1]
        self.RADIAL_MAP = {}
        self.g_Weight = [
            [0x1 << 24, 0x1, 0x1 << 20, 0x1 << 16, 0x1 << 16, 0x1 << 20, 0x1, 0x1 << 24],
            [0x1, 0x1, 0x1 << 16, 0x1 << 4, 0x1 << 4, 0x1 << 16, 0x1, 0x1],
            [0x1 << 20, 0x1 << 16, 0x1 << 12, 0x1 << 8, 0x1 << 8, 0x1 << 12, 0x1 << 16, 0x1 << 20],
            [0x1 << 16, 0x1 << 4, 0x1 << 8, 0, 0, 0x1 << 8, 0x1 << 4, 0x1 << 16],
            [0x1 << 16, 0x1 << 4, 0x1 << 8, 0, 0, 0x1 << 8, 0x1 << 4, 0x1 << 16],
            [0x1 << 20, 0x1 << 16, 0x1 << 12, 0x1 << 8, 0x1 << 8, 0x1 << 12, 0x1 << 16, 0x1 << 20],
            [0x1, 0x1, 0x1 << 16, 0x1 << 4, 0x1 << 4, 0x1 << 16, 0x1, 0x1],
            [0x1 << 24, 0x1, 0x1 << 20, 0x1 << 16, 0x1 << 16, 0x1 << 20, 0x1, 0x1 << 24]
        ]
        #to initiate the values
        rad_map = {-1: (-1, 0), 1: (1, 0), -8: (0, -1), 8: (0, 1), -7: (1, -1), 7: (-1, 1), -9: (-1, -1), 9: (1, 1)}
        for dir, dirtup in rad_map.items():
            lis = [0] * 64
            for sqr in range(64):
                mask = 0
                sq = sqr
                x, y = self.to_move(sq)
                sq += dir
                x += dirtup[0]
                y += dirtup[1]
                while 0 <= x < 8 and 0 <= y < 8 and 0 <= sq < 64:
                    mask |= self.BIT[sq]
                    sq += dir
                    x += dirtup[0]
                    y += dirtup[1]
                lis[sqr] = mask
            self.RADIAL_MAP[dir] = lis
    #THis is a standard function given by TA
    def get_move(self, board, color, move_num=None,time_remaining=None, time_opponent=None):
        W, B = self.to_bitboard(board)
        wb = (W, B)# if color > 0 else (B, W)
        begin = time.time()
        self.stats = {}
        i = 0
        while time.time() - begin < self.calculation_time:  #calculate while there remains time
            begin_oneloop = time.time()
            i+=1
            self.run_simulation(wb[0], wb[1], color, i)
            end = time.time()
            #print "oneloop:\t",
            #print end-begin_oneloop
        actions_states = []
        print '*********************////*/*/******************************search times:',
        print i
        maxnum = 0
        bestmov = self.legalmoves[0]        #from the set of legal moves, we choose the best one
        if color > 0:
            for p in self.legalmoves:
                #a = self.to_move(p)
                #print a
                tmpW = W
                tmpB = B
                #self.print_bitboard(tmpB)
                #self.print_bitboard(tmpW)
                flipmask = self.flip(tmpW, tmpB, p)
                tmpW ^= flipmask | self.BIT[p]
                tmpB ^= flipmask
                if (color, tmpW,tmpB) in self.stats:
                    if self.stats[(color, tmpW, tmpB)].visits == 0:
                        self.print_bitboard(tmpW)
                        self.print_bitboard(tmpB)
                        print "aaaa"
                    num = self.stats[(color, tmpW,tmpB)].value / self.stats[(color, tmpW, tmpB)].visits
                    if num >= maxnum:
                        maxnum = num
                        bestmov = p
        else:
            for p in self.legalmoves:
                #a = self.to_move(p)
                #print a
                tmpW = W
                tmpB = B
                #self.print_bitboard(tmpW)
                #self.print_bitboard(tmpB)
                flipmask = self.flip(tmpB, tmpW, p)
                tmpW ^= flipmask
                tmpB ^= flipmask | self.BIT[p]
                #self.print_bitboard(tmpW)
                #self.print_bitboard(tmpB)
                if (color, tmpW, tmpB) in self.stats:
                    if self.stats[(color, tmpW, tmpB)].visits == 0:
                        self.print_bitboard(tmpW)
                        self.print_bitboard(tmpB)
                        print "aaaa"
                    num = self.stats[(color, tmpW, tmpB)].value / self.stats[(color, tmpW, tmpB)].visits
                    print "visitimes:",
                    print self.stats[(color, tmpW, tmpB)].visits,
                    print "\tvalue",
                    print self.stats[(color, tmpW, tmpB)].value
                    if num >= maxnum:
                        maxnum = num
                        bestmov = p
        return self.to_move(bestmov)
    #This function is used to simulate
    def run_simulation(self, W, B, color, i):
        current_W = W #copy.deepcopy(W)     #first we initiate some values
        current_B = B #copy.deepcopy(B)
        current_color = color
        visited_states = set()
        stats = self.stats
        expand = True
        #print 'before gogogo'
        #begin = time.time()
        firstBlood = True
        count = 0
        while True:                         #simulate until a terminal state
            count+=1
            if count > 128:                 #was used to ensure there is no chance to enter a dead loop
                return
            #begin_oneloop = time.time()
            #print 'begin time:\t\t',
            #print begin_oneloop
            wmovemap = self.move_gen(current_W, current_B)
            bmovemap = self.move_gen(current_B, current_W)
            if self.isOver(wmovemap, bmovemap, current_color):
                break
            #print '\t\t',
            #print time.time()
            #print '\t\t',
            #print time.time()
            actions_states = []
            legal_moves = []                #get the legal moves at this state using bitmap
            if current_color > 0:
                while wmovemap != 0:
                    onemov, wmovemap = self.pop_lsb(wmovemap)
                    #print self.to_move(onemov)
                    legal_moves.append(onemov)
                    tmpW = current_W
                    #self.print_bitboard(tmpW)
                    tmpB = current_B
                    #self.print_bitboard(tmpB)
                    flipmask = self.flip(tmpW, tmpB, onemov)
                    tmpW ^= flipmask | self.BIT[onemov]
                    #self.print_bitboard(tmpW)
                    tmpB ^= flipmask
                    #self.print_bitboard(tmpB)
                    actions_states.append((onemov,tmpW, tmpB))
            else:
                while bmovemap != 0:
                    onemov, bmovemap = self.pop_lsb(bmovemap)
                    #print self.to_move(onemov)
                    legal_moves.append(onemov)
                    tmpW = current_W
                    #self.print_bitboard(tmpW)
                    tmpB = current_B
                    #self.print_bitboard(tmpB)
                    flipmask = self.flip(tmpB, tmpW, onemov)
                    tmpW ^= flipmask
                    #self.print_bitboard(tmpW)
                    tmpB ^= flipmask | self.BIT[onemov]
                    #self.print_bitboard(tmpB)
                    actions_states.append((onemov,tmpW, tmpB))
            if i == 1 and firstBlood:
                firstBlood = False
                self.legalmoves = copy.deepcopy(legal_moves)
            #print '\t\t',
            #print time.time()
            #actions_states = [(p, self.board.next_state(state, p)) for p in legal_moves]
            if len(actions_states) != 0:                #check if there is a pass
                if all((current_color, W ,B) in stats for p, W, B in actions_states):   #if all of them have been expanded
                    log_total = log(sum(stats[(current_color, W ,B)].visits for p, W, B in actions_states) or 1)
                    maxnum = 0
                    for p, W, B in actions_states:              #use UCT formulation to choose
                        num = ((stats[(current_color, W ,B)].value / (stats[(current_color, W ,B)].visits or 1)) +
                         self.C * sqrt(log_total / (stats[(current_color, W ,B)].visits or 1)))
                        if num >= maxnum:
                            maxnum = num
                            action = p
                            current_W = W
                            current_B = B
                else:
                    action, W, B = random.choice(actions_states)            #or we find a step using FUTP(first urgent to play)
                    current_W = W
                    current_B = B
                    max = 0
                    for action, W, B in actions_states:
                        if (current_color, W, B) in stats:
                            continue
                        if current_color > 0:
                            value = self.eval(W, B)
                            #value = self.eval_new(action)
                        else:
                            value = self.eval(B, W)
                            #value = self.eval_new(action)
                        if value > max:
                            max = value
                            current_W = W
                            current_B = B

                if expand and (current_color, current_W, current_B) not in stats:       #if we need to expand a node
                    expand = False
                    stats[(current_color, current_W, current_B)] = Stat()
                visited_states.add((current_color, current_W, current_B))

            current_color = -current_color                          #get to next state
            end_oneloop = time.time()
        end = time.time()
        black_count = self.count_bit(current_B)                     #check if this path is good or not
        white_count = self.count_bit(current_W)

        #print 'before goback'
        self.end_values[1] = 0
        self.end_values[-1] = 0
        if black_count > white_count:
            self.end_values[-1] = 1
            self.end_values[1]  = 0
        elif black_count < white_count :
            self.end_values[-1] = 0
            self.end_values[1]  = 1
        for player, W,B in visited_states:                          #back through
            if (player, W, B) not in stats:
                continue
            S = stats[(player, W, B)]
            S.visits += 1
            S.value += self.end_values[player]

    def isOver(self, wmovemap, bmovemap, current_color):            #check if the game is over
        if wmovemap == 0 and bmovemap == 0:
            return True
        return False

    def to_bitboard(self,board):                                    #convert the standard board to bitboard for acceleration
        W = 0
        B = 0
        for r in range(8):
            for c in range(8):
                if board[c][r] == -1:
                    B |= self.BIT[8 * r + c]
                elif board[c][r] == 1:
                    W |= self.BIT[8 * r + c]
        return (W, B)

    def move_gen_sub(self, P, mask, dir):               #generate the legal moves
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

    def move_gen(self,P, O):
        mask = O & 0x7E7E7E7E7E7E7E7E
        return ((self.move_gen_sub(P, mask, 1) \
                 | self.move_gen_sub(P, O, 8) \
                 | self.move_gen_sub(P, mask, 7) \
                 | self.move_gen_sub(P, mask, 9)) & ~(P | O)) & self.FULL_MASK

    def lsb(self, bitmap):
        return self.LSB_TABLE[(((bitmap & (~bitmap + 1)) * self.LSB_HASH) & self.FULL_MASK) >> 58]

    def pop_lsb(self, bitmap):
        l = self.lsb(bitmap)
        bitmap &= bitmap - 1
        return l, bitmap & self.FULL_MASK

    def count_bit(self, b):
        b -= (b >> 1) & 0x5555555555555555;
        b = (((b >> 2) & 0x3333333333333333) + (b & 0x3333333333333333));
        b = ((b >> 4) + b) & 0x0F0F0F0F0F0F0F0F;
        return ((b * 0x0101010101010101) & self.FULL_MASK) >> 56

    def flip(self, W, B, mv):
        mask = 0
        for dir in self.DIR[self.SQ_DIR[mv]]:
            mvtmp = mv
            mvtmp += dir
            while mvtmp >= 0 and mvtmp < 64 and (self.BIT[mvtmp] & B != 0) and (self.BIT[mvtmp] & self.RADIAL_MAP[dir][mv] != 0):
                mvtmp += dir
            if (mvtmp >= 0 and mvtmp < 64 and self.BIT[mvtmp] & W != 0) and (self.BIT[mvtmp] & self.RADIAL_MAP[dir][mv] != 0):
                mvtmp -= dir
                while mvtmp != mv:
                    mask |= self.BIT[mvtmp]
                    mvtmp -= dir

        return mask

    def to_move(self, bitmove):
        return (bitmove % 8, bitmove // 8)

    def print_bitboard(self,BB):
        bitarr = [1 if (1 << i) & BB != 0 else 0 for i in range(64)]
        s = ""
        for rk in range(7, -1, -1):
            for fl in range(8):
                s += str(bitarr[fl + 8 * rk]) + " "
            s += "\n"
        print s

    def eval_new(self, action):  # W is mine and it's a naive evaluation method
        location = self.to_move(action)
        return self.g_Weight[location[0]][location[1]]

    def eval(self, W, B):       #a mature evaluation method
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

            #         scorepiece = \
            #             10.0 * wpiece / (wpiece + bpiece) if wpiece > bpiece \
            #             else -10.0 * bpiece / (wpiece + bpiece) if wpiece < bpiece \
            #             else 0
        scorepiece = wpiece - bpiece

        # mobility
        wmob = self.count_bit(self.move_gen(W, B))

        scoremob = 20 * wmob

        return scorepiece + scoreunstable + scoremob
engine = BetaDonkeyEngine