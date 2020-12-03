#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@file  : __init__.py.py
@Time  : 2020/12/3 14:43
@Author: Tao.Xu
@Email : tao.xu2008@outlook.com
"""

import os
import sys
from pyrobot.core import report_han, convert_to_rf, run_rf, clear_robot_file

# print(sys.path)
print(sys.executable)

if sys.version_info.major != 3:
    print("Just support Python 3+")
    exit()


def main():

    # 运行结果存入字典
    result = {}

    # 只清除所有robot用例文件
    if '--delrf' in sys.argv:
        clear_robot_file()
        exit(0)

    # 只转化Python用例为robot framework格式用例
    if '--torf' in sys.argv:
        convert_to_rf()
        exit(0)

    # 只运行测试
    if '--runrf' in sys.argv:
        run_rf()
        exit(0)        

    # 只汉化测试报告
    if '--hanrf' in sys.argv:
        report_han()
        exit(0)

    # 所有步骤都执行
    convert_to_rf()

    ret = run_rf()
    print(f'-------- RF execute result code: {ret} --------')
    result['run_robot'] = ret

    # 如果运行成功，执行汉化
    if ret < 5:  # 0 success, 1 faiure, 252 no matches found
        report_han()
        os.system('log.html')

    return result


if __name__ == '__main__':
    result = main()
