#! encoding: utf-8
from __future__ import absolute_import
import random
import time
from math import log, sqrt
import copy
from engines import Engine

p6=20
p5=7
p4=6
p3=5
p2=2
p1=1
p0=0

priority = {}
priority[( 0 , 0 )] = p6
priority[( 0 , 1 )] = p1
priority[( 0 , 2 )] = p5
priority[( 0 , 3 )] = p5
priority[( 0 , 4 )] = p5
priority[( 0 , 5 )] = p5
priority[( 0 , 6 )] = p1
priority[( 0 , 7 )] = p6
priority[( 1 , 0 )] = p1
priority[( 1 , 1 )] = p0
priority[( 1 , 2 )] = p2
priority[( 1 , 3 )] = p2
priority[( 1 , 4 )] = p2
priority[( 1 , 5 )] = p2
priority[( 1 , 6 )] = p0
priority[( 1 , 7 )] = p1
priority[( 2 , 0 )] = p5
priority[( 2 , 1 )] = p2
priority[( 2 , 2 )] = p4
priority[( 2 , 3 )] = p4
priority[( 2 , 4 )] = p4
priority[( 2 , 5 )] = p4
priority[( 2 , 6 )] = p2
priority[( 2 , 7 )] = p5
priority[( 3 , 0 )] = p5
priority[( 3 , 1 )] = p2
priority[( 3 , 2 )] = p4
priority[( 3 , 3 )] = p3
priority[( 3 , 4 )] = p3
priority[( 3 , 5 )] = p4
priority[( 3 , 6 )] = p2
priority[( 3 , 7 )] = p5
priority[( 4 , 0 )] = p5
priority[( 4 , 1 )] = p2
priority[( 4 , 2 )] = p4
priority[( 4 , 3 )] = p3
priority[( 4 , 4 )] = p3
priority[( 4 , 5 )] = p4
priority[( 4 , 6 )] = p2
priority[( 4 , 7 )] = p5
priority[( 5 , 0 )] = p5
priority[( 5 , 1 )] = p2
priority[( 5 , 2 )] = p4
priority[( 5 , 3 )] = p4
priority[( 5 , 4 )] = p4
priority[( 5 , 5 )] = p4
priority[( 5 , 6 )] = p2
priority[( 5 , 7 )] = p5
priority[( 6 , 0 )] = p1
priority[( 6 , 1 )] = p0
priority[( 6 , 2 )] = p2
priority[( 6 , 3 )] = p2
priority[( 6 , 4 )] = p2
priority[( 6 , 5 )] = p2
priority[( 6 , 6 )] = p0
priority[( 6 , 7 )] = p1
priority[( 7 , 0 )] = p6
priority[( 7 , 1 )] = p1
priority[( 7 , 2 )] = p5
priority[( 7 , 3 )] = p5
priority[( 7 , 4 )] = p5
priority[( 7 , 5 )] = p5
priority[( 7 , 6 )] = p1
priority[( 7 , 7 )] = p6

class Statistics(object):
    __slots__ = ('value', 'visits')

    def __init__(self,value=0,visits=0):
        self.value=value
        self.visits=visits

#one state(tuple): p1 placed(black), p2 placed(white), player to move # 1 correspond white and -1 correspond black
#placed 由00110010...表示

# data:
# 'pieces': pieces,pieces由多个字典{'type': 'disc', 'player': 1, 'row': r, 'column': c}组成
# 'player': player,
# 'previous_player': previous,

#          1:black -1:white
def trans(board,color):
    states={-1:0,1:0}
    for x in xrange(7,-1,-1):
        for y in xrange(8):
            if(board[x][y] == 1):
                states[1] += 1 << ((7-x) * 8 + y)
            elif(board[x][y] == -1):
                states[-1] += 1 << ((7-x) * 8 + y)

    return (states[1],states[-1],color)

class UCT(object): #父类
    def __init__(self,board,color,time=60, **kwargs): #board:当前状态 color:下一步要走的人 time:规定时间
        self.board=board
        self.color=color

        self.statistics={} #每调用一次get_action()就清空一次记录 当次get_action()所探索到的所有(player, state)#当前player和他导致的下一个状态
        self.history=[]
        self.state=trans(board,color) #当前state:(state[1], state[-1], player)

        self.max_depth=0
        self.data={}

        self.calculation_time=time
        self.max_actions=int(kwargs.get('max_actions',8))
        self.C=float(kwargs.get('C',1.4))

    def update(self,state):
        self.history.append(state)

    def is_end(self,board, state): #当前board,当前state,当前player
        p1_palce, p2_place, player = state

        if p1_palce == 0:
            return True
        if p2_place == 0:
            return True

        occupied = p1_palce | p2_place
        return ((occupied == (1 << (8 * 8)) - 1) or (len(board.get_legal_moves(player)) == 0))

    def end_value(self,board,state):
        if not self.is_end(board,state):
            return

        p1_placed, p2_placed, player = state

        p1_score = bin(p1_placed).count('1')
        p2_score = bin(p2_placed).count('1')

        if p1_score > p2_score:
            return {1: 1, -1: 0}
        if p2_score > p1_score:
            return {1: 0, -1: 1}
        if p1_score == p2_score:
            return {1: 0.5, -1: 0.5}

    def point_value(self,board, state):
        # if not self.is_end(board,state):
        #     return
        # p1_placed, p2_placed, player = state
        #
        # p1_score = bin(p1_placed).count('1')
        # p2_score = bin(p2_placed).count('1')
        #
        # return {1: p1_score, -1: p2_score}
        p1_score = 0
        p2_score = 0
        for x in xrange(7, -1, -1):
            for y in xrange(8):
                if (board[x][y] == 1):
                    p1_score += priority[(x, y)]
                elif (board[x][y] == -1):
                    p2_score += priority[(x, y)]
        return {1: p1_score, -1: p2_score}




    def get_action(self):
        # Causes the AI to calculate the best action from the
        # current game state and return it.

        self.max_depth = 0
        self.data = {}
        self.statistics.clear()  # 每调用一次get_action()，就清空一次记录

        state = self.state
        player = self.color
        legal = self.board.get_legal_moves(self.color)

        if not legal:
            return
        if len(legal) == 1:
            return legal[0]

        games = 0
        begin = time.time()
        while time.time() - begin < (self.calculation_time - 1):
            self.run_simulation()
            games += 1

        # Display the number of calls of `run_simulation` and the
        # time elapsed.
        self.data.update(games=games, max_depth=self.max_depth,
                         time=str(time.time() - begin))
        #print self.data['games'], self.data['time']
        #print "Maximum depth searched:", self.max_depth

        # Store and display the stats for each possible action.
        finalact = self.calculate_action_values(self.board,state, player, legal)
        #for m in self.data['actions']:
        #    print self.action_template.format(**m)

        # Pick the action with the highest average value.
        return finalact  # 将二进制转换为坐标

    # newboard = deepcopy(board)
    # newboard.execute_move(mv, color)
    def run_simulation(self):
        # Plays out a "random" game from the current position,
        # then updates the statistics tables with the result.

        # A bit of an optimization here, so we have a local
        # variable lookup instead of an attribute access each loop.

        statistics = self.statistics

        newboard=copy.deepcopy(self.board)

        visited_state=set()
        player=self.color

        expand=True
        for t in xrange(1,self.max_actions+1):
            legal=newboard.get_legal_moves(player)
            actions_states=[] #actions_states = [(p, self.board.next_state(state, p)) for p in legal] #当前状态下所有合法动作和下一个状态
            for act in legal:
                tmp_board=copy.deepcopy(newboard)
                tmp_board.execute_move(act,player)

                if len(tmp_board.get_legal_moves(-player)) != 0:
                    actions_states.append((act, trans(tmp_board, -player)))
                else:
                    actions_states.append((act, trans(tmp_board, player)))

            if all((player,S) in statistics for p,S in actions_states):
                # If we have stats on all of the legal actions here, use UCB1.
                log_total = log(sum(statistics[(player, S)].visits for p, S in actions_states) or 1)

                value, action, state = max(
                    ((statistics[(player, S)].value / (statistics[(player, S)].visits or 1)) +
                     self.C * sqrt(log_total / (statistics[(player, S)].visits or 1)), p, S)
                    for p, S in actions_states
                )
            else:
                expand = True
                collection = [(p, S) for (p, S) in actions_states if (player, S) not in statistics]
                action, state = random.choice(collection)
                # Otherwise, just make an arbitrary decision.
                # action, state = random.choice(actions_states)

            newboard.execute_move(action,player)

            # `player` here and below refers to the player
            # who moved into that particular state.
            if expand and (player, state) not in statistics:
                expand = False
                statistics[(player, state)] = Statistics()
                if t > self.max_depth:
                    self.max_depth = t


            visited_state.add((player, state))
            player=state[-1]
            if(self.is_end(newboard,state)):
                break

        # Back-propagation
        finial_values = self.finial_value(newboard,state)
        for player, state in visited_state:
            if (player, state) not in statistics:
                continue
            S = statistics[(player, state)]
            S.visits += 1
            S.value += finial_values[player]


class UCTWins(UCT):#按最终输赢评估
    action_template = "{action}: {percent:.2f}% ({wins} / {plays})"

    def __init__(self, board,color,time=60, **kwargs):
        super(UCTWins, self).__init__(board,color,time, **kwargs)
        self.finial_value = self.end_value  # 最终结果

    def calculate_action_values(self,board, state, player, legal): #在当前状态下对每个动作的评估
        # actions_states = [(p, self.board.next_state(state, p)) for p in legal] #当前状态下所有合法动作和下一个状态
        actions_states = []
        for act in legal:
            tmp_board = copy.deepcopy(board)
            tmp_board.execute_move(act, player)

            if len(tmp_board.get_legal_moves(-player)) != 0:
                actions_states.append((act, trans(tmp_board, -player)))
            else:
                actions_states.append((act, trans(tmp_board, player)))
        #actions_states = ((p, self.board.next_state(state, p)) for p in legal)
        self.data['actions'] = sorted(
            ({'action': p,
              'percent': 100 * self.statistics[(player, S)].value / self.statistics[(player, S)].visits,
              'wins': self.statistics[(player, S)].value,
              'plays': self.statistics[(player, S)].visits}
             for p, S in actions_states if (player, S) in self.statistics),
            key=lambda x: (x['percent'], x['plays']),
            reverse=True
        )
        #print self.data['actions'][0]['action'], self.data['actions'][0]['percent']
        return self.data['actions'][0]['action']

class UCTValues(UCT):#按最终棋子数评估
    action_template = "{action}: {average:.1f} ({sum} / {plays})"


    def __init__(self, board,color,time=60, **kwargs):
        super(UCTValues, self).__init__(board,color,time, **kwargs)
        self.finial_value = self.point_value

    def calculate_action_values(self,board, state, player, legal):
        actions_states = []
        for act in legal:
            tmp_board = copy.deepcopy(board)
            tmp_board.execute_move(act, player)

            if len(tmp_board.get_legal_moves(-player)) != 0:
                actions_states.append((act, trans(tmp_board, -player)))
            else:
                actions_states.append((act, trans(tmp_board, player)))
        #actions_states = ((p, self.board.next_state(state, p)) for p in legal)
        self.data['actions'] = sorted(
            ({'action': p,
              'average': self.statistics[(player, S)].value / self.statistics[(player, S)].visits,
              'sum': self.statistics[(player, S)].value,
              'plays': self.statistics[(player, S)].visits}
             for p, S in actions_states if (player, S) in self.statistics),
            key=lambda x: ((x['average']/32.0)*0.2+(priority[x['action']]/5.0)*0.8, x['plays']),
            reverse=True
        )
        #print "a:",(self.data['actions'][0]['average']/32.0),"b:",(priority[self.data['actions'][0]['action']]/5.0)
        # print self.data['actions'][0]['action']
        # for m in self.data['actions']:
        #     print self.action_template.format(**m)
        return self.data['actions'][0]['action']





class MCTSEngine(Engine):
    def get_move(self, board, color, move_num=None,time_remaining=None, time_opponent=None):
        time_remaining=60
        mctsengine=UCTValues(board,color,time_remaining)
        return mctsengine.get_action()

engine = MCTSEngine

