*** Settings ***

Library  test_ha.py   WITH NAME  test_ha

Test Setup    test_ha.HA.setUpClass

Test Teardown    test_ha.HA.tearDownClass

Force Tags     smoke_test  

Default Tags     P1

Library  test_ha.HA   WITH NAME  HA



*** Test Cases ***

cases.ha.test_ha.HA.test_ha_1
  [Tags]      
  [Setup]     HA.setUp
  [Teardown]  HA.tearDown

  HA.test_ha_1
