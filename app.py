import os
import io
import base64
import time

from flask import Flask, render_template_string, request, redirect, url_for
import numpy as np
import matplotlib.pyplot as plt

# --- Original Game Logic Restored ---
class Kalaha:
    def __init__(self, start_number=6, play_timer=0):
        self.play_timer = play_timer
        # six pits each side + store
        self.s1_f1 = self.s1_f2 = self.s1_f3 = self.s1_f4 = self.s1_f5 = self.s1_f6 = start_number
        self.s2_f1 = self.s2_f2 = self.s2_f3 = self.s2_f4 = self.s2_f5 = self.s2_f6 = start_number
        self.s1_points = self.s2_points = 0
        self.board = np.array([
            [self.s1_f1, self.s1_f2, self.s1_f3, self.s1_f4, self.s1_f5, self.s1_f6, self.s1_points],
            [self.s2_f1, self.s2_f2, self.s2_f3, self.s2_f4, self.s2_f5, self.s2_f6, self.s2_points]
        ])
        self.n_stones = 0
        self.total_stones = np.sum(self.board)
        self.player1_name = 'Player1'
        self.player2_name = 'Player2'
        self.lastposition = [0, 0]
        self.player_counter = False  # False → Player1, True → Player2

    def set_player_name(self, player1, player2):
        self.player1_name = player1
        self.player2_name = player2

    def reset_game(self, start_number=6):
        self.__init__(start_number, self.play_timer)

    def display_board_image(self):
        """Render the board to a PNG and return as base64."""
        fig, ax = plt.subplots(figsize=(6, 3))
        # pits
        for r in (0,1):
            for c in range(6):
                ax.text(c + 1, 1 - r, str(self.board[r, c]), ha='center', va='center', fontsize=14)
        # stores
        ax.text(0, 1, str(self.s2_points), ha='center', va='center', fontsize=16, fontweight='bold')
        ax.text(7, 0, str(self.s1_points), ha='center', va='center', fontsize=16, fontweight='bold')
        ax.set_xlim(-0.5, 7.5)
        ax.set_ylim(-0.5, 1.5)
        ax.axis('off')
        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('ascii')

    def play(self, field_input):
        """Exact sowing & capture rules from your original class."""
        field_input -= 1
        # pick row by player
        row = 0 if not self.player_counter else 1
        if self.board[row, field_input] == 0:
            return  # invalid move
        
        # pick up
        self.n_stones = self.board[row, field_input]
        self.board[row, field_input] = 0
        last_row, last_col = row, field_input

        while self.n_stones > 0:
            # move
            if last_row == 0:
                # on bottom row, move right until store at col=6, then switch to row=1
                if last_col < 6:
                    last_col += 1
                else:
                    last_row = 1
                    last_col = 6
            else:
                # on top row, move left until store at col=6, then switch to row=0
                if last_col > 0:
                    last_col -= 1
                else:
                    last_row = 0
                    last_col = 0

            # sow or score into store
            if last_col == 6:
                # store cell
                if (last_row == 0 and not self.player_counter) or (last_row == 1 and self.player_counter):
                    if last_row == 0:
                        self.s1_points += 1
                    else:
                        self.s2_points += 1
                    self.n_stones -= 1
                # else skip opponent's store
            else:
                # normal pit
                self.board[last_row, last_col] += 1
                self.n_stones -= 1
            time.sleep(self.play_timer)
        
        # capture: if last stone landed in an empty pit on your side
        if last_col != 6 and last_row == row and self.board[last_row, last_col] == 1:
            opp_col = 5 - last_col
            opp_row = 1 - last_row
            captured = self.board[opp_row, opp_col]
            if captured > 0:
                # move both into your store
                if row == 0:
                    self.s1_points += captured + 1
                else:
                    self.s2_points += captured + 1
                self.board[opp_row, opp_col] = 0
                self.board[last_row, last_col] = 0

        # toggle player unless ended in your store (extra turn)
        if last_col != 6:
            self.player_counter = not self.player_counter

# --- Flask wrapper ---
app = Flask(__name__)
game = Kalaha()
game.set_player_name('Julian', 'Matteo')

TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Kalaha</title>
  <style>
    body { font-family: sans-serif; text-align: center; }
    .turn { font-size: 1.2em; margin: 0.5em; }
    button { width: 40px; height: 40px; margin: 2px; }
  </style>
</head>
<body>
  <h1>Kalaha Game</h1>
  <div class="turn">
    Current Turn: <strong>{{ current_turn }}</strong>
  </div>
  <img src="data:image/png;base64,{{ board_img }}" alt="Board"/><br/>
  <form method="post" action="/play">
    {% for i in range(1,7) %}
      <button name="field" value="{{ i }}">{{ i }}</button>
    {% endfor %}
  </form>
  <form method="post" action="/reset">
    <button>Reset Game</button>
  </form>
</body>
</html>
'''

@app.route('/')
def index():
    board_img = game.display_board_image()
    current = game.player1_name if not game.player_counter else game.player2_name
    return render_template_string(TEMPLATE, board_img=board_img, current_turn=current)

@app.route('/play', methods=['POST'])
def play():
    field = int(request.form['field'])
    game.play(field)
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset():
    game.reset_game()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
