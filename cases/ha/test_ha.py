#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@file  : test_ha.py
@Time  : 2020/12/4 9:53
@Author: Tao.Xu
@Email : tao.xu2008@outlook.com
"""

import random
from pyrobot.case import RFTestCase


def fun():
    pass


class HA(RFTestCase):
    """HA test cases"""
    default_tags = ['P1']
    force_tags = ['smoke_test']

    @staticmethod
    def test_ha_1():
        """HA test case 1"""
        print("ttttttttttttt")
        assert random.randint(1, 8) > 0


if __name__ == '__main__':
    import unittest
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(HA))
    print(suite)
    print(suite._tests[0])
    print(suite._tests[0].id())
    print(suite._tests[0].tags)
