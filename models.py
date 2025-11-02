from database import Base
from sqlalchemy import Column,Integer,Float,String,ForeignKey
from sqlalchemy.orm import relationship

class city(Base):
    __tablename__ = "city"

    city_id = Column(String(191), primary_key=True)
    long = Column(Float)
    lat = Column(Float)
    name = Column(String(500))
    country = Column(String(500))


class weather(Base):
    __tablename__ = "weather"

    weather_id = Column(String(191), primary_key=True)
    main = Column(String)
    description = Column(String)
    icon = Column(String(500))
    city_id = Column(String(191),ForeignKey(city.city_id))


class weather_info(Base):
    __tablename__="weather_info"

    id=Column(String(191),primary_key=False)
    city_id=Column(String(191),ForeignKey(city.city_id), primary_key=True)
    temp = Column(Float)
    feels_like = Column(Float)
    temp_min = Column(Float)
    temp_max = Column(Float)
    pressure = Column(Float)
    humidity = Column(Float)
    sea_lvl = Column(Float)
    grnd_lvl = Column(Float)
    visibility = Column(Float)


class wind_info(Base):
    __tablename__="wind_info"

    id=Column(String(191),primary_key=False)
    city_id=Column(String(191),ForeignKey(city.city_id), primary_key=True)
    speed=Column(Float)
    gust=Column(Float)
