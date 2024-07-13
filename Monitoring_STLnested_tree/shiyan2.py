import copy
import matplotlib.pyplot as plt
import numpy as np
import time

# from STLnested_tool import Phi
# from STLnested_tool import Probability_Phi
# from STLnested_tool import Probability
from STLnested_tree import Phi


#  给两个列表集合取交集，考虑R以及\运算
def jiao(region1, region2):
    # 用来给两个集合取交集，考虑全集R，R的存法是region = [['R']]
    if region1[0] == 'R':
        region = region2
    elif region2[0] == 'R':
        region = region1
    else:  # 这种情况是两个都不是R，正常取交集即可
        if region1[0] == 'not':
            if region2[0] == 'not':
                region = ['not', list(set(region1[1]) | set(region2[1]))]
            else:
                region = [list(set(region2[0]) - set(region1[1]))]
        elif region2[0] == 'not':  # 这时候region1肯定不是not了
            region = [list(set(region1[0]) - set(region2[1]))]
        else:  # 俩都不是not不是R，正常取交集
            # print(region1)
            # print(region2)
            region = [list(set(region1[0]) & set(region2[0]))]
    return region

#  给两个列表取并集，考虑R以及\运算
def bing(region1, region2):
    # 用来给两个集合取并集，考虑全集R，R的存法是region = ['R'] 存了一个字符R
    if region1[0] == 'R':
        region = region1
    elif region2[0] == 'R':
        region = region2
    else:  # 这种情况是两个都不是R，正常取并集即可
        if region1[0] == 'not':
            if region2[0] == 'not':  # 都是not
                region = ['not', list(set(region1[1]) & set(region2[1]))]
            else:  # 1是not，2不是
                region = ['not', list(set(region1[1]) - set(region2[0]))]
        elif region2[0] == 'not':  # 这时候region1肯定不是not了
            region = [list(set(region2[1]) - set(region1[0]))]
        else:  # 俩都不是not不是R，正常取并集
            region = [list(set(region1[0]) | set(region2[0]))]
    return region

class Feasible_Set():
    # 用来存储X_k^I
    def __init__(self, k, probability_phi, X):
        self.k = k
        self.I = probability_phi
        self.X = X

    # 重写print
    def __repr__(self):
        prt = f"{self.I.P_list}"
        return prt


def fanwei(low, high, left, right):
    # 将连续的范围转换成离散的取值列表，目前的精度为0.1
    x = round(low,1)
    y = round(left,1)
    list = []
    while(x <= high):
        y = round(left, 1)
        while(y<=right):
            list.append((x, y))
            y = y + 0.1
            y = round(y, 1)
        x = x + 0.1
        x = round(x, 1)
    return list

def fanwei_tiqu(fanwei):
    # 把一大堆散点表示的范围提取出其中的整数来
    if fanwei == 'R':
        return 'R'
    fanwei_zhengshu = []
    for point in fanwei:
        if point[0]%1 == 0 and point[1]%1 == 0:
            fanwei_zhengshu.append(point)
    return fanwei_zhengshu

def one_step_set_backward1(fanwei_k1):
    x_list = []
    y_hl_list = []  # [[min,max],[min,max],...,[min,max]]
    for i in range(len(fanwei_k1)):
        if fanwei_k1[i][0] not in x_list:
            x_list.append(fanwei_k1[i][0])
            y_hl_list.append([fanwei_k1[i][1], fanwei_k1[i][1]])
        else:
            x_index = x_list.index(fanwei_k1[i][0])
            if fanwei_k1[i][1] > y_hl_list[x_index][1]:
                y_hl_list[x_index][1] = fanwei_k1[i][1]
            elif fanwei_k1[i][1] < y_hl_list[x_index][0]:
                y_hl_list[x_index][0] = fanwei_k1[i][1]
    fanwei_k = fanwei_k1.copy()
    for i in range(len(x_list)):
        x = x_list[i]
        for j in range(1,11):
            y1 = y_hl_list[i][0] - 0.1 * j
            y2 = y_hl_list[i][1] + 0.1 * j
            fanwei_k.append((x, y1))
            fanwei_k.append((x, y2))
    left = min(x_list)
    left_index = x_list.index(left)
    left_low = y_hl_list[left_index][0]
    left_high = y_hl_list[left_index][1]
    right = max(x_list)
    right_index = x_list.index(right)
    right_low = y_hl_list[right_index][0]
    right_high = y_hl_list[right_index][1]
    for i in range(1,11):
        x_left = left - i*0.1
        x_right = right + i*0.1
        for j in range(1,11):
            fanwei_k.append((x_left, left_low - j*0.1))
            fanwei_k.append((x_left, left_high + j*0.1))
            fanwei_k.append((x_right, right_low - j*0.1))
            fanwei_k.append((x_right, right_high + j*0.1))
        for j in range(int((left_high-left_low)/0.1+1)):
            fanwei_k.append((x_left, left_low+j*0.1))
        for j in range(int((right_high-right_low)/0.1+1)):
            fanwei_k.append((x_right, right_low+j*0.1))
    return [fanwei_k]

def one_step_set_backward(fanwei_k1):
    fanwei_k = fanwei_k1.copy()
    for i in range(len(fanwei_k1)):
        point = fanwei_k1[i]
        fanwei_this = []
        for dx in range(-10,11):
            for dy in range(-10,11):
                x = point[0]+dx*0.1
                y = point[1]+0.1*dy
                x = round(x, 1)
                y = round(y, 1)
                fanwei_this.append((x, y))
        fanwei_k = bing([fanwei_k], [fanwei_this])[0]

    return [fanwei_k]

def feasible_set(task):
    flag = 0
    end = task.effective_horizon()[1]
    feasible_set_list = []
    for i in range(end+2):
        feasible_set_list += [[]]
    I_every_k = task.potential_set()
    I_every_k_phi = []
    for i in range(end+2):
        I_every_k_phi.append([])
    for i in range(end+2):
        for I_k in I_every_k[i]:
            p_phi = Probability_Phi(None, None, I_k)
            I_every_k_phi[i] += [p_phi]
            # if p_phi.sat == False:
            #     I_every_k_phi[i] += [p_phi]
    print(I_every_k_phi)
    # print(I_every_k[end+1])
    for I_T1 in I_every_k_phi[end+1]:
        # print(I_T1)
        feasible_set_list[end+1] += [Feasible_Set(end+1, I_T1, ['R'])]
    k = end
    while(k>=0):
        print(k)
        print(I_every_k_phi[k])
        for I_k in I_every_k_phi[k]:
            # 已经T了就别算了，反正是R
            if I_k.sat == True:
                # 由于已经为True的I_k在这里会被直接跳过，因此在k-1时该I_k的前置集无法在feasible_set_list[k]里找到该I_k，从而也无法确定其
                # 的one_step_set_backward应该是多少，但又不想徒增feasible_set_list[k]的元素数，所以在下边找I_k的时候做了优化
                # continue
                # feasible_set_list[k] += [Feasible_Set(I_k.k, I_k, ['R'])]
                continue
            # 算某个I的X_k_I，需要算其所有后继集
            X_k_I_list = []
            linshi_list = []
            for I_k1 in I_every_k_phi[k+1]:
                # print(I_k)
                # print(I_k1)
                if task.is_successor_phi(I_k, I_k1):
                    consistent_region = task.consistent_region(I_k.P_list, I_k1.P_list)
                    # 与上边I_k为True时直接跳过在这里对应的优化，如果I_k1为True直接one_step_set = ['R']
                    # 如果feasible_set_list[k+1]里没有I_k1说明其可行集为[[]] 所以上一次没有加进去，那其one_step_set也是空集
                    if I_k1.sat != True:
                        # for X_k1 in feasible_set_list[k+1]:
                        for i_k1 in range(len(feasible_set_list[k + 1])):
                            X_k1 = feasible_set_list[k+1][i_k1]
                            # if X_k1.I.is_equal(I_k1):
                            if I_k1.is_equal(X_k1.I):
                                if X_k1.X != ['R']:
                                    # print(f"here{X_k1.X}")
                                    one_step_set = one_step_set_backward(X_k1.X[0])
                                else:
                                    one_step_set = ['R']
                                break
                            elif i_k1 == len(feasible_set_list[k + 1])-1:
                                print("因为我所以空集了")
                                one_step_set = [[]]
                    else:
                        one_step_set = ['R']
                    # if k == 0 or k == 1:  # 检查一下从1到0算的对不对
                    if True:
                        print(I_k.P_list)
                        print(I_k1.P_list)
                        print(f"交:{fanwei_tiqu(consistent_region[0])}和{fanwei_tiqu(one_step_set[0])}")
                        # print(f"结果是:{jiao(consistent_region, one_step_set)[0]}")
                        print(f"结果是:{fanwei_tiqu(jiao(consistent_region, one_step_set)[0])}")
                        print()
                    linshi_list += [jiao(consistent_region, one_step_set)]
            # print(f"所有后继集:{linshi_list}")
            X_k_I_list = linshi_list[0]
            for list1 in linshi_list:
                X_k_I_list = bing(X_k_I_list, list1)
            # print(X_k_I_list)
            # feasible_set_list[k] += [Feasible_Set(k, I_k, X_k_I_list)]
            if X_k_I_list != [[]]:
                feasible_set_list[k] += [Feasible_Set(k, I_k, X_k_I_list)]
        k = k-1
    return feasible_set_list

def feasible_set_tree(task):
    end = task.effective_horizon()[1]
    all_all_p = task.all_p()
    all_p = all_all_p[0]  # 这是含了True的情况的，用来当后继集下一时刻k+1的
    feasible_set_list = []
    for i in range(end+2):
        feasible_set_list += [[]]
    I_every_k = all_all_p[1]  # 这是不包含True情况的，只要None的，用来当k时刻的
    # print(I_every_k[end+1])
    for I_T1 in all_p[end+1]:
        # print(I_T1)
        feasible_set_list[end+1] += [Feasible_Set(end+1, I_T1, ['R'])]
    k = end
    while(k>=0):
        print(k)
        for I_k in I_every_k[k]:
            # 算某个I的X_k_I，需要算其所有后继集
            X_k_I_list = []
            linshi_list = []
            for I_k1 in all_p[k+1]:
                if task.is_successor(I_k, I_k1):
                    consistent_region = task.consistent_region(I_k, I_k1)
                    # 与上边I_k为True时直接跳过在这里对应的优化，如果I_k1为True直接one_step_set = ['R']
                    # 如果feasible_set_list[k+1]里没有I_k1说明其可行集为[[]] 所以上一次没有加进去，那其one_step_set也是空集
                    if task.tree.check(I_k1) != True:
                        # for X_k1 in feasible_set_list[k+1]:
                        for i_k1 in range(len(feasible_set_list[k + 1])):
                            X_k1 = feasible_set_list[k+1][i_k1]
                            # if X_k1.I.is_equal(I_k1):
                            if I_k1 == X_k1.I:
                                if X_k1.X != ['R']:
                                    # print(f"here{X_k1.X}")
                                    one_step_set = one_step_set_backward(X_k1.X[0])
                                else:
                                    one_step_set = ['R']
                                break
                            elif i_k1 == len(feasible_set_list[k + 1])-1:
                                # print("因为我所以空集了")
                                one_step_set = [[]]
                    else:
                        one_step_set = ['R']
                    # if k == 0 or k == 1:  # 检查一下从1到0算的对不对
                    # if True:
                    #     print(I_k)
                    #     print(I_k1)
                    #     print(f"交:{fanwei_tiqu(consistent_region[0])}和{fanwei_tiqu(one_step_set[0])}")
                    #     # print(f"结果是:{jiao(consistent_region, one_step_set)[0]}")
                    #     print(f"结果是:{fanwei_tiqu(jiao(consistent_region, one_step_set)[0])}")
                    #     print()
                    linshi_list += [jiao(consistent_region, one_step_set)]
            # print(f"所有后继集:{linshi_list}")
            X_k_I_list = linshi_list[0]
            for list1 in linshi_list:
                X_k_I_list = bing(X_k_I_list, list1)
            # print(X_k_I_list)
            # feasible_set_list[k] += [Feasible_Set(k, I_k, X_k_I_list)]
            if X_k_I_list != [[]]:
                feasible_set_list[k] += [Feasible_Set(k, I_k, X_k_I_list)]
        k = k-1
    return feasible_set_list

if __name__ == "__main__":
    # print(temperature_dynamic(20,0))
    # print(fanwei(10,15))
    # print(one_step_set_temperature(fanwei(10,15)))
    o2 = Phi([0], [1], ['G'], [fanwei(3, 4, 3, 4)])
    # print(o1)
    # task = Phi([0], [3], ['U'], [o2], [fanwei(-10, 10, -10, 10)])  # 简单版本
    task = Phi([0, 0], [5, 5], ['U', 'U'], [fanwei(1, 2, 1, 2), o2], [fanwei(-5, 10, -5, 10), fanwei(-5, 10, -5, 10)])  # 简单版本
    # task = Phi([0, 0], [2, 2], ['U', 'U'], [fanwei(1, 2, 1, 2), fanwei(3, 4, 3, 4)], [fanwei(-5, 10, -5, 10), fanwei(-5, 10, -5, 10)])  # 简单版本
    # task = Phi([0, 0], [2, 2], ['U', 'U'], [fanwei(1, 2, 1, 2), fanwei(3, 4, 3, 4)], [['R'], ['R']])  # 简单版本

    t1 = time.time()
    print(task)
    print(task.tree)
    print(task.effective_horizon())
    max_k = task.effective_horizon()[1]
    I_every_k = task.potential_set()
    # print(I_every_k)
    feasible_set_task = feasible_set_tree(task)
    for i in range(max_k+1):
        print("---------------------------------------------------------------")
        print(f"k={i}")
        print(f"{len(I_every_k[i])}, {len(feasible_set_task[i])}")
        # print(I_every_k[i])
        # print(feasible_set_task[i])
    print(time.time()-t1)

    fig = plt.figure()
    ax1 = fig.add_subplot(2, 4, 1)
    x = []
    y = []
    colors = []
    color_list = ['#f07c82', '#8abcd1', "green", "cyan", "orange", "purple", "beige", "magenta", "red"]
    color_index = 1  # 选上边哪个颜色
    alpha = 0.1  # 透明度
    # for j in range(max_k+1):
    #     X_k_this = feasible_set_task[j][0].X
    #     for num in range(1, len(feasible_set_task[j])):
    #         X_k_this = bing(X_k_this, feasible_set_task[j][num].X)
    #     for i in range(len(X_k_this[0])):
    #         x.append(X_k_this[0][i][0])
    #         y.append(X_k_this[0][i][1])
    #         colors.append(color_list[j])
    k = 0
    X_k_this = feasible_set_task[k][0].X
    for num in range(1, len(feasible_set_task[k])):
        X_k_this = bing(X_k_this, feasible_set_task[k][num].X)
    for i in range(len(X_k_this[0])):
        x.append(X_k_this[0][i][0])
        y.append(X_k_this[0][i][1])
        colors.append(color_list[1])
    x = np.array(x)
    y = np.array(y)
    plt.scatter(x, y, marker='s', s=10, alpha=alpha, c=colors)
    plt.xlabel('k=0')

    ax2 = fig.add_subplot(2, 4, 2)
    x = []
    y = []
    colors = []
    k = 1
    X_k_this = feasible_set_task[k][0].X
    for num in range(1, len(feasible_set_task[k])):
        X_k_this = bing(X_k_this, feasible_set_task[k][num].X)
    for i in range(len(X_k_this[0])):
        x.append(X_k_this[0][i][0])
        y.append(X_k_this[0][i][1])
        colors.append(color_list[1])
    x = np.array(x)
    y = np.array(y)
    plt.scatter(x, y, marker='s', s=10, alpha=alpha, c=colors)
    plt.xlabel('k=1')

    ax3 = fig.add_subplot(2, 4, 3)
    x = []
    y = []
    colors = []
    k = 2
    X_k_this = feasible_set_task[k][0].X
    for num in range(1, len(feasible_set_task[k])):
        X_k_this = bing(X_k_this, feasible_set_task[k][num].X)
    for i in range(len(X_k_this[0])):
        x.append(X_k_this[0][i][0])
        y.append(X_k_this[0][i][1])
        colors.append(color_list[1])
    x = np.array(x)
    y = np.array(y)
    plt.scatter(x, y, marker='s', s=10, alpha=alpha, c=colors)
    plt.xlabel('k=2')

    ax4 = fig.add_subplot(2, 4, 4)
    x = []
    y = []
    colors = []
    k = 3
    X_k_this = feasible_set_task[k][0].X
    for num in range(1, len(feasible_set_task[k])):
        X_k_this = bing(X_k_this, feasible_set_task[k][num].X)
    for i in range(len(X_k_this[0])):
        x.append(X_k_this[0][i][0])
        y.append(X_k_this[0][i][1])
        colors.append(color_list[1])
    x = np.array(x)
    y = np.array(y)
    plt.scatter(x, y, marker='s', s=10, alpha=alpha, c=colors)
    plt.xlabel('k=3')

    ax5 = fig.add_subplot(2, 4, 5)
    x = []
    y = []
    colors = []
    k = 4
    X_k_this = feasible_set_task[k][0].X
    for num in range(1, len(feasible_set_task[k])):
        X_k_this = bing(X_k_this, feasible_set_task[k][num].X)
    for i in range(len(X_k_this[0])):
        x.append(X_k_this[0][i][0])
        y.append(X_k_this[0][i][1])
        colors.append(color_list[1])
    x = np.array(x)
    y = np.array(y)
    plt.scatter(x, y, marker='s', s=10, alpha=alpha, c=colors)
    plt.xlabel('k=4')

    ax6 = fig.add_subplot(2, 4, 6)
    x = []
    y = []
    colors = []
    k = 5
    X_k_this = feasible_set_task[k][0].X
    for num in range(1, len(feasible_set_task[k])):
        X_k_this = bing(X_k_this, feasible_set_task[k][num].X)
    for i in range(len(X_k_this[0])):
        x.append(X_k_this[0][i][0])
        y.append(X_k_this[0][i][1])
        colors.append(color_list[1])
    x = np.array(x)
    y = np.array(y)
    plt.scatter(x, y, marker='s', s=10, alpha=alpha, c=colors)
    plt.xlabel('k=5')

    ax7 = fig.add_subplot(2, 4, 7)
    x = []
    y = []
    colors = []
    k = 6
    X_k_this = feasible_set_task[k][0].X
    for num in range(1, len(feasible_set_task[k])):
        X_k_this = bing(X_k_this, feasible_set_task[k][num].X)
    for i in range(len(X_k_this[0])):
        x.append(X_k_this[0][i][0])
        y.append(X_k_this[0][i][1])
        colors.append(color_list[1])
    x = np.array(x)
    y = np.array(y)
    plt.scatter(x, y, marker='s', s=10, alpha=alpha, c=colors)
    plt.xlabel('k=6')

    # ax8 = fig.add_subplot(2, 4, 8)
    # x = []
    # y = []
    # colors = []
    # k = 6
    # X_k_this = feasible_set_task[k][0].X
    # for num in range(1, len(feasible_set_task[k])):
    #     X_k_this = bing(X_k_this, feasible_set_task[k][num].X)
    # for i in range(len(X_k_this[0])):
    #     x.append(X_k_this[0][i][0])
    #     y.append(X_k_this[0][i][1])
    #     colors.append(color_list[color_index])
    # # for i in range(len(X_k_this[0])):
    # #     x.append(X_k_this[0][i][0])
    # #     y.append(X_k_this[0][i][1])
    # #     colors.append(color_list[2])
    # x = np.array(x)
    # y = np.array(y)
    # plt.scatter(x, y, marker='s', s=10, alpha=alpha, c=colors)

    # ----------------------------------------------------------------------------------------------------------

    rect = plt.Rectangle((1, 1), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax1.add_patch(rect)
    rect = plt.Rectangle((3, 3), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax1.add_patch(rect)
    ax1.text(1.55, 1.2, '1', fontsize=8, color='black', ha='center')
    ax1.text(3.5, 3.2, '2', fontsize=8, color='black', ha='center')

    rect = plt.Rectangle((1, 1), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax2.add_patch(rect)
    rect = plt.Rectangle((3, 3), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax2.add_patch(rect)
    ax2.text(1.55, 1.2, '1', fontsize=8, color='black', ha='center')
    ax2.text(3.5, 3.2, '2', fontsize=8, color='black', ha='center')

    rect = plt.Rectangle((1, 1), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax3.add_patch(rect)
    rect = plt.Rectangle((3, 3), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax3.add_patch(rect)
    ax3.text(1.55, 1.2, '1', fontsize=8, color='black', ha='center')
    ax3.text(3.5, 3.2, '2', fontsize=8, color='black', ha='center')

    rect = plt.Rectangle((1, 1), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax4.add_patch(rect)
    rect = plt.Rectangle((3, 3), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax4.add_patch(rect)
    ax4.text(1.55, 1.2, '1', fontsize=8, color='black', ha='center')
    ax4.text(3.5, 3.2, '2', fontsize=8, color='black', ha='center')

    rect = plt.Rectangle((1, 1), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax5.add_patch(rect)
    rect = plt.Rectangle((3, 3), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax5.add_patch(rect)
    ax5.text(1.55, 1.2, '1', fontsize=8, color='black', ha='center')
    ax5.text(3.5, 3.2, '2', fontsize=8, color='black', ha='center')

    rect = plt.Rectangle((1, 1), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax6.add_patch(rect)
    rect = plt.Rectangle((3, 3), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax6.add_patch(rect)
    ax6.text(1.55, 1.2, '1', fontsize=8, color='black', ha='center')
    ax6.text(3.5, 3.2, '2', fontsize=8, color='black', ha='center')

    rect = plt.Rectangle((1, 1), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax7.add_patch(rect)
    rect = plt.Rectangle((3, 3), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    ax7.add_patch(rect)
    ax7.text(1.55, 1.2, '1', fontsize=8, color='black', ha='center')
    ax7.text(3.5, 3.2, '2', fontsize=8, color='black', ha='center')

    # rect = plt.Rectangle((1, 1), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    # ax8.add_patch(rect)
    # rect = plt.Rectangle((3, 3), 1, 1, alpha=1, edgecolor='black', facecolor='none', linewidth=1)
    # ax8.add_patch(rect)
    # ax8.text(1.55, 1.2, '1', fontsize=8, color='black', ha='center')
    # ax8.text(3.5, 3.2, '2', fontsize=8, color='black', ha='center')

    ax1.set_xlim(-5, 10)
    ax1.set_ylim(-5, 10)
    ax2.set_xlim(-5, 10)
    ax2.set_ylim(-5, 10)
    ax3.set_xlim(-5, 10)
    ax3.set_ylim(-5, 10)
    ax4.set_xlim(-5, 10)
    ax4.set_ylim(-5, 10)
    ax5.set_xlim(-5, 10)
    ax5.set_ylim(-5, 10)
    ax6.set_xlim(-5, 10)
    ax6.set_ylim(-5, 10)
    ax7.set_xlim(-5, 10)
    ax7.set_ylim(-5, 10)
    # ax8.set_xlim(-5, 10)
    # ax8.set_ylim(-5, 10)
    plt.show()