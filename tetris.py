import pygame
import random
import sqlite3
import time

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 300
SCREEN_HEIGHT = 600
BLOCK_SIZE = 30

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Shapes and their rotations
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1], [1, 1]],  # O
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]],  # Z
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]]   # J
]

SHAPE_COLORS = [CYAN, MAGENTA, YELLOW, GREEN, RED, ORANGE, BLUE]

class Tetris:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.level = 1
        self.font = pygame.font.SysFont('Arial', 24)
        self.game_over_font = pygame.font.SysFont('Arial', 48)
        self.conn = sqlite3.connect('tetris_scores.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY, score INTEGER)''')
        self.conn.commit()

    def new_piece(self):
        shape = random.choice(SHAPES)
        color = random.choice(SHAPE_COLORS)
        return {
            'shape': shape,
            'color': color,
            'x': self.width // 2 - len(shape[0]) // 2,
            'y': 0
        }

    def valid_move(self, piece, x, y):
        for i, row in enumerate(piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    new_x = x + j
                    new_y = y + i
                    if new_x < 0 or new_x >= self.width or new_y >= self.height or (new_y >= 0 and self.grid[new_y][new_x]):
                        return False
        return True

    def place_piece(self):
        for i, row in enumerate(self.current_piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    self.grid[self.current_piece['y'] + i][self.current_piece['x'] + j] = self.current_piece['color']
        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        if not self.valid_move(self.current_piece, self.current_piece['x'], self.current_piece['y']):
            self.game_over = True
            self.save_score()

    def clear_lines(self):
        lines_cleared = 0
        new_grid = [row for row in self.grid if not all(row)]
        lines_cleared = self.height - len(new_grid)
        self.grid = [[0 for _ in range(self.width)] for _ in range(lines_cleared)] + new_grid
        self.score += lines_cleared ** 2 * 100
        self.level = 1 + self.score // 1000

    def move(self, dx):
        new_x = self.current_piece['x'] + dx
        if self.valid_move(self.current_piece, new_x, self.current_piece['y']):
            self.current_piece['x'] = new_x

    def rotate(self):
        piece = self.current_piece
        new_shape = [list(row) for row in zip(*piece['shape'][::-1])]
        if self.valid_move({'shape': new_shape, 'x': piece['x'], 'y': piece['y']}, piece['x'], piece['y']):
            self.current_piece['shape'] = new_shape

    def drop(self):
        while self.valid_move(self.current_piece, self.current_piece['x'], self.current_piece['y'] + 1):
            self.current_piece['y'] += 1
        self.place_piece()

    def update(self):
        if not self.game_over:
            if self.valid_move(self.current_piece, self.current_piece['x'], self.current_piece['y'] + 1):
                self.current_piece['y'] += 1
            else:
                self.place_piece()

    def draw(self, screen):
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x]:
                    pygame.draw.rect(screen, self.grid[y][x], (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
        if self.current_piece:
            for i, row in enumerate(self.current_piece['shape']):
                for j, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(screen, self.current_piece['color'], ((self.current_piece['x'] + j) * BLOCK_SIZE, (self.current_piece['y'] + i) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
        # Draw the vertical line
        pygame.draw.line(screen, WHITE, (self.width * BLOCK_SIZE, 0), (self.width * BLOCK_SIZE, SCREEN_HEIGHT), 2)
        # Draw the next piece
        for i, row in enumerate(self.next_piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, self.next_piece['color'], ((self.width + j + 1) * BLOCK_SIZE, (i + 1) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
        # Draw the score
        score_text = self.font.render(f'Score: {self.score}', True, WHITE)
        screen.blit(score_text, (10, 10))
        # Draw the level
        level_text = self.font.render(f'Level: {self.level}', True, WHITE)
        screen.blit(level_text, (10, 40))
        # Draw the game over screen
        if self.game_over:
            game_over_text = self.game_over_font.render('Game Over', True, RED)
            screen.blit(game_over_text, (self.width * BLOCK_SIZE // 2 - game_over_text.get_width() // 2, self.height * BLOCK_SIZE // 2 - game_over_text.get_height() // 2))
            top_scores = self.get_top_scores()
            for index, score in enumerate(top_scores):
                score_text = self.font.render(f'{index + 1}. {score}', True, WHITE)
                screen.blit(score_text, (self.width * BLOCK_SIZE // 2 - score_text.get_width() // 2, self.height * BLOCK_SIZE // 2 + game_over_text.get_height() // 2 + 30 * (index + 1)))

    def save_score(self):
        self.cursor.execute('INSERT INTO scores (score) VALUES (?)', (self.score,))
        self.conn.commit()

    def get_top_scores(self):
        self.cursor.execute('SELECT score FROM scores ORDER BY score DESC LIMIT 5')
        return [row[0] for row in self.cursor.fetchall()]

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH + 150, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    game = Tetris(SCREEN_WIDTH // BLOCK_SIZE, SCREEN_HEIGHT // BLOCK_SIZE)

    fall_time = 0
    fall_speed = 1000  # Milliseconds

    while not game.game_over:
        screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    game.move(-1)
                if event.key == pygame.K_RIGHT:
                    game.move(1)
                if event.key == pygame.K_DOWN:
                    game.drop()
                if event.key == pygame.K_UP:
                    game.rotate()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN]:
            fall_speed = 100
        else:
            fall_speed = 1000 - (game.level - 1) * 100

        fall_time += clock.get_rawtime()
        clock.tick()

        if fall_time >= fall_speed:
            game.update()
            fall_time = 0

        game.draw(screen)
        pygame.display.flip()

    # Persist the game over screen for three seconds
    game.draw(screen)
    pygame.display.flip()
    time.sleep(3)
    pygame.quit()

if __name__ == "__main__":
    main()