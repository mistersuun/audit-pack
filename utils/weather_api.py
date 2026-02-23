"""
Utility to fetch weather forecast using OpenWeather API (free tier).
"""

import os
import requests
from datetime import datetime


def get_current_weather_data():
    """
    Get current weather conditions for Laval, QC as structured data.

    Returns:
        dict with temperature, feels_like, description, humidity, wind_speed
    """
    api_key = os.getenv('OPENWEATHER_API_KEY', 'REMOVED_KEY')
    lat, lon = 45.5800, -73.7600

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=fr"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    return {
        'temperature': round(data['main']['temp']),
        'feels_like': round(data['main']['feels_like']),
        'description': data['weather'][0]['description'].capitalize(),
        'humidity': data['main']['humidity'],
        'wind_speed': round(data['wind']['speed'] * 3.6),  # km/h
        'icon': data['weather'][0]['icon'],
    }

def get_weather_forecast_laval():
    """
    Gets 7-day weather forecast for Laval using OpenWeather OneCall API.
    Uses free API key (limited to 1000 calls/day).
    Returns: Formatted string with weather data.
    """
    try:
        # Using a free OpenWeather API key (public for this project)
        # You can get your own at: https://openweathermap.org/api
        api_key = os.getenv('OPENWEATHER_API_KEY', 'REMOVED_KEY')

        # Coordinates for Laval, QC
        lat, lon = 45.5800, -73.7600

        # Get current weather + 7-day forecast
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=fr&cnt=40"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Get current weather
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=fr"
        current_response = requests.get(current_url, timeout=10)
        current_data = current_response.json()

        # Format the forecast
        today = datetime.now().strftime('%d %B %Y')

        # Current conditions
        current_temp = current_data['main']['temp']
        feels_like = current_data['main']['feels_like']
        description = current_data['weather'][0]['description']
        humidity = current_data['main']['humidity']
        wind_speed = current_data['wind']['speed'] * 3.6  # Convert m/s to km/h

        output = f"""╔══════════════════════════════════════════════════════════╗
  PRÉVISIONS MÉTÉO - LAVAL, QC
  Mise à jour: {today}
╚══════════════════════════════════════════════════════════╝

CONDITIONS ACTUELLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌡️  Température: {current_temp:.1f}°C (ressenti {feels_like:.1f}°C)
☁️  Conditions: {description.capitalize()}
💧 Humidité: {humidity}%
💨 Vent: {wind_speed:.0f} km/h

PRÉVISIONS 7 PROCHAINS JOURS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # Group forecasts by day (get one forecast per day around noon)
        daily_forecasts = {}
        days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

        for item in data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            date_key = dt.strftime('%Y-%m-%d')

            # Take the forecast around 12:00 for each day
            if date_key not in daily_forecasts and dt.hour >= 12:
                day_name = days_fr[dt.weekday()]
                date_str = dt.strftime('%d/%m')

                daily_forecasts[date_key] = {
                    'day': day_name,
                    'date': date_str,
                    'temp': item['main']['temp'],
                    'temp_min': item['main']['temp_min'],
                    'temp_max': item['main']['temp_max'],
                    'description': item['weather'][0]['description'],
                    'pop': item.get('pop', 0) * 100,  # Probability of precipitation
                    'humidity': item['main']['humidity']
                }

            if len(daily_forecasts) >= 7:
                break

        # Format each day
        for date_key in sorted(daily_forecasts.keys())[:7]:
            f = daily_forecasts[date_key]

            # Choose appropriate emoji based on description
            weather_emoji = "☁️"
            desc_lower = f['description'].lower()
            if 'pluie' in desc_lower or 'averses' in desc_lower:
                weather_emoji = "🌧️"
            elif 'neige' in desc_lower:
                weather_emoji = "❄️"
            elif 'orage' in desc_lower:
                weather_emoji = "⛈️"
            elif 'ensoleillé' in desc_lower or 'clair' in desc_lower or 'dégagé' in desc_lower:
                weather_emoji = "☀️"
            elif 'nuageux' in desc_lower or 'couvert' in desc_lower:
                weather_emoji = "☁️"

            output += f"""
{weather_emoji}  {f['day']} {f['date']}
   {f['description'].capitalize()}
   Température: {f['temp']:.0f}°C (min {f['temp_min']:.0f}°C, max {f['temp_max']:.0f}°C)
   Précipitations: {f['pop']:.0f}% | Humidité: {f['humidity']}%
"""

        output += "\n" + "─" * 60

        return output

    except Exception as e:
        print(f"Error fetching weather: {e}")
        return """╔══════════════════════════════════════════════════════════╗
  PRÉVISIONS MÉTÉO - LAVAL, QC
╚══════════════════════════════════════════════════════════╝

⚠️  Service météo temporairement indisponible.

Veuillez consulter:
• meteomedia.com/ca/weather/quebec/laval
• weather.gc.ca

Pour les prévisions météo actuelles.
"""
