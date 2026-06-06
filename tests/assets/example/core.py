from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, MetaData, String, Table, Text, Uuid

UTC = timezone.utc

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4()),
    Column("display_name", String(100)),
    Column("created", DateTime, nullable=False, default=datetime.now(UTC)),
)

posts = Table(
    "posts",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4()),
    Column("author", ForeignKey("users.id"), nullable=False),
    Column("created", DateTime, nullable=False, default=datetime.now(UTC)),
    Column("live", Boolean, default=False, comment="True if post is published"),
    Column("content", Text, default=""),
)

comments = Table(
    "comments",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid4()),
    Column("post", Uuid, ForeignKey("posts.id"), default=uuid4()),
    Column("author", ForeignKey("users.id"), nullable=False),
    Column("created", DateTime, nullable=False, default=datetime.now(UTC)),
    Column("live", Boolean, default=False),
    Column("content", Text, default=""),
)
