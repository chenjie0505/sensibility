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

import warnings
from typing import Sequence, Sized, Optional

from .corpus import Corpus
from .edit import Edit, Insertion, Deletion, Substitution
from .source_vector import SourceVector
from .lexical_analysis import Token
from .vectors import Vectors


class SourceFile(Sized):
    """
    A source file from the corpus. Easy access to both the token sequence, and
    the source tokens themselves.
    """
    corpus: Optional[Corpus] = None
    vectors: Optional[Vectors] = None

    __slots__ = ('file_hash', '_token_vector', '_source_tokens')

    def __init__(self, file_hash: str) -> None:
        self.file_hash = file_hash
        self._token_vector: Optional[SourceVector] = None
        self._source_tokens: Optional[Sequence[Token]] = None

    def __repr__(self):
        clsname = type(self).__name__
        return f"{clsname}({self.file_hash!r})"

    def __len__(self):
        return len(self.vector)

    @property
    def vector(self) -> SourceVector:
        """
        A vector representation of the file composed of vocabulary indicies.
        """
        # We already have it stored!
        if self._token_vector is not None:
            return self._token_vector

        if self.vectors is None:
            raise Exception('forgot to assign SourceFile.vectors')
        # Fetch the vector.
        _, tokens = self.vectors[self.file_hash]
        self._token_vector = SourceVector(tokens)

        # Sanity check: the vector and source file length should be the same.
        if self._source_tokens is not None:
            assert len(self.vector) == len(self.source_tokens)

        return self._token_vector

    @property
    def source_tokens(self) -> Sequence[Token]:
        """
        Original, parsed tokens, with position information (line and column).
        """
        warnings.warn('This method assumes JavaScript code', DeprecationWarning)
        from .tokenize_js import tokenize
        # We already have it stored!
        if self._source_tokens is not None:
            return self._source_tokens

        if self.corpus is None:
            raise Exception('forgot to assign SourceFile.corpus')
        # Fetch the source tokens.
        source = self.corpus.get_source(self.file_hash)
        self._source_tokens = tokenize(source.decode('UTF-8'))

        # Sanity check: the vector and source file length should be the same.
        if self._token_vector is not None:
            assert len(self.vector) == len(self.source_tokens)

        return self._source_tokens

    # TODO: TEST!
    @property
    def sloc(self):
        """
        Source lines of code, or how many lines of code there are.
        """
        last_token = self.source_tokens[-1]
        return last_token.line

    # TODO: TEST!
    # XXX: THIS CAN ONLY WORK WITH ONE MUTATION PER FILE.
    # TODO: Replace this ENTIRELY with a vector of line numbers.
    def line_of_index(self, index: int, edit: Edit=None) -> int:
        """
        Finds the line number of the token at the given index.
        If given a mutation, assumes the index belongs to the token stream
        AFTER mutation has been applied. That is, it's an index into in the
        file after mutation.  However, self MUST be the file PRIOR to
        mutation!
        """
        if edit is None:
            # The line is constant if no edit was applied
            return self.source_tokens[index].line
        elif isinstance(edit, Insertion):
            assert len(self.vector + edit) == len(self) + 1
            fixed_index = index - 1 if index > edit.index else index
            return self.source_tokens[fixed_index].line
        elif isinstance(edit, Deletion):
            assert len(self.vector + edit) == len(self) - 1
            fixed_index = index + 1 if index >= edit.index else index
            return self.source_tokens[fixed_index].line
        elif isinstance(edit, Substitution):
            assert len(self) == len(self.vector + edit)
            # The line is constant if the substitution edit is applied (no
            # change in index).
            return self.source_tokens[index].line
        else:
            raise NotImplementedError
