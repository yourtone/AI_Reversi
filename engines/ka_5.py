from __future__ import absolute_import

import copy
import math
import random
import time

from engines import Engine


class KaEngine(Engine):
    # Any subclass must implement this method or otherwise raise a
    # NotImplementedError.
    def get_move(self, board, color, move_num=None, time_remaining=None, time_opponent=None):
        self.color = color  # 记录自身是黑方还是白方
        self.remainingTime = time_remaining  # 记录搜索允许的剩余时间

        board = copy.deepcopy(board)  # 深度复制棋盘，防止对原对象的修改
        color = copy.deepcopy(color)
        state = (board, color)  # 初始状态包括初始棋盘和自身代表的颜色

        return self.search(state)  # 返回搜索的结果

    # 树搜索
    def search(self, state):
        # 包含初始状态的初始节点，指向该节点的行为是None，父节点是None
        rootNode = Node(state, None, None)

        startTime = time.time()  # 记录搜索开始的时间
        while time.time() - startTime < self.remainingTime / 2000:  # 如果时间超过剩余时间的1/2000，停止搜索
            selectedNode = self.treePolicy(rootNode)  # 选择一个子节点
            delta = self.simulate(selectedNode.state)  # 对该子节点进行模拟，得到收益值
            self.backPropagate(selectedNode, delta)  # 使用该收益值更新路径上的所有节点

        return self.getBestAction(rootNode)  # 搜索结束，选择最佳的行为

    # 选择子节点的策略
    def treePolicy(self, rootNode):
        if len(rootNode.legalMoves) == 0:  # 如果初始节点是结束状态（没有子节点）
            return rootNode  # 返回这个初始节点
        elif len(rootNode.triedMoves) < len(rootNode.legalMoves):  # 如果初始节点存在未被扩展的子节点
            # 获取初始节点未使用过的行为（对应一个新的未被扩展的子节点）
            untriedMoves = [
                move for move in rootNode.legalMoves
                if move not in rootNode.triedMoves
            ]
            move = random.choice(untriedMoves)  # 随机选择一个未使用过的行为
            rootNode.triedMoves.add(move)  # 更新初始节点的已使用的行为列表

            # 赋值初始节点的状态
            nextBoard = copy.deepcopy(rootNode.state[0])
            nextColor = copy.deepcopy(rootNode.state[1])
            # 根据选择的行为产生下一个节点所包含状态
            nextBoard.execute_move(move, nextColor)
            nextColor = -nextColor
            nextState = (nextBoard, nextColor)

            return Node(nextState, move, rootNode)  # 返回新生成的子节点
        else:  # 如果初始节点不存在未被扩展的子节点
            return self.treePolicy(self.getBestChild(rootNode))  # 选择初始节点的最佳子节点

    # 获取最佳子节点
    def getBestChild(self, node):
        # 使用UCB算法
        parentNumber = node.number
        for childNode in node.childNodes:
            childNumber = childNode.number
            childReward = childNode.reward
            if node.state[1] != self.color:
                childReward = -childReward
            childNode.value = (1.0 * childReward / childNumber) + 8 * \
                math.sqrt(2.0 * math.log(parentNumber) / childNumber)

        # 根据UCB算法计算的结果进行从大到小的排序
        node.childNodes.sort(key=lambda node: node.value, reverse=True)
        return node.childNodes[0]  # 返回计算结果最大的节点作为最佳子节点

    # 模拟
    def simulate(self, state):
        state = copy.deepcopy(state)  # 深度复制，防止对原对象的修改
        count = 0  # 回合数
        boardCount = state[0].count(-1) + state[0].count(+1)  # 初始状态上棋盘的所有棋子数
        while True:
            blackLegalMoves = state[0].get_legal_moves(-1)  # 黑方能够采取的行为数量
            whiteLegalMoves = state[0].get_legal_moves(+1)  # 白方能够采取的行为数量
            # 如果回合数不在下限和上限内，或者当前状态到达结束状态（双方均没有能够采取的行为）
            if count < 16 or count > boardCount / 2 or (len(blackLegalMoves) == 0 and len(whiteLegalMoves) == 0):
                blackCount = state[0].count(-1)
                whiteCount = state[0].count(+1)
                # 返回双方的棋子数量差作为delta
                if self.color == 1:
                    return whiteCount - blackCount
                else:
                    return blackCount - whiteCount
            else:
                # 继续下一回合的模拟
                legalMoves = state[0].get_legal_moves(state[1])
                if len(legalMoves) != 0:  # 如果某一方有能够采取的行为
                    move = random.choice(legalMoves)  # 随机选择一个行为
                    state[0].execute_move(move, state[1])  # 执行该行为
                state = (state[0], -state[1])  # 下一回合交给对手
            count += 1  # 回合数加1

    # 最佳行为
    def getBestAction(self, node):
        # 根据收益值/总次数，选择最大的节点对应的行为
        bestRatio = None
        bestActions = []
        for childNode in node.childNodes:
            ratio = 1.0 * childNode.reward / childNode.number
            if bestRatio is None:
                bestRatio = ratio
                bestActions = [childNode.move]
            elif ratio > bestRatio:
                bestRatio = ratio
                bestActions = [childNode.move]
            elif ratio == bestRatio:
                bestActions.append(childNode.move)
            #print ("%s, %+5d, %+5d, %+7.3f, %+7.3f" % (childNode.move, childNode.reward, childNode.number, ratio, childNode.value))
        # print bestActions
        return random.choice(bestActions)  # 如果并列的行为有多个，随机选择

    # 更新路径上的节点
    def backPropagate(self, node, delta):
        # 从当前节点沿着路径返回直至根节点
        while node is not None:
            node.number += 1  # 模拟次数加1
            node.reward += delta  # 收益值加delta
            node = node.parentNode


# 节点类
class Node:
    def __init__(self, state, move, parentNode):
        self.state = state  # 状态，包括棋盘和颜色
        self.move = move  # 指向该节点的行为

        self.parentNode = parentNode  # 父节点
        self.childNodes = []  # 子节点列表

        self.legalMoves = state[0].get_legal_moves(state[1])  # 能采取的行为
        self.triedMoves = set()  # 已采取的行为

        self.number = 0  # 模拟次数
        self.reward = 0  # 收益值
        self.value = 0.0  # UCB算法得到的值，供测试

        if parentNode is not None:
            parentNode.childNodes.append(self)  # 构造过程中，将该节点添加至父节点的子节点列表


engine = KaEngine
