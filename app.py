from flask import Flask, render_template_string, request, redirect, url_for
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

class Kalaha:
    def __init__(self, start_number=6, play_timer=0):
        self.play_timer = play_timer
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
        self.player_counter = False

    def set_player_name(self, player1, player2):
        self.player1_name = player1
        self.player2_name = player2

    def reset_game(self, start_number=6):
        self.__init__(start_number, self.play_timer)

    def display_board_image(self):
        fig, ax = plt.subplots(figsize=(6, 3))
        for r in [0, 1]:
            for c in range(6):
                ax.text(c, 1 - r, str(self.board[r, c]), ha='center', va='center', fontsize=14)
        ax.text(6, 1, str(self.s2_points), ha='center', va='center', fontsize=16, fontweight='bold')
        ax.text(6, 0, str(self.s1_points), ha='center', va='center', fontsize=16, fontweight='bold')
        ax.set_xlim(-0.5, 6.5)
        ax.set_ylim(-0.5, 1.5)
        ax.axis('off')
        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('ascii')

    def play(self, field_input):
        field_input -= 1
        row = 0 if not self.player_counter else 1
        if self.board[row, field_input] == 0:
            return
        n_stones = self.board[row, field_input]
        self.board[row, field_input] = 0
        idx = field_input
        current_row = row
        while n_stones > 0:
            idx += 1
            if idx == 6:
                if (current_row == 0 and not self.player_counter) or (current_row == 1 and self.player_counter):
                    if current_row == 0:
                        self.s1_points += 1
                    else:
                        self.s2_points += 1
                    n_stones -= 1
                current_row = 1 - current_row
                idx = -1
                continue
            self.board[current_row, idx] += 1
            n_stones -= 1
        self.player_counter = not self.player_counter

app = Flask(__name__)
game = Kalaha()
game.set_player_name('Julian', 'Matteo')

tmpl = '''<!doctype html>
<html lang="en">
  <head><meta charset="utf-8"><title>Kalaha</title></head>
  <body>
    <h1>Kalaha Game</h1>
    <img src="data:image/png;base64,{{ board_img }}"/>
    <form method="post" action="/play">
      {% for i in range(1,7) %}<button name="field" value="{{ i }}">{{ i }}</button>{% endfor %}
    </form>
    <form method="post" action="/reset"><button>Reset</button></form>
  </body>
</html>'''

@app.route('/')
def index():
    img = game.display_board_image()
    return render_template_string(tmpl, board_img=img)

@app.route('/play', methods=['POST'])
def play():
    game.play(int(request.form['field']))
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset():
    game.reset_game()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
