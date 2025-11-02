from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware 
from pydantic import BaseModel
from typing import List
import requests
from sqlalchemy.orm import Session
from database import get_db
import models
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


WEATHER_API_KEY = "023c9c13319858500d625d1f1b79a09b"

@app.get("/suggest-clothes/{city_name}")
def suggest_clothes(city_name: str, db: Session = Depends(get_db)):
    """
    Auto-fetch weather, store in DB, and get smart clothing suggestions
    """
    print(f"\n{'='*60}")
    print(f"Processing request for: {city_name}")
    print(f"{'='*60}")
    
    # STEP 1: Check if city exists in database
    city = db.query(models.city).filter(models.city.name.ilike(city_name)).first()
    
    if not city:
        print(f"City '{city_name}' not found in database. Fetching from OpenWeather API...")
        
        # STEP 2: Fetch from OpenWeather API
        weather_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {"q": city_name, "appid": WEATHER_API_KEY, "units": "metric"}
        
        try:
            weather_response = requests.get(weather_url, params=params, timeout=10)
            
            if weather_response.status_code != 200:
                raise HTTPException(
                    status_code=404, 
                    detail=f"City '{city_name}' not found in OpenWeather API"
                )
            
            data = weather_response.json()
            print(f"✓ Weather data fetched successfully")
            
            # STEP 3: Store in database
            city = models.city(
                name=data["name"].lower(),
                city_id=str(data["id"]),
                long=data["coord"]["lon"],
                lat=data["coord"]["lat"],
                country=data["sys"]["country"],
            )
            
            weather = models.weather(
                city_id=str(data["id"]),
                weather_id=str(data["id"]),
                description=data["weather"][0]["description"],
                main=data["weather"][0]["main"]
            )
            
            weather_info = models.weather_info(
                city_id=str(data["id"]),
                temp=data["main"]["temp"],
                feels_like=data["main"]["feels_like"],
                temp_min=data["main"]["temp_min"],
                temp_max=data["main"]["temp_max"],
                humidity=data["main"]["humidity"]
            )
            
            wind_info = models.wind_info(
                city_id=str(data["id"]),
                speed=data["wind"]["speed"],
                gust=data["wind"].get("gust", None)
            )
            
            db.merge(city)
            db.merge(weather)
            db.merge(weather_info)
            db.merge(wind_info)
            db.commit()
            
            print(f"✓ City data stored in database")
            
        except requests.RequestException as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to fetch weather data: {str(e)}"
            )
    else:
        print(f"✓ City '{city_name}' found in database")

    # STEP 4: Get weather data from database
    weather_info = db.query(models.weather_info).filter(
        models.weather_info.city_id == city.city_id
    ).first()
    
    weather = db.query(models.weather).filter(
        models.weather.city_id == city.city_id
    ).first()
    
    wind_info = db.query(models.wind_info).filter(
        models.wind_info.city_id == city.city_id
    ).first()

    if not weather_info or not weather:
        raise HTTPException(status_code=404, detail="Weather data not found")

    print(f"✓ Weather data retrieved: {weather_info.temp}°C, {weather.description}")

    # STEP 5: Generate Smart Rule-Based Suggestions
    print(f"\n🧠 Generating smart clothing suggestions...")
    print(f"   Condition detected: {weather.description}")
    
    temp = weather_info.temp
    humidity = weather_info.humidity
    condition = weather.description.lower()
    wind_speed = wind_info.speed if wind_info else 0
    
    suggestions = []
    
    # Temperature-based suggestions (base layer)
    if temp < 0:
        suggestions = [
            "Heavy Winter Jacket with insulation",
            "Thermal Underwear (top and bottom)",
            "Insulated Winter Boots",
            "Thick Wool Scarf",
            "Insulated Gloves",
            "Warm Beanie or Winter Hat"
        ]
    elif 0 <= temp < 10:
        suggestions = [
            "Winter Jacket or Heavy Coat",
            "Warm Sweater or Hoodie",
            "Long Pants (jeans or chinos)",
            "Closed-toe Shoes or Boots",
            "Light Scarf"
        ]
    elif 10 <= temp < 20:
        suggestions = [
            "Light Jacket or Cardigan",
            "Long Sleeve Shirt or Blouse",
            "Jeans or Long Pants",
            "Comfortable Sneakers"
        ]
    elif 20 <= temp < 30:
        suggestions = [
            "T-Shirt or Polo Shirt",
            "Light Pants or Shorts",
            "Comfortable Sneakers",
            "Sunglasses"
        ]
    else:  # 30+
        suggestions = [
            "Light Cotton T-Shirt or Tank Top",
            "Shorts or Light Linen Pants",
            "Sandals or Breathable Shoes",
            "Sunglasses (UV protection)",
            "Wide-brim Sun Hat"
        ]
    
    # ENHANCED WEATHER CONDITION ADJUSTMENTS
    
    # RAIN - Different intensities
    if "rain" in condition:
        print(f"   🌧️  Rain detected!")
        if "heavy" in condition or "extreme" in condition:
            print(f"   ⚠️  Heavy rain!")
            suggestions.insert(0, "🌧️ Heavy-duty Waterproof Jacket")
            suggestions.insert(1, "Waterproof Pants")
            suggestions.append("Rain Boots (Wellington boots)")
            suggestions.append("Large Sturdy Umbrella")
            suggestions.append("Waterproof Bag/Backpack cover")
        elif "light" in condition:
            print(f"   💧 Light rain")
            suggestions.insert(0, "🌧️ Light Rain Jacket or Windbreaker")
            suggestions.append("Water-resistant Shoes")
            suggestions.append("Compact Umbrella")
        else:
            print(f"   🌧️  Moderate rain")
            suggestions.insert(0, "🌧️ Waterproof Raincoat")
            suggestions.append("Waterproof Shoes or Rain Boots")
            suggestions.append("Umbrella")
            suggestions.append("Waterproof Bag cover")
    
    if "drizzle" in condition:
        print(f"   💧 Drizzle detected")
        suggestions.insert(0, "💧 Light Rain Jacket or Hoodie with hood")
        suggestions.append("Water-resistant Footwear")
        suggestions.append("Compact Umbrella (optional)")
    
    if "shower" in condition:
        print(f"   🌦️  Showers expected")
        suggestions.insert(0, "🌦️ Packable Rain Jacket")
        suggestions.append("Quick-dry Clothing")
        suggestions.append("Waterproof Footwear")
        suggestions.append("Keep umbrella handy")
    
    if "thunderstorm" in condition:
        print(f"   ⛈️  Thunderstorm warning!")
        suggestions.insert(0, "⛈️ Heavy Waterproof Raincoat")
        suggestions.insert(1, "Rubber-soled Waterproof Boots")
        suggestions.append("Sturdy Umbrella (non-metallic)")
        suggestions.append("Avoid metallic accessories")
        suggestions.append("⚠️ Stay indoors if possible")
    
    if "snow" in condition:
        print(f"   ❄️  Snow conditions")
        suggestions.insert(0, "❄️ Insulated Waterproof Winter Jacket")
        suggestions.insert(1, "Insulated Snow Boots with grip")
        suggestions.append("Waterproof Gloves")
        suggestions.append("Winter Hat covering ears")
        suggestions.append("Scarf or Neck Warmer")
    
    if "fog" in condition or "mist" in condition:
        print(f"   🌫️  Foggy/Misty conditions")
        suggestions.append("Light layers (easy to adjust)")
        suggestions.append("Reflective clothing if walking/cycling")
    
    # Wind adjustments
    if wind_speed > 25:
        print(f"   💨 Strong winds detected!")
        suggestions.append("💨 Windbreaker or Wind-resistant Jacket")
        suggestions.append("Secure hat or avoid wearing one")
    elif wind_speed > 15:
        suggestions.append("Light Windbreaker")
    
    # Humidity adjustments
    if humidity > 80:
        print(f"   💧 High humidity")
        suggestions.append("Breathable fabrics (Cotton/Linen)")
        suggestions.append("Moisture-wicking clothing")
    
    # Take first 6-8 items and format as numbered list
    final_suggestions = suggestions[:8]
    ai_suggestion = "\n".join([f"{i+1}. {item}" for i, item in enumerate(final_suggestions)])
    
    print(f"✓ Generated {len(final_suggestions)} suggestions!")
    print(f"\n{'='*60}")
    
    # Return in correct format for frontend
    return {
        "success": True,
        "city": city.name.title(),
        "country": city.country,
        "coordinates": {
            "latitude": city.lat,
            "longitude": city.long
        },
        "weather": {
            "temperature": weather_info.temp,
            "feels_like": weather_info.feels_like,
            "condition": weather.description,
            "humidity": weather_info.humidity,
            "wind_speed": wind_info.speed if wind_info else None
        },
        "ai_suggestion": ai_suggestion,
        "model": "Smart Weather-Based AI",
        "data_source": "OpenWeather API"
    }

@app.delete("/city")
def delete_city(city_name: str, db: Session = Depends(get_db)):
    city = db.query(models.city).filter(models.city.name.ilike(city_name)).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    
    db.query(models.weather).filter(models.weather.city_id == city.city_id).delete()
    db.query(models.weather_info).filter(models.weather_info.city_id == city.city_id).delete()
    db.query(models.wind_info).filter(models.wind_info.city_id == city.city_id).delete()
    db.delete(city)
    db.commit()
    
    return {"message": f"City '{city.name}' and related data deleted successfully"}


@app.get("/cities")
def get_cities(db: Session = Depends(get_db)):
    city_data = db.query(models.city).all()
    if not city_data:
        return {"cities": []}

    response_data = []
    for data in city_data:
        weather = db.query(models.weather).filter(models.weather.city_id == data.city_id).first()
        weather_info = db.query(models.weather_info).filter(models.weather_info.city_id == data.city_id).first()
        wind_info = db.query(models.wind_info).filter(models.wind_info.city_id == data.city_id).first()

        cur_data = {
            "id": data.city_id,
            "name": data.name,
            "long": data.long,
            "lat": data.lat,
            "country": data.country,
            "weather": {
                "weather_id": weather.weather_id if weather else None,
                "main": weather.main if weather else None,
                "description": weather.description if weather else None
            },
            "weather_info": {
                "temp": weather_info.temp if weather_info else None,
                "feels_like": weather_info.feels_like if weather_info else None,
                "temp_min": weather_info.temp_min if weather_info else None,
                "temp_max": weather_info.temp_max if weather_info else None,
                "humidity": weather_info.humidity if weather_info else None
            },
            "wind_info": {
                "speed": wind_info.speed if wind_info else None,
                "gust": wind_info.gust if wind_info else None
            }
        }
        response_data.append(cur_data)

    return {"cities": response_data}


@app.post("/sync-weather")
def sync_weather(cities: List[str], db: Session = Depends(get_db)):
    API_KEY = "023c9c13319858500d625d1f1b79a09b"
    URL = "http://api.openweathermap.org/data/2.5/weather"
    stored = []

    for city_name in cities:
        params = {"q": city_name, "appid": API_KEY, "units": "metric"}
        res = requests.get(URL, params=params)
        if res.status_code != 200:
            raise HTTPException(status_code=404, detail=f"City {city_name} not found")

        data = res.json()

        city = models.city(
            name=data["name"].lower(),
            city_id=str(data["id"]),
            long=data["coord"]["lon"],
            lat=data["coord"]["lat"],
            country=data["sys"]["country"],
        )

        weather = models.weather(
            city_id=str(data["id"]),
            weather_id=str(data["id"]),
            description=data["weather"][0]["description"],
            main=data["weather"][0]["main"]
        )
        
        weather_info = models.weather_info(
            city_id=str(data["id"]),
            temp=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            temp_min=data["main"]["temp_min"],
            temp_max=data["main"]["temp_max"],
            humidity=data["main"]["humidity"]
        )
        
        wind_info = models.wind_info(
            city_id=str(data["id"]),
            speed=data["wind"]["speed"],
            gust=data["wind"].get("gust", None)
        )
        
        db.merge(city)
        db.merge(weather)
        db.merge(weather_info)
        db.merge(wind_info)
        db.commit()
        stored.append(city_name)

    return {"success": True, "message": "Data stored", "cities": stored}