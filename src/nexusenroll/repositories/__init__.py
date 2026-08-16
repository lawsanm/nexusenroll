"""Data Access layer (tier 3 of the 3-Tier structure inside each service).

Substitutable by construction: `interfaces.py` is owned by the business logic
layer, `in_memory.py` is one implementation of it, and a SQL implementation
would be another.  Nothing above this package imports a concrete class.
"""
