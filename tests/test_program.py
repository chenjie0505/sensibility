#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import io

from hypothesis import given  # type: ignore
from hypothesis.strategies import random_module  # type: ignore

from strategies import programs


def setup():
    # XXX: This is more or less hardcoded to work with JavaScript.
    from sensibility.language import language
    language.set_language('javascript')


@given(programs(), random_module())
def test_program_random(program, random):
    assert 0 <= program.random_token_index() < len(program)
    assert 0 <= program.random_insertion_point() <= len(program)


@given(programs())
def test_program_print(program):
    """
    Test that printing programs gives the proper amount of space-separated
    tokens.
    """
    with io.StringIO() as output:
        program.print(output)
        output_text = output.getvalue()
    assert len(program) == len(output_text.split())
