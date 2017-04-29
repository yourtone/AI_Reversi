#coding:utf-8
from __future__ import absolute_import
import time,copy,math,random
from board import Board
from copy import deepcopy

from engines import Engine

occ = 2  # expand某一节点时，用occ来占位方便计算
white = 1
black = -1

weight = [[30, 5,20,15,15,20, 5,30], [5, 3,10,11,11,10, 3, 5], [20,10,12,12,12,12,10,20], [15,11,12,10,10,12,11,15], [15,11,12,10,10,12,11,15], [20,10,12,12,12,12,10,20], [5, 3,10,11,11,10, 3, 5], [30, 5,20,15,15,20, 5,30]]
goi = [0 for o in range(64)]
goj = [0 for p in range(64)]

class Node:  # 节点信息
    def __init__(self, data):
        self.data = data  # 棋盘
        self.total_value = 0  # 胜利次数
        self.times = 0  # 访问次数
        self.children = []  # 子节点
        self.parent = None  # 父节点
        self.position = [-1, -1]  # 当前棋盘下的棋子位置

    def getdata(self):
        return self.data

    def getchildren(self):
        return self.children

    def getparent(self):
        return self.parent

    def add(self, node):  # 增加子节点
        node.parent = self
        self.children.append(node)

class tree:  # 设置树
    def __init__(self):
        self.head = Node('header')

    def linktohead(self, node):
        self.head.add(node)

def TreePolicy(node,flag):
    f_node = node
    t_node = copy.deepcopy(node)
    board = copy.deepcopy(node.data)
    while If_Win(t_node)==False:
        position = If_go(t_node,flag)
        board[position[0]][position[1]] = flag
        if position!=[-1,-1]:
            if f_node.children == []:
                return Expand(f_node,position,flag)
            else:
                for child in f_node.children:
                    if position[0] != child.position[0] or position[1] != child.position[1]:
                        return Expand(f_node,position,flag)
                    else:
                        board[position[0]][position[1]] = 0
                        position = If_go(t_node, flag)
                        board[position[0]][position[1]] = flag
        if position!=[-1,-1]:
            return Expand(f_node,position,flag)
        else:
            f_node = BestChild(f_node,1)
            if f_node == None:
                return None
            t_node = copy.deepcopy(f_node)
            flag = -flag
    return f_node

# def Compare_array(a1,a2):
#    for i in range(0,8):
#        for j in range(0,8):
#            if a1[i][j]!=a2[i][j]:
#                return False
#    return True

def Expand(node, position, flag):  # 添加子节点
    tmp_chess = copy.deepcopy(node.data)
    tmp_chess[position[0]][position[1]] = flag
    tmp = Node(tmp_chess)
    Replace(tmp, flag, position)
    tmp.position = copy.deepcopy(position)
    node.add(tmp)
    return tmp

def BestChild(node, factor):  # 按照公式计算bestchild
    if len(node.children) == 0:
        return None
    else:
        maxi = copy.deepcopy(node.children[0])
        for i in node.children:
            if Canculate(i, factor) > Canculate(maxi, factor):
                maxi = i
        return maxi

def Canculate(node, factor):  # 计算公式
    val = node.total_value / node.times
    tmp = 2 * math.log(node.times, math.e) / node.times
    val = val + factor * math.sqrt(tmp)
    return val

def DefaultPolicy(node,flag):
    timet = time.time()
    t_node = copy.deepcopy(node)
    test = 999
    flag = -flag

    debug = 0

    while If_Win(t_node)==False and debug < 60:
        #i = random.randint(0,7);
        #j = random.randint(0,7);
        debug = debug + 1


        total = 0
        sum = 0
        for i in range(0, 8):
            for j in range(0, 8):
                if IfValid(t_node, flag, i, j) == 1:
                    goi[total] = i
                    goj[total] = j
                    total = total + 1
                    sum = sum + weight[i][j]
        choose = random.randint(0, sum)
        while choose > 0:
            total = total - 1
            choose = choose - weight[goi[total]][goj[total]]
        i = goi[total]
        j = goj[total]


        if t_node.data[i][j] == 0:
            t_node.data[i][j] = flag
            Replace(t_node,flag,[i,j])
        flag = -flag


    if debug == 60:
        return 0




    if WinColor(t_node)==black:
        return 1
    else:
        return -1

def IfValid(node, color, x, y):
    if node.data[x][y] != 0:
        return -1
    if x > 0:
        if node.data[x - 1][y] == -color:
            i = x - 1
            while i >= 0:
                if node.data[i][y] == 0:
                    break
                if node.data[i][y] == color:
                    return 1
                i = i - 1
        i = x - 1
        if y > 0:
            j = y - 1
            if node.data[x][j] == -color:
                while j >= 0:
                    if node.data[x][j] == 0:
                        break
                    if node.data[x][j] == color:
                        return 1
                    j = j - 1
            j = y - 1
            if node.data[i][j] == -color:
                while i >= 0 and j >= 0:
                    if node.data[i][j] == 0:
                        break
                    if node.data[i][j] == color:
                        return 1
                    j = j - 1
                    i = i - 1
        if y < 7:
            j = y + 1
            i = x - 1
            if node.data[x][j] == -color:
                while j <= 7:
                    if node.data[x][j] == 0:
                        break
                    if node.data[x][j] == color:
                        return 1
                    j = j + 1
            j = y + 1
            if node.data[i][j] == -color:
                while i >= 0 and j <= 7:
                    if node.data[i][j] == 0:
                        break
                    if node.data[i][j] == color:
                        return 1
                    j = j + 1
                    i = i - 1
    if x < 7:
        if node.data[x + 1][y] == -color:
            i = x + 1
            while i <= 7:
                if node.data[i][y] == 0:
                    break
                if node.data[i][y] == color:
                    return 1
                i = i + 1
        i = x + 1
        if y > 0:
            j = y - 1
            if node.data[x][j] == -color:
                while j >= 0:
                    if node.data[x][j] == 0:
                        break
                    if node.data[x][j] == color:
                        return 1
                    j = j - 1
            j = y - 1
            if node.data[i][j] == -color:
                while i <= 7 and j >= 0:
                    if node.data[i][j] == 0:
                        break
                    if node.data[i][j] == color:
                        return 1
                    j = j - 1
                    i = i + 1
        if y < 7:
            j = y + 1
            i = x + 1
            if node.data[x][j] == -color:
                while j <= 7:
                    if node.data[x][j] == 0:
                        break
                    if node.data[x][j] == color:
                        return 1
                    j = j + 1
            j = y + 1
            if node.data[i][j] == -color:
                while i <= 7 and j <= 7:
                    if node.data[i][j] == 0:
                        break
                    if node.data[i][j] == color:
                        return 1
                    j = j + 1
                    i = i + 1
    return -1

def WinColor(node):  # 计算出胜利的颜色
    b = 0;
    w = 0;
    for i in range(0, 8):
        for j in range(0, 8):
            if node.data[i][j] == black:
                b += 1
            if node.data[i][j] == white:
                w += 1
    if b > w:
        return black
    else:
        return white

def If_go(node, flag):  # 寻找下子位置
    for i in range(0, 8):
        for j in range(0, 8):
            if node.data[i][j] == flag:  # 横向是否有下子位置
                if i > 1 and node.data[i - 1][j] == -flag:
                    for k in range(i - 2, -1, -1):
                        if node.data[k][j] == 0:
                            node.data[k][j] = occ  # 如果当前位置已经被占有了
                            x_pos = k
                            y_pos = j
                            return [x_pos, y_pos]
                        if node.data[k][j] != -flag:
                            break
                if i < 6 and node.data[i + 1][j] == -flag:  # 横向是否有下子位置
                    for k in range(i + 2, 8, 1):
                        if node.data[k][j] == 0:
                            node.data[k][j] = occ
                            x_pos = k
                            y_pos = j
                            return [x_pos, y_pos]
                        if node.data[k][j] != -flag:
                            break
                if j > 1 and node.data[i][j - 1] == -flag:  # 竖向是否有下子位置
                    for k in range(j - 2, -1, -1):
                        if node.data[i][k] == 0:
                            node.data[i][k] = occ
                            x_pos = i
                            y_pos = k
                            return [x_pos, y_pos]
                        if node.data[i][k] != -flag:
                            break
                if j < 6 and node.data[i][j + 1] == -flag:  # 竖向是否有下子位置
                    for k in range(j + 2, 8, 1):
                        if node.data[i][k] == 0:
                            node.data[i][k] = occ
                            x_pos = i
                            y_pos = k
                            return [x_pos, y_pos]
                        if node.data[i][k] != -flag:
                            break
                if i > 1 and j > 1 and node.data[i - 1][j - 1] == -flag:  # 斜向是否有下子位置
                    for k in range(2, min(i, j) + 1, 1):
                        if node.data[i - k][j - k] == 0:
                            node.data[i - k][j - k] = occ
                            x_pos = i - k
                            y_pos = j - k
                            return [x_pos, y_pos]
                        if node.data[i - k][j - k] != -flag:
                            break
                if i > 1 and j < 6 and node.data[i - 1][j + 1] == -flag:  # 斜向是否有下子位置
                    for k in range(2, min(i, 7 - j) + 1, 1):
                        if node.data[i - k][j + k] == 0:
                            node.data[i - k][j + k] = occ
                            x_pos = i - k
                            y_pos = j + k
                            return [x_pos, y_pos]
                        if node.data[i - k][j + k] != -flag:
                            break
                if i < 6 and j > 1 and node.data[i + 1][j - 1] == -flag:  # 斜向是否有下子位置
                    for k in range(2, min(7 - i, j) + 1, 1):
                        if node.data[i + k][j - k] == 0:
                            node.data[i + k][j - k] = occ
                            x_pos = i + k
                            y_pos = j - k
                            return [x_pos, y_pos]
                        if node.data[i + k][j - k] != -flag:
                            break
                if i < 6 and j < 6 and node.data[i + 1][j + 1] == -flag:  # 斜向是否有下子位置
                    for k in range(2, min(7 - i, 7 - j) + 1, 1):
                        if node.data[i + k][j + k] == 0:
                            node.data[i + k][j + k] = occ
                            x_pos = i + k
                            y_pos = j + k
                            return [x_pos, y_pos]
                        if node.data[i + k][j + k] != -flag:
                            break
    return [-1, -1]

def If_Win(node):  # 游戏是否结束
    for i in range(0, 8):
        for j in range(0, 8):
            if node.data[i][j] == 0:
                return False
    return True

def BackUp(node, val):  # 回溯计算value
    while node != None:
        node.times += 1
        node.total_value += val
        node = node.getparent()

def Replace(node, flag, position):  # 翻转棋
    i = position[0]
    j = position[1]
    if i > 1 and node.data[i - 1][j] == -flag:  # 横向翻转
        for k in range(i - 2, 0, -1):
            if node.data[k][j] == flag:
                for m in range(k, i):
                    node.data[m][j] = flag
                break
            if node.data[k][j] == 0:
                break
    if i < 6 and node.data[i + 1][j] == -flag:  # 横向翻转
        for k in range(i + 2, 8, 1):
            if node.data[k][j] == flag:
                for m in range(i, k):
                    node.data[m][j] = flag
                break
            if node.data[k][j] == 0:
                break
    if j > 1 and node.data[i][j - 1] == -flag:  # 竖向翻转
        for k in range(j - 2, 0, -1):
            if node.data[i][k] == flag:
                for m in range(k, j):
                    node.data[i][m] = flag
                break
            if node.data[i][k] == 0:
                break
    if j < 6 and node.data[i][j + 1] == -flag:  # 竖向翻转
        for k in range(j + 2, 8, 1):
            if node.data[i][k] == flag:
                for m in range(j + 1, k):
                    node.data[i][m] = flag
                break
            if node.data[i][k] == 0:
                break
    if i > 1 and j > 1 and node.data[i - 1][j - 1] == -flag:  # 斜向翻转
        for k in range(2, min(i, j) + 1, 1):
            if node.data[i - k][j - k] == flag:
                for m in range(1, k, 1):
                    node.data[i - m][j - m] = flag
                break
            if node.data[i - k][j - k] == 0:
                break
    if i > 1 and j < 6 and node.data[i - 1][j + 1] == -flag:  # 斜向翻转
        for k in range(2, min(i, 7 - j) + 1, 1):
            if node.data[i - k][j + k] == flag:
                for m in range(1, k, 1):
                    node.data[i - m][j + m] = flag
                break
            if node.data[i - k][j + k] == 0:
                break
    if i < 6 and j > 1 and node.data[i + 1][j - 1] == -flag:  # 斜向翻转
        for k in range(2, min(7 - i, j) + 1, 1):
            if node.data[i + k][j - k] == flag:
                for m in range(1, k, 1):
                    node.data[i + m][j - m] = flag
                break
            if node.data[i + k][j - k] == 0:
                break
    if i < 6 and j < 6 and node.data[i + 1][j + 1] == -flag:  # 斜向翻转
        for k in range(2, min(7 - i, 7 - j) + 1, 1):
            if node.data[i + k][j + k] == flag:
                for m in range(1, k, 1):
                    node.data[i + m][j + m] = flag
                break
            if node.data[i + k][j + k] == 0:
                break

def trans(m):  # 转置矩阵
    a = [[] for i in m[0]]
    for i in m:
        for j in range(len(i)):
            a[j].append(i[j])
    return a

class RandomEngine(Engine):
    """ Game engine that plays completely randomly. """



    def get_move(self, board, color, movenum, time_me, time_oppo):  # 得到步数

        chess = board.pieces
        now = color
        chessboard = copy.deepcopy(chess)
        root = Node(chessboard)
        time1 = time.time()
        flag = now
        while (time.time() - time1) < 5:
            tmp = TreePolicy(root, flag)  # 选择
            if tmp != root and tmp != None:
                val = DefaultPolicy(tmp, flag)  # 模拟
                BackUp(tmp, val)  # 回溯
            else:
                break
        pos = copy.deepcopy(BestChild(root, 0).position)
        #x = pos[0]
        #pos[0] = pos[1]
        #pos[1] = x
        print BestChild(root, 0).data
        print color




        result=tuple(pos)




        return result

engine = RandomEngine
