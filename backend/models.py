from datetime import datetime
from sqlalchemy import Column, Integer, Numeric, DateTime, func
from database import Base


class PT100Reading(Base):
    __tablename__ = "pt100_readings"

    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Numeric(6, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DHT22Reading(Base):
    __tablename__ = "dht22_readings"

    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Numeric(5, 2), nullable=False)
    humidity = Column(Numeric(5, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GY906Reading(Base):
    __tablename__ = "gy906_readings"

    id = Column(Integer, primary_key=True, index=True)
    object_temp = Column(Numeric(6, 2), nullable=False)
    ambient_temp = Column(Numeric(6, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
