from flask import Flask, render_template, redirect, url_for, request, jsonify
import threading
import time
import json
import os

app = Flask(__name__)

# Configuration
rounds = [
    {'round': 1, 'small_blind': 100, 'big_blind': 200, 'duration': 900},
    {'round': 2, 'small_blind': 200, 'big_blind': 400, 'duration': 900},
    {'round': 3, 'small_blind': 500, 'big_blind': 1000, 'duration': 900},
    {'round': 4, 'small_blind': 800, 'big_blind': 1600, 'duration': 900},
    {'round': 5, 'small_blind': 1000, 'big_blind': 1500, 'duration': 900},
    {'round': 6, 'small_blind': 1500, 'big_blind': 2000, 'duration': 900},
    {'round': 7, 'small_blind': 2500, 'big_blind': 4000, 'duration': 900},
    {'round': 8, 'small_blind': 3000, 'big_blind': 6000, 'duration': 900},
    {'round': 9, 'small_blind': 4000, 'big_blind': 8000, 'duration': 900},
    {'round': 10, 'small_blind': 5000, 'big_blind': 10000, 'duration': 900},
    {'round': 11, 'small_blind': 15000, 'big_blind': 20000, 'duration': 900},
    {'round': 12, 'small_blind': 20000, 'big_blind': 30000, 'duration': 900},
    {'round': 13, 'small_blind': 25000, 'big_blind': 40000, 'duration': 900}
]

# Player management
players_data_file = 'players.json'
default_players = [
    {'id': 1, 'name': 'Player 1', 'active': True, 'position': 1},
    {'id': 2, 'name': 'Player 2', 'active': True, 'position': 2},
    {'id': 3, 'name': 'Player 3', 'active': True, 'position': 3},
    {'id': 4, 'name': 'Player 4', 'active': True, 'position': 4},
    {'id': 5, 'name': 'Player 5', 'active': True, 'position': 5},
    {'id': 6, 'name': 'Player 6', 'active': True, 'position': 6}
]

current_round_index = 0
timer_remaining = rounds[0]['duration']  # Initialize with first round duration
timer_lock = threading.Lock()
timer_active = False
hand_counter = 0
dealer_position = 1
small_blind_position = 2
big_blind_position = 3

def timer_countdown():
    global timer_remaining, timer_active, timer_lock
    while timer_remaining > 0 and timer_active:
        time.sleep(1)
        with timer_lock:
            if timer_active:
                timer_remaining -= 1

def load_players():
    if os.path.exists(players_data_file):
        with open(players_data_file, 'r') as f:
            return json.load(f)
    return default_players

def save_players(players):
    with open(players_data_file, 'w') as f:
        json.dump(players, f)

@app.route('/')
def index():
    global current_round_index
    players = load_players()
    active_players = [p for p in players if p['active']]
    
    next_round_index = current_round_index + 1
    if next_round_index >= len(rounds):
        next_round_index = 0  # Loop back to the first round if needed

    return render_template('index.html', 
        round=rounds[current_round_index], 
        next_round=rounds[next_round_index],
        players=active_players,
        hand_counter=hand_counter,
        dealer_position=dealer_position,
        small_blind_position=small_blind_position,
        big_blind_position=big_blind_position)

@app.route('/update_round_time', methods=['POST'])
def update_round_time():
    round_index = int(request.form.get('round_index'))
    new_duration_minutes = int(request.form.get('duration'))
    new_duration_seconds = new_duration_minutes * 60  # Convert minutes to seconds
    
    if 0 <= round_index < len(rounds):
        rounds[round_index]['duration'] = new_duration_seconds  # Store as seconds
        if round_index == current_round_index:
            global timer_remaining
            with timer_lock:
                timer_remaining = new_duration_seconds  # Set timer in seconds
    
    return redirect(url_for('settings'))

@app.route('/update_blinds', methods=['POST'])
def update_blinds():
    round_index = int(request.form.get('round_index'))
    small_blind = int(request.form.get('small_blind'))
    big_blind = int(request.form.get('big_blind'))
    
    if 0 <= round_index < len(rounds):
        rounds[round_index]['small_blind'] = small_blind
        rounds[round_index]['big_blind'] = big_blind
    
    return redirect(url_for('settings'))

@app.route('/settings')
def settings():
    return render_template('settings.html', rounds=rounds, players=load_players())

@app.route('/next_round', methods=['POST'])
def next_round():
    global current_round_index, timer_active, timer_remaining
    with timer_lock:
        current_round_index += 1  # Increment the round index
        if current_round_index >= len(rounds):
            current_round_index = 0  # Reset to first round if it's the last round
        timer_active = False  # Stop the timer
        timer_remaining = rounds[current_round_index]['duration']  # Reset timer to new round duration
    return redirect(url_for('index'))

@app.route('/previous_round', methods=['POST'])
def previous_round():
    global current_round_index, timer_active, timer_remaining
    with timer_lock:
        current_round_index -= 1
        if current_round_index < 0:
            current_round_index = len(rounds) - 1  # Wrap around to the last round
        timer_active = False  # Stop the timer
        timer_remaining = rounds[current_round_index]['duration']  # Reset timer to new round duration
    return redirect(url_for('index'))

@app.route('/reset_timer', methods=['POST'])
def reset_timer():
    global timer_remaining, timer_active, timer_lock
    with timer_lock:
        timer_remaining = rounds[current_round_index]['duration']  # Reset to current round duration
        timer_active = False   # Stop the timer if it's currently running
    return jsonify(success=True, mins=timer_remaining // 60, secs=timer_remaining % 60)

@app.route('/continue_timer', methods=['POST'])
def continue_timer():
    global timer_active, timer_lock
    print("Received request to continue timer.")
    with timer_lock:
        if not timer_active:
            timer_active = True
            timer_thread = threading.Thread(target=timer_countdown)
            timer_thread.start()
            print("Timer is now active.")
            return jsonify(success=True)
        print("Timer was already active.")
        return jsonify(success=False), 400

@app.route('/stop_timer', methods=['POST'])
def stop_timer():
    global timer_active
    with timer_lock:
        timer_active = False
    return jsonify(success=True)

@app.route('/timer')
def timer():
    with timer_lock:
        round_complete = timer_remaining <= 0
        return jsonify(mins=timer_remaining // 60, secs=timer_remaining % 60, complete=round_complete)

@app.route('/next_hand', methods=['POST'])
def next_hand():
    global hand_counter, dealer_position, small_blind_position, big_blind_position
    
    players = load_players()
    active_players = [p for p in players if p['active']]
    player_count = len(active_players)
    
    if player_count > 0:
        hand_counter += 1
        
        # Move dealer and blind positions
        dealer_position = (dealer_position % player_count) + 1
        small_blind_position = (dealer_position % player_count) + 1
        big_blind_position = (small_blind_position % player_count) + 1
    
    return jsonify({
        'success': True, 
        'hand_counter': hand_counter,
        'dealer_position': dealer_position,
        'sb_position': small_blind_position,
        'bb_position': big_blind_position
    })

@app.route('/reset_hands', methods=['POST'])
def reset_hands():
    global hand_counter
    hand_counter = 0
    return jsonify({
        'success': True, 
        'hand_counter': hand_counter
    })

@app.route('/update_player', methods=['POST'])
def update_player():
    player_id = int(request.form.get('id'))
    name = request.form.get('name')
    active = request.form.get('active') == 'true'
    
    players = load_players()
    for player in players:
        if player['id'] == player_id:
            player['name'] = name
            player['active'] = active
            break
    
    save_players(players)
    return redirect(url_for('settings'))

if __name__ == '__main__':
    app.run(debug=True)
