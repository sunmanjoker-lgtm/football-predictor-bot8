import requests
import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

TOKEN = 'ТВОЙ_ТОКЕН_СЮДА'
CHAT_ID = ТВОЙ_CHAT_ID_СЮДА

def send_message(text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    params = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    return requests.post(url, json=params).json()

# ======= 1. ЗАГРУЗКА МОДЕЛИ =======
def load_model():
    try:
        with open('model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        return model, scaler, True
    except:
        return None, None, False

model, scaler, model_loaded = load_model()

# ======= 2. ПОЛУЧЕНИЕ МАТЧЕЙ =======
def get_todays_matches():
    """Получает матчи на сегодня с Football-Data.org"""
    FOOTBALL_DATA_KEY = '361831563ad048fb88a38be896b4aa93'
    today = datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    leagues = {
        'PL': 'Premier League',
        'PD': 'La Liga',
        'BL1': 'Bundesliga',
        'SA': 'Serie A',
        'FL1': 'Ligue 1',
        'CL': 'Champions League',
        'EL': 'Europa League'
    }
    
    matches = []
    for code, name in leagues.items():
        for date_str in [today, tomorrow]:
            url = f"https://api.football-data.org/v4/competitions/{code}/matches"
            headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
            params = {"dateFrom": date_str, "dateTo": date_str}
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                if response.status_code != 200:
                    continue
                data = response.json()
                for match in data.get('matches', []):
                    status = match.get('status', '')
                    if status in ['FINISHED', 'POSTPONED', 'CANCELLED']:
                        continue
                    matches.append({
                        'home': match['homeTeam']['name'],
                        'away': match['awayTeam']['name'],
                        'league': name,
                        'date': match['utcDate'][:10],
                        'time': match['utcDate'][11:16]
                    })
            except:
                continue
    return matches

# ======= 3. ПРОГНОЗ =======
def make_prediction(home, away):
    """Упрощённый прогноз без модели"""
    # Если модель загружена — используем
    if model_loaded and scaler is not None:
        try:
            # Создаём фичи для модели
            features = pd.DataFrame([{
                'HomeElo': 1500,
                'AwayElo': 1500,
                'Form3Home': 6,
                'Form5Home': 10,
                'Form3Away': 6,
                'Form5Away': 10,
                'OddHome': 2.0,
                'OddDraw': 3.5,
                'OddAway': 3.5,
                'MaxHome': 2.1,
                'MaxDraw': 3.7,
                'MaxAway': 3.7
            }])
            X_scaled = scaler.transform(features)
            prob_home = model.predict_proba(X_scaled)[0][1]
            
            if prob_home > 0.55:
                return 'ставка на хозяев', prob_home
            elif prob_home < 0.45:
                return 'ставка на гостей', prob_home
            else:
                return 'пропустить', prob_home
        except:
            pass
    
    # Упрощённая логика
    prob = 0.5
    return 'модель не загружена', prob

# ======= 4. ОСНОВНАЯ ЛОГИКА =======
print("🔍 Поиск матчей...")
matches = get_todays_matches()

if not matches:
    send_message('⚽ Сегодня и завтра матчей не найдено.')
    exit()

# Формируем прогнозы
lines = []
lines.append("⚽ <b>ПРОГНОЗЫ НА СЕГОДНЯ</b>")
lines.append(f"📅 {datetime.now().strftime('%d.%m.%Y')}")
lines.append("=" * 35)
lines.append("")

for match in matches:
    win_rec, prob = make_prediction(match['home'], match['away'])
    lines.append(
        f"⚽ {match['home']} vs {match['away']}\n"
        f"🏆 {match['league']}\n"
        f"⏰ {match['time']}\n"
        f"📊 {win_rec} ({prob:.0%})\n"
    )

msg = "\n".join(lines)
send_message(msg)
print("✅ Прогнозы отправлены")
