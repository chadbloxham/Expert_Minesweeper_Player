import random
import time
from ms_player import *

class tile():
    mine = False
    hint_num = 0

class player_tile():
    hint_num = None
    flag = False
    retired = False

def create_board(num_mines, num_rows, num_cols):
    # the board is just an array of tiles
    board = []
    for i in range(num_rows):
        board_row = []
        for j in range(num_cols):
            board_row.append(tile())
        board.append(board_row)

    while num_mines > 0:
        rand_row = random.randint(0, num_rows-1)
        rand_col = random.randint(0, num_cols-1)
        if board[rand_row][rand_col].mine == False:
            board[rand_row][rand_col].mine = True
        num_mines -= 1
    for i in range(num_rows):
        for j in range(num_cols):
            hint_num = 0
            above = i-1
            below = i+1
            left = j-1
            right = j+1
            above_available = above >= 0
            below_available = below <= num_rows-1
            left_available = left >= 0
            right_available = right <= num_cols-1
            if above_available:
                if board[above][j].mine == True:
                    hint_num += 1
            if below_available:
                if board[below][j].mine == True:
                    hint_num += 1
            if left_available:
                if board[i][left].mine == True:
                    hint_num += 1
            if right_available:
                if board[i][right].mine == True:
                    hint_num += 1
            if above_available and left_available:
                if board[above][left].mine == True:
                    hint_num += 1
            if above_available and right_available:
                if board[above][right].mine == True:
                    hint_num += 1
            if below_available and left_available:
                if board[below][left].mine == True:
                    hint_num += 1
            if below_available and right_available:
                if board[below][right].mine == True:
                    hint_num += 1
            board[i][j].hint_num = hint_num
    return board

def create_player_board(num_rows = 8, num_cols = 8):
    player_board = []
    for i in range(num_rows):
        board_row = []
        for j in range(num_cols):
            board_row.append(player_tile())
        player_board.append(board_row)
    return player_board

# expert world
num_rows = 16
num_cols = 30
num_mines = 99

# beginner world
# num_rows = 8
# num_cols = 8
# num_mines = 10

board = create_board(num_mines = num_mines, num_rows = num_rows, num_cols = num_cols)
player_board = create_player_board(num_rows = num_rows, num_cols = num_cols)
"""first move is given so that you can't lose immediately"""
rand_row = random.randint(0, num_rows-1)
rand_col = random.randint(0, num_cols-1)
while board[rand_row][rand_col].mine != False:
    rand_row = random.randint(0, num_rows-1)
    rand_col = random.randint(0, num_cols-1)
player_board[rand_row][rand_col].hint_num = board[rand_row][rand_col].hint_num

game_over = False
while not game_over:
    moves, retired_tiles = find_moves(player_board)
    print('Moves: ', moves)
    for move in moves:
        move_row = move[0]
        move_col = move[1]
        move_type = move[2]
        if move_type == 'uncover':
            # if we uncover a mine, the game is over
            if board[move_row][move_col].mine == True:
                game_over = True
                print('You lost :(')
            else:
                player_board[move_row][move_col].hint_num = board[move_row][move_col].hint_num
        elif move_type == 'flag':
            player_board[move_row][move_col].flag = True

    for i in range(num_rows):
        row_str = ''
        for j in range(num_cols):
            if player_board[i][j].hint_num is None:
                if game_over == True and i == move_row and j == move_col:
                    row_str += ' * '
                elif player_board[i][j].flag == True:
                    row_str += ' F '
                else:
                    row_str += ' . '
            else:
                row_str += ' ' + str(player_board[i][j].hint_num) + ' '
        print(row_str)

    for retired_tile in retired_tiles:
        player_board[retired_tile[0]][retired_tile[1]].retired = True

    unsolved_tiles = 0
    for i in range(num_rows):
        for j in range(num_cols):
            if player_board[i][j].hint_num is None and player_board[i][j].flag == False:
                unsolved_tiles += 1

    if unsolved_tiles == 0:
        game_over = True
        print('You won!')
    time.sleep(0.1)
