"""Literal Unicode case-insensitive search on both SQLite and PostgreSQL."""
import re


def literal_pattern(value):
    # SQLite's LIKE only folds ASCII. Django's iregex uses Unicode-aware matching;
    # escaping every metacharacter keeps this a text search, never a user regex.
    return re.escape(value)
