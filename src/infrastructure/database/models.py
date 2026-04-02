from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.database.base import Base
from sqlalchemy import String, Integer, ForeignKey, DateTime, func, ARRAY, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from sqlalchemy.sql.expression import text

class User(Base):
    __tablename__="users"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(10))
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Room(Base):
    __tablename__="rooms"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    descriotion: Mapped[str | None] = mapped_column(Text, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Schedule(Base):
    __tablename__="schedule"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("rooms.id"), unique=True, index=True)
    days_of_week: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    start_time: Mapped[str] = mapped_column(String(5))
    end_time: Mapped[str] = mapped_column(String(5))


class Slot(Base):
    __tablename__="slots"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("rooms.id"), index=True)
    start: Mapped[DateTime] = mapped_column(DateTime(timezone=True), index=True)
    end: Mapped[DateTime] = mapped_column(DateTime(timezone=True))


class Booking(Base):
    __tablename__="bookings"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("slots.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(10), default="active")
    conference_link: Mapped[str |  None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__=(
        Index(
            "uq_booking_slot_active",
            "slot_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )
