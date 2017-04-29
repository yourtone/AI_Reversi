# -*- coding: utf-8 -*-
from __future__ import absolute_import
from engines import Engine
from copy import deepcopy
from math import sqrt
from math import log
import time
import random



class MCTSEngine(Engine):
    def get_move(self, board, color, move_num=None,
                 time_remaining=None, time_opponent=None):
        v0 = Node(None, board, color, (-1,-1))  # 创建 v0 root 节点
        start_time = time.time()
        budget = 0.5      # 能承受的计算负担       单位: 秒

        while time.time() < start_time + budget:
            vl = self.TreePolicy(v0)
            delta = self.DefaultPolicy(vl.state, vl.color)
            self.BackUp(vl, delta)
        bestchild = self.BestChild(v0, 0)   # 选择最好的子节点
        return bestchild.move   # 返回最好的下棋点
    
    
    def TreePolicy(self, v):
        moves = v.state.get_legal_moves(v.color)    # 获得所有合法的下棋点
        while len(moves) != 0:  # 当存在下棋点
            if v.children_pos != len(moves):    # 子节点的扩展为: 将得到的合法下棋点moves从第一个到最后一个依次扩展
                                                # 因此当 children_pos = len(moves) 时说明全部扩展完了
                return self.Expand(v, moves)
            else:
                v = self.BestChild(v)
        return v
    
    
    def Expand(self, v, moves):
        move = moves[v.children_pos]
        v.children_pos += 1         # 扩展一个子节点，children_pos +1
        state__ = deepcopy(v.state)
        state__.execute_move(move, v.color) # 进行一步下棋
        v__ = Node(v, state__, -v.color, move)  # 创建子节点
        v.children.append(v__)  # 添加子节点
        return v__
    
    
    def BestChild(self, v, c = 1):  # 默认 c = 1
        BestValue = 0.0 # 记录最优的值
        BestIndex = 0   # 记录最优值子节点的位置
        for i in range(0, v.children_pos):
            q = float(v.children[i].Q_value) / float(v.children[i].N_value)
            p = float(sqrt(2 * log(v.N_value)) / float(v.children[i].N_value))
            BestValue__ = float(q + c * p)
            if BestValue__ > BestValue:
                BestValue = BestValue__
                BestIndex = i
        return v.children[BestIndex]    # 返回最优子节点
    
    
    def DefaultPolicy(self, state, color):
        #color = -color
        moves = state.get_legal_moves(color)    # 获得所有合法的下棋点
        while len(moves) != 0:                  # 如果存在下棋点
            move = random.choice(moves)         # 随机选择一个下棋点
            state.execute_move(move, color)     # 进行下棋
            color = -color                      # 反转颜色轮到对手下棋
            moves = state.get_legal_moves(color)    # 获得所有合法的下棋点
        # -1 black   1 white
        count = []
        count.append(state.count(-1))
        count.append(state.count(1))
        return count    # 返回reward: 为(黑子的个数, 白子的个数)
    
    
    def BackUp(self, v, delta): # 更新数据
        while v != None:
            v.N_value += 1
            v.Q_value += delta[int(v.color * 1/2 + 1/2)]
            v = v.parent
                    
# 树节点的结构
class Node(object):
    def __init__(self, parent, state, color, move):
        self.parent = parent    # 指向父节点
        self.children = []      # 存储所有的子节点
        self.children_pos = 0   # 记录正在使用的子节点的位置
        self.state = deepcopy(state)    # board 的复制
        self.color = color      # 存储颜色
        self.move = move        # 存储节点选择的下棋点
        self.N_value = 0        # 存储 N(v)
        self.Q_value = 0        # 存储 Q(v)
        



engine = MCTSEngine
