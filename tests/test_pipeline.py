#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright 2017 Eddie Antonio Santos <easantos@ualberta.ca>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from sensibility.token_utils import Location, Position
from sensibility.pipeline import PythonPipeline
pipeline = PythonPipeline()


source = r'''#!/usr/bin/env python
# -*- coding: utf-8 -*-

print("Hello, world!")
'''


def test_works_on_source():
    tokens = list(pipeline.execute(source))
    assert len(tokens) == 5
    assert tokens == [
        'identifier', '(', '"string"', ')', 'NEWLINE'
    ]
    # Assert we can stringify it and convert it back?


class LocationFactory:
    """
    Creates locations, incrementally.
    """
    def __init__(self, start: Position) -> None:
        self.current = start

    def point(self) -> Location:
        return Location(start=self.current, end=self.current)

    def across(self, width: int) -> Location:
        start = self.current
        self.current = Position(line=start.line, column=start.column + width)
        return Location(start=start, end=self.current)

    def single(self):
        return self.across(1)

    def newline(self):
        return self.single()


def test_returns_locations():
    tokens = list(pipeline.execute_with_locations(source))
    assert len(tokens) == 5
    loc = LocationFactory(Position(line=4, column=0))
    assert tokens == [
        (loc.across(len("print")), 'identifier'),
        (loc.single(), '('),
        (loc.across(len('"Hello, World!"')), '"string"'),
        (loc.single(), ')'),
        (loc.newline(), 'NEWLINE')
    ]
