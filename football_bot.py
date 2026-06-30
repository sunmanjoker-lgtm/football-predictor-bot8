import requests
from datetime import datetime, timedelta

TOKEN = '8917243606:AAHojdm5VMfKCasorA05zVtVphYXyNb4n5k'
CHAT_ID = 328619258

def send_message(text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    params = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    try:
        response = requests.post(url, json=params, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

# ======= 1. ПОЛУЧЕНИЕ МАТЧЕЙ =======
def get_matches():
    FOOTBALL_DATA_KEY = '361831563ad048fb88a38be896b4aa93'
    today = datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    LEAGUES = {
        'PL': 'Premier League',
        'PD': 'La Liga',
        'BL1': 'Bundesliga',
        'SA': 'Serie A',
        'FL1': 'Ligue 1',
        'CL': 'Champions League',
        'EL': 'Europa League'
    }
    
    matches = []
    for code, name in LEAGUES.items():
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

# ======= 2. ПРОГНОЗ (упрощённая логика) =======
def make_prediction(home, away):
    prob = 0.50
    home_lower = home.lower()
    away_lower = away.lower()
    
    if 'liverpool' in home_lower or 'man city' in home_lower or 'arsenal' in home_lower:
        prob = 0.60
    elif 'chelsea' in home_lower or 'tottenham' in home_lower:
        prob = 0.55
    elif 'man utd' in home_lower:
        prob = 0.52
    
    if prob > 0.55:
        return 'ставка на хозяев', prob
    elif prob < 0.45:
        return 'ставка на гостей', prob
    else:
        return 'пропустить', prob

# ======= 3. ОСНОВНАЯ ЛОГИКА =======
print("🔍 Поиск матчей...")
matches = get_matches()

if not matches:
    send_message("⚽ Сегодня и завтра матчей не найдено.")
    exit()

lines = []
lines.append("⚽ <b>ПРОГНОЗЫ НА СЕГОДНЯ</b>")
lines.append(f"📅 {datetime.now().strftime('%d.%m.%Y')}")
lines.append("=" * 35)
lines.append("")

for match in matches:
    pred, prob = make_prediction(match['home'], match['away'])
    lines.append(
        f"⚽ <b>{match['home']} vs {match['away']}</b>\n"
        f"🏆 {match['league']}\n"
        f"⏰ {match['time']} ({match['date']})\n"
        f"📊 {pred} ({prob:.0%})\n"
    )

msg = "\n".join(lines)
send_message(msg)
print("✅ Прогнозы отправлены")
