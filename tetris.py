import pygame
import sys
import random
import math


def create_matrix(w, h, val_fn):
    return [[val_fn(x, y) for x in range(w)] for y in range(h)]


class Mino:
    DOWN = (0, 1)

    @staticmethod
    def draw(screen, pos, size, color):
        r = pygame.Rect(pos[0], pos[1], size, size)
        pygame.draw.rect(screen, color, r)

    def __init__(self, pos, color):
        self.pos = pos
        self.move_pos = pos
        self.color = color
        self.frozen = False
        self.matrix = None

    def place(self, matrix):
        if self.matrix is None:
            self.matrix = matrix
        matrix.set(self.pos, self.make_cell())

    def move(self, direction):
        if self.matrix is None:
            return

        if self.pos != self.move_pos:
            return

        dx, dy = direction
        can = self.can_move(direction)
        if can:
            self.matrix.set(self.pos, None)
            self.move_pos = (self.pos[0] + dx, self.pos[1] + dy)
        return can

    def update(self):
        self.pos = self.move_pos
        self.matrix.set(self.pos, self.make_cell())

    def make_cell(self):
        return self.color, self.frozen

    def can_move(self, direction):
        if self.matrix is None:
            return

        dx, dy = direction
        cell = self.matrix.get((self.pos[0] + dx, self.pos[1] + dy))
        return cell is None or not cell[1]


class Tetromino:
    fall_speed = 400

    @staticmethod
    def rotate_structure_cc(structure):
        rotated = []
        for x in range(len(structure[0])):
            row = []
            for y in reversed(range(len(structure))):
                row.append(structure[y][x])
            rotated.append(row)
        return rotated

    @staticmethod
    def get_start_pos(structure):
        return math.floor(Tetris.matrix_width / 2) - math.floor(len(structure[0]) / 2), 0

    def __init__(self, piece, pos):
        self.type = piece[2]
        self.structure = piece[0]
        self.color = piece[1]
        self.minos = []
        self.frozen = False
        self.last_fall = 0
        self.pos = pos
        self.matrix = None
        self._create()

    def _create(self):
        structure = self.structure
        pos = self.pos
        color = self.color
        for y in range(len(structure)):
            for x in range(len(structure[0])):
                if structure[y][x] == 1:
                    self.minos.append(Mino((x + pos[0], y + pos[1]), color))

    def _destroy(self):
        self.clear()
        self.minos = []

    def clear(self):
        for mino in self.minos:
            mino.matrix.set(mino.pos, None)

    def place(self, matrix):
        self.matrix = matrix
        for mino in self.minos:
            mino.place(matrix)

    def move(self, direction):
        for mino in self.minos:
            if not mino.can_move(direction):
                return False

        self.pos = (self.pos[0] + direction[0], self.pos[1] + direction[1])
        for mino in self.minos:
            mino.move(direction)

        return True

    def update(self):
        if pygame.time.get_ticks() - self.last_fall >= Tetromino.fall_speed:
            self.fall()
            self.last_fall = pygame.time.get_ticks()
        for mino in self.minos:
            mino.update()

    def fall(self):
        if self.frozen:
            return False

        if not self.move(Mino.DOWN):
            self.freeze()
            return False

        return True

    def instant_fall(self):
        i = 0
        while self.fall():
            for mino in self.minos:
                mino.update()
            if i >= Tetris.matrix_height:
                break
            i += 1

    def rotate_cc(self):
        # rotate structure
        rotated = Tetromino.rotate_structure_cc(self.structure)

        # move tetromino back inside bounds (if neccessary), or abort rotation if other minos are in the way
        dx_outside, dy_outside = 0, 0
        for y in range(len(rotated)):
            for x in range(len(rotated[0])):
                abs_pos = (x + self.pos[0], y + self.pos[1])

                # check if colliding with other minos
                cell = self.matrix.get(abs_pos)
                if cell is not None and cell != Matrix.OUT_OF_BOUNDS and cell[1]:
                    return

                # check if outside and how far outside
                outside = not self.matrix.test_bounds(abs_pos)
                if outside:
                    if abs(x) > abs(dx_outside):
                        dx_outside = x
                    if abs(y) > abs(dy_outside):
                        dy_outside = y
        moved_pos = (self.pos[0] - dx_outside, self.pos[1])

        # remove from matrix
        self._destroy()

        # update position and rotation
        self.pos = moved_pos
        self.structure = rotated

        # add new structure to matrix
        self._create()

        # re-place tetromino
        for mino in self.minos:
            mino.place(self.matrix)

    def draw_landing_column(self, screen):
        xf, yf = Tetris.screen_scale_factor((self.matrix.width, self.matrix.height))
        rect = pygame.Rect(0, 0, len(self.structure[0]) * xf, Tetris.window_height)
        s = pygame.Surface((rect.width, rect.height))
        s.set_alpha(60)
        s.fill(Tetris.WHITE)
        screen.blit(s, (self.pos[0] * xf, 0))

    def draw(self, screen, pos, scale):
        for sy, row in enumerate(self.structure):
            for sx, cell in enumerate(row):
                if cell == 0:
                    continue
                x, y = (scale * sx) + pos[0], (scale * sy) + pos[1]
                Mino.draw(screen, (x, y), scale, self.color)

    def get_piece(self):
        return self.structure, self.color, self.type

    def get_width(self):
        return len(self.structure[0])

    def freeze(self):
        self.frozen = True
        for mino in self.minos:
            mino.frozen = True


class Matrix:
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"

    def __init__(self, w, h):
        self.width = w
        self.height = h
        self.cells = create_matrix(w, h, lambda x, y: None)

    def test_bounds(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def set(self, pos, val):
        if self.test_bounds(pos):
            self.cells[pos[1]][pos[0]] = val
        else:
            return Matrix.OUT_OF_BOUNDS

    def get(self, pos):
        if self.test_bounds(pos):
            return self.cells[pos[1]][pos[0]]
        else:
            return Matrix.OUT_OF_BOUNDS

    def cell_screen_rect(self, pos):
        m_size = (self.width, self.height)
        xf, yf = Tetris.screen_scale_factor(m_size)
        return pygame.Rect(pos[0] * xf, pos[1] * yf, xf, yf)

    def draw(self, screen):
        for cy in range(self.height):
            for cx in range(self.width):
                c_pos = (cx, cy)
                cell = self.get(c_pos)
                if cell is not None:
                    c_col, c_frozen = cell
                    c_rect = self.cell_screen_rect((cx, cy))
                    col = Tetris.BLACK if c_col is None else c_col
                    pygame.draw.rect(screen, col, c_rect)


class Tetris:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    BLUE = (3, 65, 174)
    GREEN = (114, 203, 59)
    YELLOW = (255, 213, 0)
    ORANGE = (255, 151, 28)
    RED = (255, 50, 19)
    LIGHT_BLUE = 0, 238, 255
    PURPLE = (171, 35, 235)

    FONT = None

    QUEUE_SIZE, QUEUE_VISIBLE_SIZE = 14, 5

    T_PIECE = [[0, 1, 0], [1, 1, 1]], PURPLE, "T_PIECE"
    L_PIECE = [[1, 0, 0], [1, 1, 1]], BLUE, "L_PIECE"
    L_PIECE_M = [[0, 0, 1], [1, 1, 1]], ORANGE, "L_PIECE_M"
    SQUARE_PIECE = [[1, 1], [1, 1]], YELLOW, "SQUARE_PIECE"
    LONG_PIECE = [[1], [1], [1], [1]], LIGHT_BLUE, "LONG_PIECE"
    ZIG_PIECE = [[0, 1, 1], [1, 1, 0]], GREEN, "ZIG_PIECE"
    ZIG_PIECE_M = [[1, 1, 0], [0, 1, 1]], RED, "ZIG_PIECE_M"

    ALL_PIECES = [T_PIECE, L_PIECE, L_PIECE_M, SQUARE_PIECE, LONG_PIECE, ZIG_PIECE, ZIG_PIECE_M]

    matrix_width, matrix_height = 10, 24
    window_width, window_height = 400, 960
    framerate = 30
    window_label = "Tetris"
    window_icon = "tetris-logo.png"

    @staticmethod
    def init():
        pygame.init()
        Tetris.FONT = pygame.font.SysFont("Monospace", 15)

    @staticmethod
    def screen_scale_factor(dim):
        x = (Tetris.window_width / dim[0])
        y = (Tetris.window_height / dim[1])
        return x, y

    @staticmethod
    def mouse_pos():
        x, y = pygame.mouse.get_pos()
        scale = Tetris.screen_scale_factor((Tetris.matrix_width, Tetris.matrix_height))
        x = math.floor(x / scale[0])
        y = math.floor(y / scale[1])
        return x, y

    def __init__(self):
        self.matrix = None
        self.items = None
        self.piece_queue = None
        self.piece_hold = None

        self.screen = None
        self.running = False
        self.clock = pygame.time.Clock()
        self.paused = True
        self.reset()

    def init_display(self):
        self.screen = pygame.display.set_mode((Tetris.window_width, Tetris.window_height))
        pygame.display.set_caption(Tetris.window_label)
        pygame.display.set_icon(pygame.image.load(Tetris.window_icon))

    def queue_count(self, piece):
        count = 0
        if piece is None:
            return count
        for tm in self.piece_queue:
            if tm.type == piece[2]:
                count += 1
        return count

    def make_piece(self):
        piece = None
        while piece is None or self.queue_count(piece) >= 2:
            piece = random.choice(Tetris.ALL_PIECES)
        return Tetromino(piece, Tetromino.get_start_pos(piece[0]))

    def get_piece(self):
        self.piece_queue.insert(0, self.make_piece())
        return self.piece_queue.pop()

    def complete_rows(self):
        for y, row in enumerate(self.matrix.cells):
            complete = True
            for cell in row:
                if cell is None:
                    complete = False
                    break
            if complete:
                self.matrix.cells.pop(y)
                self.matrix.cells.insert(0, [None for _ in range(self.matrix.width)])

    def draw_hud(self):
        # draw queue
        scale, padding, spacing = 12, 12, 6
        x_off = padding
        for i, piece in enumerate(reversed(self.piece_queue)):
            if i >= Tetris.QUEUE_VISIBLE_SIZE:
                break
            piece.draw(self.screen, (x_off, padding), scale)
            x_off += len(piece.structure[0]) * scale + spacing
        # draw hold
        if self.piece_hold is not None:
            self.piece_hold.draw(self.screen, (Tetris.window_width - padding - self.piece_hold.get_width() * scale, padding), scale)

    def reset(self):
        self.matrix = Matrix(Tetris.matrix_width, Tetris.matrix_height)
        self.piece_hold = None
        self.items = []
        self.piece_queue = []
        for i in range(1, Tetris.QUEUE_SIZE):
            self.piece_queue.append(self.make_piece())

    def run(self):
        self.init_display()
        self.running = True

        # main loop
        while self.running:
            # poll window events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if len(self.items) > 0:
                        if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                            self.items[0].move((-1, 0))
                        elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                            self.items[0].move((1, 0))
                        elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                            self.items[0].move(Mino.DOWN)
                        elif event.key == pygame.K_SPACE:
                            if len(self.items) > 0:
                                self.items[0].instant_fall()
                        elif event.key == pygame.K_w or event.key == pygame.K_UP:
                            self.items[0].rotate_cc()
                        elif event.key == pygame.K_c:
                            hold = self.piece_hold
                            self.piece_hold = self.items[0]
                            self.piece_hold.clear()
                            self.items.remove(self.piece_hold)
                            if hold is not None:
                                pos = Tetromino.get_start_pos(hold.structure)
                                hc = Tetromino(hold.get_piece(), pos)
                                hc.place(self.matrix)
                                self.items.append(hc)

                    if event.key == pygame.K_ESCAPE:
                        self.paused = not self.paused

            if self.paused:
                self.screen.fill(Tetris.BLACK)
                self.screen.blit(Tetris.FONT.render("PRESS ESCAPE", True, Tetris.WHITE), (0, 0))

                pygame.display.flip()
                self.clock.tick(Tetris.framerate)
                continue

            # spawn pieces
            if len(self.items) < 1:
                tm = self.get_piece()
                tm.place(self.matrix)
                self.items.append(tm)

            # update minos
            for item in self.items:
                item.update()
                if item.frozen:
                    self.items.remove(item)

            # remove complete rows
            self.complete_rows()

            # check lose
            for cell in self.matrix.cells[0]:
                if cell is not None and cell[1]:
                    self.paused = True
                    self.reset()

            # clear screen
            self.screen.fill(Tetris.BLACK)

            # draw landing
            if len(self.items) > 0:
                self.items[0].draw_landing_column(self.screen)
            # draw matrix
            self.matrix.draw(self.screen)
            # draw hud
            self.draw_hud()

            # draw screen
            pygame.display.flip()

            self.clock.tick(Tetris.framerate)
