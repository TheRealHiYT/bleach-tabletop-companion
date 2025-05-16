from flask import Flask, render_template, redirect, url_for, request
from game_logic import Game, Character
import os
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
game = Game()

UPLOAD_FOLDER = 'characters'
ALLOWED_EXTENSIONS = {'json'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_character', methods=['GET', 'POST'])
def upload_character():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            return redirect(url_for('index'))
    return render_template('upload_character.html')


@app.route('/create_character', methods=['GET', 'POST'])
def create_character():
    if request.method == 'POST':
        data = {
            "name": request.form['name'],
            "hp": int(request.form['hp']),
            "strength": int(request.form['str']),
            "dex": int(request.form['dex']),
            "cha": int(request.form['cha']),
            "snk": int(request.form['snk']),
            "mnd": int(request.form['mnd']),
            "intl": int(request.form['intl']),
            "acc": int(request.form['acc']),
            "spd": int(request.form['spd']),
            "rei": int(request.form['rei']),
            "dmg_dice": request.form['damage_dice'],
            "max_attacks": int(request.form['max_attacks']),
            "attack_range": int(request.form['attack_range']),
        }

        filename = f"characters/{data['name'].replace(' ', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        return redirect(url_for('index'))

    return render_template('create_character.html')


@app.route('/select_character', methods=['GET', 'POST'])
def select_character():
    character_files = os.listdir('characters')
    if not character_files:
        return redirect(url_for('create_character'))

    if request.method == 'POST':
        filename = request.form['character_file']
        slot = int(request.form['player_slot'])  # 0 or 1
        x, y = (1, 1) if slot == 0 else (8, 8)  # Start positions
        char = Character.from_json(os.path.join('characters', filename), x, y)
        game.players[slot] = char
        game.log.append(f"Loaded {char.name} into Player {slot + 1} slot.")
        ai_mode = request.form['ai_mode']
        game.ai_mode = False if ai_mode == "no" else True
        game.import_ai()
        return redirect(url_for('index'))

    return render_template('select_character.html', files=character_files)


@app.route('/')
def index():
    if game.players[0] is None or game.players[1] is None:
        return redirect(url_for('select_character'))

    if game.current_player == game.players[0]:
        game.players[0].has_acted = False

    elif game.current_player == game.players[1]:
        if not game.players[1].has_acted and game.ai_mode:
            game.players[1].has_acted = True
            game.ai_decide_and_play()
            return redirect(url_for('index'))

    return render_template('index.html', game=game)


@app.route('/attack')
def attack():
    game.attack()
    return redirect(url_for('index'))


@app.route('/end_turn')
def end_turn():
    game.end_turn()
    return redirect(url_for('index'))


@app.route('/auto_fight')
def auto_fight():
    while game.players[0].is_alive() and game.players[1].is_alive():
        for _ in range(game.current_player.max_attacks):
            game.attack()
        game.end_turn()

    winner = game.get_winner()
    if winner:
        game.log.append(f"{winner.name} wins the battle!")
    else:
        game.log.append("It's a draw!")

    return redirect(url_for('result'))


@app.route('/result')
def result():
    winner = game.get_winner()
    return render_template('result.html', game=game, winner=winner)


@app.route('/move')
def move():
    dx = int(request.args.get('dx', 0))
    dy = int(request.args.get('dy', 0))
    game.move_current_player(dx, dy)
    return redirect(url_for('index'))


@app.route('/new_battle', methods=['POST'])
def new_battle():
    global game
    game = Game()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
