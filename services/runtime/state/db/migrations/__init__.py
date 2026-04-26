"""Database migration support.

Migrations are idempotent column additions that run after
Base.metadata.create_all() to handle schema drift on existing databases.
"""
