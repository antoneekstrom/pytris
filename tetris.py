from tetris_lib import Tetris
import sys

if len(sys.argv) == 3:
    Tetris.window_width, Tetris.window_height = int(sys.argv[1]), int(sys.argv[2])

Tetris.init()
Tetris().run()
