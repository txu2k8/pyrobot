#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@file  : case.py
@Time  : 2020/12/3 16:33
@Author: Tao.Xu
@Email : tao.xu2008@outlook.com
"""

import unittest
from collections import defaultdict


class RFTestCase(unittest.TestCase):
    """
    A custom class inherit from unittest.TestCase, for robot
    """
    tc_loop = defaultdict(int)
    default_tags = ['P1']
    force_tags = ['smoke_test']

    def __init__(self, methodName='runTest', *args, **kwargs):
        super(RFTestCase, self).__init__(methodName)
        self.args = args
        self.kwargs = kwargs
        self.tags = []

    @staticmethod
    def parametrize(testcase_class, *args, **kwargs):
        """Return a suite of all test cases contained in testCaseClass"""
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_class)
        if not testnames and hasattr(testcase_class, 'runTest'):
            testnames = ['runTest']
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_class(name, *args, **kwargs))
        return suite

    def setUp(self):
        pass

    def tearDown(self):
        self.tc_loop[self.id()] += 1
        pass


if __name__ == '__main__':
    pass
