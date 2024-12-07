import mysql.connector
import json
from flask import Flask
from flask import jsonify
from flask_cors import CORS
import requests
import math

class Database:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='flight_game',
            user='root',
            password='123456',
            collation="latin1_swedish_ci",
            autocommit=True
        )

    def get_conn(self):
        return self.conn

db = Database()
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# To create a player
@app.route('/create_player/<player>')
def create_player(player):
    sql = f'''SELECT player_id, player, airport_ident, number_of_play
                FROM player
                WHERE player = %s'''
    cursor = db.get_conn().cursor(dictionary=True)
    cursor.execute(sql, (player,))
    result = cursor.fetchall()
    number_of_play = 1

    # if the name does not already exist
    if (result == []):
        sql = f'''INSERT INTO player (player, airport_ident, number_of_play)
                    VALUES (%s, %s, 1)'''
        cursor = db.get_conn().cursor(dictionary=True)
        cursor.execute(sql, (player,'WSSS',))

    # if the name does already exist, also create a new user, set number_of_play + 1
    if (result != []):
        number_of_play = len(result) + 1
        sql = f'''INSERT INTO player (player, airport_ident, number_of_play)
                            VALUES (%s, %s, %s)'''
        cursor = db.get_conn().cursor(dictionary=True)
        cursor.execute(sql, (player,'WSSS',number_of_play,))

    response = {
        "player_id": cursor.lastrowid,
        "player": player,
        "number_of_play": number_of_play,
    }
    return response

@app.route('/get_current_airport/<player>/<number_of_play>')
def get_current_airport(player,number_of_play):
    try:
        # print(player,number_of_play)
        sql = f'''SELECT player_id, player, airport_ident, number_of_play
                        FROM player
                        WHERE player = %s AND number_of_play = %s'''
        cursor = db.get_conn().cursor(dictionary=True)
        cursor.execute(sql, (player,number_of_play))
        result = cursor.fetchall()[0]
        # print("result:",result)
        response = {
            "player_id": result["player_id"],
            "player": result["player"],
            "airport_ident": result["airport_ident"],
            "number_of_play": result["number_of_play"],
        }
        # print(response)
    finally:
        pass
    return response



# To get some airport data near current airport
@app.route('/get_near_airport_data/<current_airport>')
def get_near_airport_data(current_airport):
    from geopy import distance
    def haversine(lat1, lon1, lat2, lon2):
        # Radius of Earth in kilometers
        R = 6371.0
        # Convert degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        # Haversine formula
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        # Distance in kilometers
        distance = R * c
        return distance


    # fetch all large airports (include log and lat and name) (exclude the current airport)
    sql = f'''SELECT ident, name, latitude_deg, longitude_deg, municipality, iata_code
                    FROM airport
                    WHERE type=%s AND ident!= %s'''
    cursor = db.get_conn().cursor(dictionary=True)
    cursor.execute(sql, ('large_airport',current_airport,))
    result = cursor.fetchall()

    # fetch current airport informantion
    sql = f'''SELECT ident, name, latitude_deg, longitude_deg, municipality, iata_code
                        FROM airport
                        WHERE ident= %s'''
    cursor = db.get_conn().cursor(dictionary=True)
    cursor.execute(sql, (current_airport,))
    now_airport_result = cursor.fetchall()

    ident_cur = now_airport_result[0]["ident"]
    name_cur = now_airport_result[0]["name"]
    latitude_deg_cur = now_airport_result[0]["latitude_deg"]
    longitude_deg_cur = now_airport_result[0]["longitude_deg"]
    municipality_cur = now_airport_result[0]["municipality"]
    iata_code_cur = now_airport_result[0]["iata_code"]

    ret = []
    for row in result:
        ident = row["ident"]
        name = row["name"]
        latitude_deg = row["latitude_deg"]
        longitude_deg = row["longitude_deg"]
        municipality = row["municipality"]
        iata_code = row["iata_code"]

        # dist = haversine(latitude_deg_cur, longitude_deg_cur, latitude_deg, longitude_deg)
        dist = distance.distance((latitude_deg_cur, longitude_deg_cur), (latitude_deg, longitude_deg)).km
        if (dist <= 5000):
            ret.append( {
                    "ident": ident,
                    "name": name,
                    "latitude_deg": latitude_deg,
                    "longitude_deg": longitude_deg,
                    "municipality": municipality,
                    "iata_code": iata_code,
                    "distance": dist,   })
    return jsonify(ret)



# To get some airport information near current airport
@app.route('/get_current_airport_info/<current_airport>')
def get_current_airport_info(current_airport):
    # fetch current airport informantion
    sql = f'''SELECT ident, name, latitude_deg, longitude_deg, municipality, iata_code
                        FROM airport
                        WHERE ident= %s'''
    cursor = db.get_conn().cursor(dictionary=True)
    cursor.execute(sql, (current_airport,))
    now_airport_result = cursor.fetchall()
    # print(now_airport_result)
    return json.dumps(now_airport_result)



@app.route('/update_clicked_airport/<next_airport_ident>/<playername>/<number_of_play>')
def update_clicked_airport(next_airport_ident, playername, number_of_play):
    try:
        sql = f'''UPDATE `player`
                    SET airport_ident=%s
                    WHERE `player`=%s AND number_of_play=%s
                    '''
        conn = db.get_conn()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (next_airport_ident, playername, number_of_play,))
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
    return jsonify([])

@app.route('/update_sequence/<current_airport_ident>/<next_airport_ident>/<distance>')
def update_sequence(current_airport_ident, next_airport_ident, distance):
    sql = f'''INSERT INTO sequence (starting_location, ending_location, distance)
                VALUES (%s, %s, %s)
    '''
    conn = db.get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, (current_airport_ident, next_airport_ident, float(distance),))
    conn.commit()
    return jsonify([cursor.lastrowid])

@app.route('/update_player_seq/<player_id>/<seq_id>')
def update_player_seq(player_id, seq_id):
    sql = f'''INSERT INTO player_seq (player_id, seq_id)
                VALUES (%s, %s)
    '''
    conn = db.get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, (player_id, seq_id))
    conn.commit()
    return jsonify([])





# To check_is_game_finished(player_id)
@app.route('/check_is_game_finished/<player_id>')
def check_is_game_finished(player_id):
    sql = f'''SELECT player, airport_ident, number_of_play
                    FROM player
                    WHERE player_id=%s
        '''
    cursor = db.get_conn().cursor(dictionary=True)
    cursor.execute(sql, (player_id, ))
    result = cursor.fetchall()
    player, airport_ident, number_of_play = result[0]['player'], result[0]['airport_ident'], result[0]['number_of_play']

    # print(type(result[0]))
    # print(result[0])
    # print(result[0]['player'])
    # print(airport_ident)
    # print(number_of_play)

    if airport_ident != 'WSSS':
        return jsonify([0])
    elif airport_ident == 'WSSS':
        sql = f'''SELECT ps.seq_id,
                    a_start.longitude_deg AS starting_longitude,
                    a_end.longitude_deg AS ending_longitude,
                    s.distance
                    FROM player_seq ps
                    JOIN sequence s ON ps.seq_id = s.seq_id
                    JOIN airport a_start ON s.starting_location = a_start.ident
                    JOIN airport a_end ON s.ending_location = a_end.ident
                    WHERE ps.player_id = %s
                    ORDER BY ps.seq_id
                '''
        cursor = db.get_conn().cursor(dictionary=True)
        cursor.execute(sql, (player_id,))
        result = cursor.fetchall()
        visited_longitudes = set()
        total_distance = 0
        print("HERE")
        print(result)
        for row in result:
            seq_id, starting_longitude, ending_longitude, distance = row['seq_id'], row['starting_longitude'], row['ending_longitude'], row['distance']

            if starting_longitude < 0:
                start_longitude = int(starting_longitude) + 360
            else:
                start_longitude = int(starting_longitude)
            if ending_longitude < 0:
                end_longitude = int(ending_longitude) + 360
            else:
                end_longitude = int(ending_longitude)

            if start_longitude < end_longitude and abs(start_longitude - end_longitude) < 180:
                visited_longitudes.update(range(start_longitude-1, end_longitude + 1))
            elif start_longitude < end_longitude and abs(start_longitude - end_longitude) > 180:
                visited_longitudes.update(range(0, start_longitude + 1))
                visited_longitudes.update(range(end_longitude-1, 360 + 1))
            elif start_longitude > end_longitude and abs(start_longitude - end_longitude) < 180:
                visited_longitudes.update(range(end_longitude-1, start_longitude + 1))
            elif start_longitude > end_longitude and abs(start_longitude - end_longitude) > 180:
                visited_longitudes.update(range(0, end_longitude + 1))
                visited_longitudes.update(range(start_longitude-1, 360 + 1))

            total_distance = total_distance + distance

        if len(visited_longitudes) >= 360-20:
            return jsonify([total_distance])
        else:
            return jsonify([0])


@app.route('/insert_ranking_record/<player_id>/<total_distance>')
def insert_ranking_record(player_id, total_distance):
    sql = f'''INSERT INTO ranking (player_id, total_distance)
                VALUES (%s, %s)
        '''
    cursor = db.get_conn().cursor(dictionary=True)
    cursor.execute(sql, (player_id, total_distance, ))
    return jsonify([0])

@app.route('/get_ranking_table')
def get_ranking_table():
    sql = f'''SELECT p.player_id, p.player, r.total_distance
                    FROM ranking r
                    JOIN player p
                    ON r.player_id = p.player_id
                    ORDER BY r.total_distance ASC
            '''
    cursor = db.get_conn().cursor(dictionary=True)
    cursor.execute(sql, ())
    result = cursor.fetchall()
    print(result)
    return json.dumps(result)









# To get weather of a city
@app.route('/get_weather/<ident>')
def get_weather(ident):
    def check_weather(city_name):
        api_key = "6fb8418b9a666dbde2c8889c86619ee6"  # OpenWeatherMap API key
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"  # metric for Celsius temperature

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Failed to retrieve weather data. Status code: {response.status_code}")
            return False  # Treat as bad weather if request fails

    sql = f'''SELECT municipality
                FROM airport
                        WHERE ident=%s
                '''
    cursor = db.get_conn().cursor(dictionary=True)
    cursor.execute(sql, (ident, ))
    result = cursor.fetchall()
    city_name = result[0]['municipality']

    print(city_name)
    data = check_weather(city_name)

    return data


if __name__ == '__main__':
    app.run(use_reloader=True, host='127.0.0.1', port=3001)