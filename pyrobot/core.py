#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@file  : __init__.py.py
@Time  : 2020/12/3 14:43
@Author: Tao.Xu
@Email : tao.xu2008@outlook.com
"""

import ast
import os
import sys
import shutil
import unittest

# CASE_DIR = r'cases'
REPORT_DIR = r"C:\workspace\pyrobot\report"
CASE_DIR = r"C:\workspace\pyrobot\cases\ha"
CASE_GEN_DIR = r'cases_gen'
LOG_LEVEL = 2

GEN_DIR = False

python_executable = sys.executable
if ' ' in sys.executable:
    python_executable = f'"{python_executable}"'

# pyrobot 特殊处理的参数
PYROBOT_ARGS = [
    '--genSepDir',  # 另外产生case dir
    '--torf',
    '--delrf',
    '--runrf',
    '--hanrf',
]


def myprint(level=2, *args, **kwargs):
    if level >= LOG_LEVEL:
        print(*args, **kwargs)


def clear_robot_file():
    print('清除所有robotframework格式用例')
    robot_files = []
    for (dirpath, dirnames, filenames) in os.walk(CASE_DIR):
        robot_files += [os.path.join(dirpath, fn) for fn in filenames if fn.endswith('.robot')]

    # 只能删除有同名py文件的
    for rf in robot_files:
        if os.path.exists(rf[:-5] + 'py'):
            os.remove(rf)

        # if rf == '__init__.robot':
        #     os.remove(rf)


class SuiteFileConvert:
    SUITE_TAGS = [
        'force_tags',
        'default_tags',
    ]

    SUITE_STS = [
        'suite_setup',
        'suite_teardown',
        'test_setup',
        'test_teardown',
    ]

    def __init__(self, pyfile):

        self.pyfile = pyfile

        # 构建suite对象
        self.suite = {

            'testcases': []
        }

    def handle(self):

        with open(self.pyfile, encoding='utf8') as pf:
            data = pf.read()

        # 解析 py case 代码
        tree = ast.parse(data, self.pyfile)

        for level1 in tree.body:

            # 全局变量定义
            if type(level1) == ast.Assign:
                target = level1.targets[0]

                # 如果没有id属性，那么可能是这样的 语句 GSTORE['key']= 1，跳过
                if not hasattr(target, 'id'):
                    continue

                name = target.id
                value = level1.value

                # 套件标签设置
                if name in self.SUITE_TAGS:
                    myprint(1, f'Assign: {name}')
                    if type(value) == ast.List:
                        self.suite[name] = [elt.s for elt in value.elts]
                    else:
                        print(f'标签 {name} 值一定要是list类型')

            # 全局函数定义
            if type(level1) == ast.FunctionDef:
                myprint(1, f'FunctionDef: {level1.name}')

                # 套件初始化
                if level1.name in self.SUITE_STS:
                    self.suite[level1.name] = True

            # 类定义，对应用例
            elif type(level1) == ast.ClassDef:
                self.addOneTestCase(level1)

        if self.pyfile.endswith('__st__.py'):
            return self.writeRobotInitFile()
        else:
            return self.writeRobotSuiteFile()

    def addOneTestCase(self, classNode):

        myprint(1, f'ClassDef: {classNode.name}')
        classname = classNode.name

        # 准备构建testcase，里面保存需要写入robot文件的信息即可
        testcase = {
            'classname': classname
        }

        for level2 in classNode.body:
            # 类静态属性定义
            if type(level2) == ast.Assign:
                target = level2.targets[0]
                value = level2.value

                # myprint(f'    staticAttr: {target.id}')

                # 简单赋值语句
                if type(target) == ast.Name:

                    # 赋值语句右边是字符串
                    # Python3.8      value 类型为 ast.Constant
                    # Python3.7 之前 value 类型为 ast.Str
                    if target.id == 'name' and type(value) in [ast.Str, ast.Constant]:
                        testcase['name'] = value.s
                        testcase['type'] = 'normalcase'

                    # 数据驱动的多个用例，格式如下
                    #     cases = [
                    #         ('登录 - 000031', 'user001','888888'),
                    #         ('登录 - 000032', 'user002',''),
                    #     ]

                    if target.id == 'cases' and type(value) == ast.List:
                        testcase['cases'] = ast.literal_eval(value)
                        testcase['type'] = 'multicase'

                    # 属性名 为 tags ，表示用例标签
                    if target.id == 'tags' and type(value) == ast.List:
                        testcase['tags'] = ast.literal_eval(value)

                    # 属性名 为 cid ，表示用例编号
                    if target.id == 'cid' and type(value) in [ast.Str, ast.Constant]:
                        testcase['cid'] = value.s


            # 类方法定义
            elif type(level2) == ast.FunctionDef:
                myprint(1, f'    MethodDef: {level2.name}')
                if level2.name == 'setup':
                    testcase['setup'] = True
                elif level2.name == 'teardown':
                    testcase['teardown'] = True
                elif level2.name == 'teststeps':
                    testcase['teststeps'] = True

        # '\u767d\u6708\u9ed1\u7fbd\u7248\u6743\u6240\u6709'
        self.suite['testcases'].append(testcase)

    # 写初始化文件对应的robot格式文件 __init__.robot
    def writeRobotInitFile(self):

        # ==============  写入 robot 文件   ===============

        fileDir = os.path.dirname(self.pyfile)

        if GEN_DIR:
            robotFile = CASE_GEN_DIR + os.path.join(fileDir[len(CASE_DIR):], '__init__.robot')
        else:
            robotFile = os.path.join(fileDir, '__init__.robot')

        moduleName = os.path.basename(self.pyfile)[:-3]

        settings_txt = self.handleSuiteSettings(moduleName)

        with open(robotFile, 'w', encoding='utf8') as rf:
            rf.write(settings_txt)

    # 写套件文件对应的robot格式文件
    def writeRobotSuiteFile(self):

        # pprint(self.suite,indent=4, width=40)

        # =============   有效性检查   ====================
        if not self.suite['testcases']:
            print('!! 没有定义测试用例 !!')
            return False

        effective_testcases = []
        for tc in self.suite['testcases']:
            if not ('name' in tc or 'cases' in tc):
                print(f'!! {tc["classname"]}没有 name 或者 cases 定义')
                continue

            if 'teststeps' not in tc:
                print(f'!! {tc["classname"]}没有 teststeps 定义')
                continue

            # 用例名加上编号作为后缀
            if 'cid' in tc:
                tc['name'] += f" ( {tc['cid']} )"

            effective_testcases.append(tc)

        # 一个有效 用例类定义都没有，返回
        if not effective_testcases:
            return

        # ==============  写入 robot 文件   ===============

        if GEN_DIR:
            robotFile = CASE_GEN_DIR + self.pyfile[len(CASE_DIR):-3] + '.robot'
        else:
            robotFile = self.pyfile[:-3] + '.robot'

        moduleName = os.path.basename(self.pyfile)[:-3]

        testcases_txt = ''

        settings_txt = self.handleSuiteSettings(moduleName)

        testcases_txt += '\n\n*** Test Cases ***'

        for tc in effective_testcases:
            classname = tc['classname']

            settings_txt += f'Library  {moduleName}.{classname}   WITH NAME  {classname}\n\n'

            # 单个用例
            if tc['type'] == 'normalcase':
                testcases_txt += f'\n\n{tc["name"]}\n'

                if 'tags' in tc:
                    tags = '   '.join(tc['tags'])
                    testcases_txt += f'  [Tags]      {tags}\n'
                if 'setup' in tc:
                    testcases_txt += f'  [Setup]     {classname}.setup\n'
                if 'teardown' in tc:
                    testcases_txt += f'  [Teardown]  {classname}.teardown\n'

                testcases_txt += f'\n  {classname}.teststeps\n'

            # 对应数据驱动的多个用例，示例格式如下
            # cases = [
            #         ('登录 - 000031', 'user001','888888'),
            #         ('登录 - 000032', 'user002',''),
            #     ]
            #
            #     def teststeps(self,index):
            #         case, username, password = self.cases[index]

            elif tc['type'] == 'multicase':
                for idx, case in enumerate(tc["cases"]):
                    casename = case[0]
                    testcases_txt += f'\n\n{casename}\n'

                    if 'tags' in tc:
                        tags = '   '.join(tc['tags'])
                        testcases_txt += f'  [Tags]      {tags}\n'
                    if 'setup' in tc:
                        testcases_txt += f'  [Setup]     {classname}.setup\n'
                    if 'teardown' in tc:
                        testcases_txt += f'  [Teardown]  {classname}.teardown\n'

                    testcases_txt += f'\n  {classname}.teststeps   ${{{idx}}}\n'

        with open(robotFile, 'w', encoding='utf8') as rf:
            rf.write(settings_txt)
            rf.write(testcases_txt)

    def handleSuiteSettings(self, moduleName):

        settings_txt = '''*** Settings ***\n\n'''

        # 如果是初始化文件，使用名字D 表示dir
        if moduleName == '__st__':
            NAME = 'D'
        # 如果是用例文件，使用名字F 表示 File
        else:
            NAME = 'F'

        settings_txt += f'Library  {moduleName}.py   WITH NAME  {NAME}\n\n'

        if 'suite_setup' in self.suite:
            settings_txt += f'Suite Setup    {NAME}.suite_setup\n\n'

        if 'suite_teardown' in self.suite:
            settings_txt += f'Suite Teardown    {NAME}.suite_teardown\n\n'

        if 'test_setup' in self.suite:
            settings_txt += f'Test Setup    {NAME}.test_setup\n\n'

        if 'test_teardown' in self.suite:
            settings_txt += f'Test Teardown    {NAME}.test_teardown\n\n'

        if 'force_tags' in self.suite:
            tags = '   '.join(self.suite['force_tags'])
            settings_txt += f'Force Tags     {tags}  \n\n'

        if 'default_tags' in self.suite:
            tags = '   '.join(self.suite['default_tags'])
            settings_txt += f'Default Tags     {tags}\n\n'

        return settings_txt


# 汉化测试报告
def report_han():
    print('\n === 汉化测试报告 ===\n\n')

    shared = '''
    '#total-stats th:nth-of-type(1)>div' : '全局统计',
    '#total-stats th:nth-of-type(2)>div' : '总数',
    '#total-stats th:nth-of-type(3)>div' : '通过',
    '#total-stats th:nth-of-type(4)>div' : '失败',
    '#total-stats th:nth-of-type(5)>div' : '耗时',
    '#total-stats th:nth-of-type(6)>div' : '通过/失败比例', 
    
    
    '#tag-stats th:nth-of-type(1)>div' : '根据标签统计',
    '#tag-stats th:nth-of-type(2)>div' : '总数',
    '#tag-stats th:nth-of-type(3)>div' : '通过',
    '#tag-stats th:nth-of-type(4)>div' : '失败',
    '#tag-stats th:nth-of-type(5)>div' : '耗时',
    '#tag-stats th:nth-of-type(6)>div' : '通过/失败比例',    
    
    '#suite-stats th:nth-of-type(1)>div' : '根据套件统计',
    '#suite-stats th:nth-of-type(2)>div' : '总数',
    '#suite-stats th:nth-of-type(3)>div' : '通过',
    '#suite-stats th:nth-of-type(4)>div' : '失败',
    '#suite-stats th:nth-of-type(5)>div' : '耗时',
    '#suite-stats th:nth-of-type(6)>div' : '通过/失败比例',    
    
    '#statistics-container h2' : '统计信息',  
'''

    js_log_translate = '''\n\n
<script type="text/javascript">

var  translateTable = {  
    '#header h1' : '测试日志',
    '#report-or-log-link a' : '测试报告',
       
    '#total-stats tbody .row-0 span' : '关键用例',
    '#total-stats tbody .row-1 span' : '所有用例',
    
    %s
    
    '#statistics-container ~ h2' : '执行过程日志'
    
}

$(document).ready(function() {
    for (var exp in translateTable) {
        console.log(exp)
        document.querySelector(exp).innerHTML = translateTable[exp];
    };
    
});
</script>
''' % shared

    js_report_translate = '''\n\n
<script type="text/javascript">

var  translateTable = {
    '#header h1' : '测试报告',
    '#report-or-log-link a' : '执行日志',
    
    
    '#header ~ h2' : '汇总信息',
    '#header ~ table:nth-of-type(1) tr:nth-of-type(1)>th' : '测试结果',
    '#header ~ table:nth-of-type(1) tr:nth-of-type(2)>th' : '开始时间',
    '#header ~ table:nth-of-type(1) tr:nth-of-type(3)>th' : '结束时间',
    '#header ~ table:nth-of-type(1) tr:nth-of-type(4)>th' : '测试用时',
    '#header ~ table:nth-of-type(1) tr:nth-of-type(5)>th' : '执行日志',
    
    %s
    
    
    '#total-stats tbody .row-0 a' : '关键用例',
    '#total-stats tbody .row-1 a' : '所有用例',
    
    '#totals' : '详细信息',
    //'#detail-tabs li:nth-of-type(1) a' : '总计',
    //'#detail-tabs li:nth-of-type(2) a' : '标签',
    //'#detail-tabs li:nth-of-type(3) a' : '套件',
    //'#detail-tabs li:nth-of-type(4) a' : '搜索',
    
    
}


$(document).ready(function() {
    for (var exp in translateTable) {
    
        try{
            document.querySelector(exp).innerHTML = translateTable[exp];
        }
        catch(error) {
          console.error(exp);
          console.error(error);
          
        }
    };
    
});
</script>
''' % shared

    if os.path.exists('log.html'):
        with open('log.html', "a", encoding='utf8') as f:
            f.write(js_log_translate)
            print('汉化日志文件 log.html')
    else:
        print('！！日志文件 log.html')

    if os.path.exists('report.html'):
        with open('report.html', "a", encoding='utf8') as f:
            f.write(js_report_translate)
            print('汉化报告文件 report.html')
    else:
        print('！！报告文件 report.html 不存在')


def convert_to_rf():
    global GEN_DIR

    result = {}

    print('\n== 用例 Python格式 转化为 Robot 格式 ==\n')

    if '--genSepDir' in sys.argv:
        GEN_DIR = True

    # print(f'\n\n== 清理目录 {CASE_DIR} ==')
    clear_robot_file()

    # print('\n\n== 产生用例执行目录 cases_gen  ==')

    if GEN_DIR:
        if os.path.exists(CASE_GEN_DIR):
            shutil.rmtree(CASE_GEN_DIR)

        shutil.copytree(CASE_DIR, CASE_GEN_DIR)

    py_files = []

    for (dirpath, dirnames, filenames) in os.walk(CASE_DIR):
        py_files += [os.path.join(dirpath, fn) for fn in filenames if fn.endswith('.py')]

    for file in py_files:
        print(f'{file}...', end='')
        sc = SuiteFileConvert(file)
        ret = sc.handle()
        if ret:
            print('ok')


def run_rf():
    # 检查 robotfframework 有没有安装
    try:
        import robot.libraries.BuiltIn
    except:
        print('\nrobotframework 还没有安装...')
        ret = os.system(f'{python_executable} -m pip install robotframework')
        if ret != 0:
            print('安装 robotframework 失败！！！\n')
            exit(2)
        else:
            print('安装 robotframework 成功\n\n')

    print('\n\n== 执行测试用例 ==\n')

    # 先去掉 pyrobot 自己的参数 和 脚本名参数

    print(sys.argv)

    args_for_rf = [arg for arg in sys.argv if arg not in PYROBOT_ARGS][1:]

    args_for_rf = [f'"{arg}"' if ' ' in arg else arg for arg in args_for_rf]

    arg_str = ' '.join(args_for_rf)

    print(args_for_rf)

    if GEN_DIR:
        cmd = f'{python_executable} -m robot.run {arg_str}  {CASE_GEN_DIR}'
    else:
        cmd = f'{python_executable} -m robot.run {arg_str}  {CASE_DIR}'

    # cmd += f" -r {REPORT_DIR}\\report -l {REPORT_DIR}\\log -o {REPORT_DIR}\\output"
    print(cmd)
    ret = os.system(cmd)

    return ret


class Py2Robot(object):
    """Convert the python file to robot test"""

    def __init__(self, py_file, tc_class):
        self.py_file = py_file
        self.tc_class = tc_class
        self.module_name = os.path.basename(self.py_file)[:-3]
        self.settings_txt = ""
        self.testcases_txt = ""

    @property
    def suite(self):
        suite = unittest.TestSuite()
        loader = unittest.TestLoader()
        suite.addTests(loader.loadTestsFromTestCase(self.tc_class))
        return suite

    def handle_suite_settings(self):
        """
        handle the suite setting text
        :return:
        """
        self.settings_txt = '''*** Settings ***\n\n'''
        self.settings_txt += f'Library  {self.module_name}.py   WITH NAME  {self.module_name}\n\n'

        # Suite Setup/Teardown from __init__.py
        # settings_txt += f'Suite Setup    {module_name}.setUpClass\n\n'
        # settings_txt += f'Suite Teardown    {module_name}.tearDownClass\n\n'

        # Test Setup/Teardown from setUp/tearDown Class
        self.settings_txt += f'Test Setup    {self.module_name}.{self.tc_class.__name__}.setUpClass\n\n'
        self.settings_txt += f'Test Teardown    {self.module_name}.{self.tc_class.__name__}.tearDownClass\n\n'
        # Force Tags
        force_tags = '   '.join(self.tc_class.force_tags)
        self.settings_txt += f'Force Tags     {force_tags}  \n\n'
        # Default Tags
        default_tags = '   '.join(self.tc_class.default_tags)
        self.settings_txt += f'Default Tags     {default_tags}\n\n'

    def handle_test_cases(self):
        """
        handle test cases text
        :return:
        """
        self.testcases_txt = '\n\n*** Test Cases ***'

        for test in self.suite._tests:
            self.settings_txt += f'Library  {self.module_name}.{self.tc_class.__name__}   WITH NAME  {self.tc_class.__name__}\n\n'
            self.testcases_txt += f'\n\n{test.id()}\n'
            tags = '   '.join(test.tags)
            self.testcases_txt += f'  [Tags]      {tags}\n'
            self.testcases_txt += f'  [Setup]     {self.tc_class.__name__}.setUp\n'
            self.testcases_txt += f'  [Teardown]  {self.tc_class.__name__}.tearDown\n'
            self.testcases_txt += f'\n  {self.tc_class.__name__}.{test.id().split(".")[-1]}\n'

    def handle(self):
        self.handle_suite_settings()
        # print(self.settings_txt)
        self.handle_test_cases()
        # print(self.testcases_txt)

        robot_file = "{0}_{1}.robot".format(self.py_file[:-3], self.tc_class.__name__)
        with open(robot_file, 'w', encoding='utf8') as rf:
            rf.write(self.settings_txt)
            rf.write(self.testcases_txt)


if __name__ == '__main__':
    from cases.ha.test_ha import HA
    pr = Py2Robot(r"C:\workspace\pyrobot\cases\ha\test_ha.py", HA)
    pr.handle()
    run_rf()
