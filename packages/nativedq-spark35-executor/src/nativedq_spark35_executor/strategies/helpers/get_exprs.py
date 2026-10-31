from typing import List

from nativedq.definitions.dq_test import DQTest


def get_expr(test:DQTest):
    call = test()
    fn = call.func_callable
    parameters = {
        p.name: p.value
        for p in call.parameters
    }
    return fn(**parameters)


def get_exprs(tests:List[DQTest]):
    return [get_expr(test) for test in tests]