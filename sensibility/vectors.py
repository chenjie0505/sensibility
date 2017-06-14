#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright 2016, 2017 Eddie Antonio Santos <easantos@ualberta.ca>
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

"""
Manages a vector of files with fold assignments.
"""

import warnings
import sqlite3
from pathlib import Path
from typing import Union, Tuple, Sequence, Iterable

from .lexical_analysis import Lexeme
from .source_vector import SourceVector
from .vectorize_tokens import serialize_tokens
from .vocabulary import vocabulary


# Results are always the hash and the source vector.
Result = Tuple[str, SourceVector]


SCHEMA = """
pragma FOREIGN_KEYS = on;

CREATE TABLE IF NOT EXISTS vectorized_source(
    hash     TEXT PRIMARY KEY,
    array    BLOB NOT NULL,     -- the array, as a blob.
    n_tokens INTEGER NOT NULL   -- the amount of tokens, (excluding start/end)
);

CREATE TABLE IF NOT EXISTS fold_assignment(
    hash TEXT PRIMARY KEY,
    fold INTEGER NOT NULL,  -- the fold assignment

    FOREIGN KEY (hash) REFERENCES vectorized_source(hash)
);
"""

# TODO: Remove responsibility of fold assignment from Vectors


class Vectors:
    """
    Represents a corpus with condensed tokens according to a vocabulary.

    Can get results by rowid (ONE-INDEXED!) or by file SHA 256 hash.

    >>> c = Vectors.connect_to(':memory:')
    >>> tokens = (Lexeme(value='var', name='Keyword'),)
    >>> c.insert('123abc', tokens)

    Accessing using the SHA-256:

    >>> file_hash, (tok_id,) = c['123abc']
    >>> tok_id
    90
    >>> file_hash
    '123abc'

    Accessing using one-indexed row ID:

    >>> file_hash, (tok_id,) = c[1]
    >>> file_hash
    '123abc'
    >>> tok_id
    90
    >>> c.min_index
    1
    >>> c.max_index
    1

    >>> tokens = (
    ...     Lexeme(value='var', name='Keyword'),
    ...     Lexeme(value='foo', name='Identifier')
    ... )
    >>> c.insert('foobar', tokens)
    >>> c.max_index
    2

    Files can also be assigned to folds. Initially there are no assignments:

    >>> list(c.hashes_in_fold(0))
    []

    One can an file hash to EXACTLY one fold.

    >>> c.add_to_fold('foobar', 0)
    >>> list(c.hashes_in_fold(0))
    ['foobar']
    >>> c.add_to_fold('foobar', 1)
    Traceback (most recent call last):
      ...
    sqlite3.IntegrityError: UNIQUE constraint failed: fold_assignment.hash
    >>> c.add_to_fold('123abc', 0)
    >>> list(c.hashes_in_fold(0))
    ['foobar', '123abc']

    The hash has to be in vectors first.

    >>> c.add_to_fold('does not exist', 0)
    Traceback (most recent call last):
      ...
    sqlite3.IntegrityError: FOREIGN KEY constraint failed

    We can count how many tokens are in a fold:
    >>> c.ntokens_in_fold(0)
    3
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        assert len(vocabulary) < 256
        warnings.warn("deprecated", DeprecationWarning)
        self.conn = conn
        self._maybe_instantiate_schema()

    def _maybe_instantiate_schema(self):
        # try querying the database
        try:
            self.conn.execute('''
                SELECT COUNT(*) FROM vectorized_source
            ''')
        except sqlite3.OperationalError:
            # Otherwise, we need to create the schema...
            with self.conn:
                self.conn.executescript(SCHEMA)

    def disconnect(self) -> None:
        self.conn.close()

    def get_result_by_hash(self, file_hash: str) -> Result:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT array FROM vectorized_source
            WHERE hash = ?
        """, (file_hash,))
        blob, = cur.fetchone()
        return file_hash, SourceVector.from_bytes(blob)

    def get_result_by_rowid(self, rowid: int) -> Result:
        assert isinstance(rowid, int)
        cur = self.conn.cursor()
        cur.execute("""
            SELECT hash, array FROM vectorized_source
            WHERE rowid = ?
        """, (rowid,))
        file_hash, blob = cur.fetchone()
        return file_hash, SourceVector.from_bytes(blob)

    @property
    def min_index(self) -> int:
        result, = self.conn.execute("""
            SELECT MIN(rowid) FROM vectorized_source
        """).fetchone()
        return result

    @property
    def max_index(self) -> int:
        result, = self.conn.execute("""
            SELECT MAX(rowid) FROM vectorized_source
        """).fetchone()
        return result

    def hashes_in_fold(self, fold_no: int) -> Iterable[str]:
        """
        Generate all hashes in the given fold number.
        """
        cur = self.conn.execute("""
            SELECT hash FROM fold_assignment WHERE fold = ?
        """, (fold_no,))
        yield from (result for result, in cur.fetchall())

    def files_in_fold(self, fold_no: int) -> Iterable[Result]:
        """
        Generated all hash, token pairs from the corpus.
        """
        for file_hash in self.hashes_in_fold(fold_no):
            yield self.get_result_by_hash(file_hash)

    def ntokens_in_fold(self, fold: int) -> int:
        assert fold in self.fold_ids
        result, = self.conn.execute(r'''
            SELECT SUM(n_tokens)
              FROM vectorized_source JOIN fold_assignment USING (hash)
             WHERE fold = :fold
         ''', dict(fold=fold)).fetchone()
        return result

    @property
    def unassigned_files(self) -> Iterable[str]:
        """
        Returns a list of all files that are not assigned to existing folds.
        """
        yield from (file_hash for (file_hash,) in self.conn.execute("""
            SELECT hash
            FROM vectorized_source
            WHERE hash NOT IN (
                SELECT hash
                FROM fold_assignment
            );
        """))

    def __getitem__(self, key: Union[str, int]) -> Result:
        if isinstance(key, str):
            return self.get_result_by_hash(key)
        else:
            return self.get_result_by_rowid(key)

    def insert(self, file_hash: str, tokens: Sequence[Lexeme]) -> None:
        """
        Insert tokens in the database of vectors.
        """
        byte_string = serialize_tokens(tokens).to_bytes()
        assert len(byte_string) == len(tokens)

        with self.conn:
            self.conn.execute("""
                INSERT INTO vectorized_source(hash, array, n_tokens)
                     VALUES (?, ?, ?)
             """, (file_hash, byte_string, len(tokens)))

    def add_to_fold(self, file_hash: str, fold_no: int) -> None:
        """
        Add a file hash to a fold.
        """
        with self.conn:
            self.conn.execute("""
                INSERT INTO fold_assignment(hash, fold) VALUES (?, ?)
             """, (file_hash, fold_no))

    @property
    def fold_ids(self) -> Sequence[int]:
        """
        A list of all current fold numbers.
        """
        cur = self.conn.execute("""
            SELECT DISTINCT fold
              FROM fold_assignment
        """)
        return [int(fold_id) for fold_id, in cur.fetchall()]

    @property
    def has_fold_assignments(self) -> bool:
        """
        Does this corpus have fold assignments?
        """
        return len(self.fold_ids) > 0

    def destroy_fold_assignments(self) -> None:
        """
        Deletes any current fold assignments.
        """
        with self.conn:
            self.conn.execute("DELETE FROM fold_assignment")

    @classmethod
    def connect_to(cls, filename: Union[str, Path]) -> 'Vectors':
        conn = sqlite3.connect(str(filename))
        return cls(conn)
