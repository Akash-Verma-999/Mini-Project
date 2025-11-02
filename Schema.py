from pydantic import BaseModel

class CitySchema(BaseModel):
    city_id: str
    name: str
    country: str
    lat: float
    long: float

    class Config:
        orm_mode = True

class WeatherSchema(BaseModel):
    weather_id: str
    main: str
    description: str
    icon: str
    city_id: str

    class Config:
        orm_mode = True


class WeatherInfoSchema(BaseModel):
    id: int
    city_id: str
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int
    sea_lvl: int
    grnd_lvl: int
    visibility: int

    class Config:
        orm_mode = True

class WindInfoSchema(BaseModel):
    id: int
    city_id: str
    speed: float
    gust: float

    class Config:
        orm_mode = True
