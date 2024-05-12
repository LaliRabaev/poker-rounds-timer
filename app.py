from flask import Flask, render_template, redirect, url_for, request, jsonify
import threading
import time

app = Flask(__name__)

# Configuration
rounds = [{'round': 1, 'small_blind': 100, 'big_blind': 200}, {'round': 2, 'small_blind': 200, 'big_blind': 400}, {'round': 3, 'small_blind': 500, 'big_blind': 1000}, {'round': 4, 'small_blind': 800, 'big_blind': 1600}, {'round': 5, 'small_blind': 1000, 'big_blind': 1500},
          {'round': 6, 'small_blind': 1500, 'big_blind': 2000}, {'round': 7, 'small_blind': 2500, 'big_blind': 4000}, {'round': 8, 'small_blind': 3000, 'big_blind': 6000}, {'round': 9, 'small_blind': 4000, 'big_blind': 8000}, {'round': 10, 'small_blind': 5000, 'big_blind': 10000},
          {'round': 11, 'small_blind': 15000, 'big_blind': 20000}, {'round': 12, 'small_blind': 20000, 'big_blind': 30000}, {'round': 13, 'small_blind': 25000, 'big_blind': 40000}]
current_round_index = 0
timer_remaining = 900  # in seconds
timer_lock = threading.Lock()
timer_active = False

def timer_countdown():
    global timer_remaining, timer_active, timer_lock
    while timer_remaining > 0 and timer_active:
        time.sleep(1)
        with timer_lock:
            if timer_active:
                timer_remaining -= 1


@app.route('/')
def index():
    global current_round_index
    next_round_index = current_round_index + 1
    if next_round_index >= len(rounds):
        next_round_index = 0  # Loop back to the first round if needed

    return render_template('index.html', 
        round=rounds[current_round_index], 
        next_round=rounds[next_round_index])


@app.route('/next_round', methods=['POST'])
def next_round():
    global current_round_index, timer_active
    with timer_lock:
        current_round_index += 1  # Increment the round index
        if current_round_index >= len(rounds):
            current_round_index = 0  # Reset to first round if it's the last round
        timer_active = False  # Optionally, stop the timer
    return redirect(url_for('index'))

@app.route('/previous_round', methods=['POST'])
def previous_round():
    global current_round_index
    with timer_lock:
        current_round_index -= 1
        if current_round_index < 0:
            current_round_index = len(rounds) - 1  # Wrap around to the last round
        timer_active = False  # Optionally, stop the timer
    return redirect(url_for('index'))

@app.route('/reset_timer', methods=['POST'])
def reset_timer():
    global timer_remaining, timer_active, timer_lock
    with timer_lock:
        timer_remaining = 900  # Reset the timer to 15 minutes
        timer_active = False   # Stop the timer if it's currently running
    return redirect(url_for('index'))

@app.route('/start_timer', methods=['POST'])
def start_timer():
    global timer_remaining, timer_active, timer_lock
    with timer_lock:
        if not timer_active:  # Check if the timer is not already active
            timer_active = True
            timer_thread = threading.Thread(target=timer_countdown, args=(timer_remaining,))
            timer_thread.start()
    return redirect(url_for('index'))


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
    return redirect(url_for('index'))

@app.route('/timer')
def timer():
    with timer_lock:
        return jsonify(mins=timer_remaining // 60, secs=timer_remaining % 60)

if __name__ == '__main__':
    app.run(debug=True)
