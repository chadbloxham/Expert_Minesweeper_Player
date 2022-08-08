import numpy as np
from itertools import combinations
import random

def find_moves(player_board):
	moves, retired = simple_comparisons(player_board)
	if moves:
		print('comparison')
		return moves, retired
	moves, retired = pattern_finder(player_board)
	if moves:
		print('pattern')
		return moves, retired
	moves, retired = mine_probs(player_board)
	if moves:
		print('probs')
		return moves, retired
	move = guess_uncover(player_board)
	print('Need to guess :(')
	return [move], []

def get_covered_neighbors(i, j, player_board):
	num_rows = len(player_board)
	num_cols = len(player_board[0])
	above = i-1
	below = i+1
	left = j-1
	right = j+1
	above_available = above >= 0
	below_available = below <= num_rows-1
	left_available = left >= 0
	right_available = right <= num_cols-1
	neighbors = []
	if above_available and player_board[above][j].hint_num is None:
		neighbors.append([above, j])
	if below_available and player_board[below][j].hint_num is None:
		neighbors.append([below, j])
	if left_available and player_board[i][left].hint_num is None:
		neighbors.append([i, left])
	if right_available and player_board[i][right].hint_num is None:
		neighbors.append([i, right])
	if above_available and left_available and player_board[above][left].hint_num is None:
		neighbors.append([above, left])
	if above_available and right_available and player_board[above][right].hint_num is None:
		neighbors.append([above, right])
	if below_available and left_available and player_board[below][left].hint_num is None:
		neighbors.append([below, left])
	if below_available and right_available and player_board[below][right].hint_num is None:
		neighbors.append([below, right])
	return neighbors

"""
Iterates through the current state of the board searching for an instance of 1 of
3 scenarios:

(1) The hint number is 0, indicating that all neighbor tiles are safe.

(2) The hint number is equal to the number of flagged neighbors, indicating that
all other neighbors are safe.

(3) The hint number is equal to the number of covered neighbors, indicating that
all covered neighbors are mines.
"""

def simple_comparisons(player_board):
	num_rows = len(player_board)
	num_cols = len(player_board[0])
	moves = []
	retired = []
	for i in range(num_rows):
		for j in range(num_cols):
			hint_num = player_board[i][j].hint_num
			if hint_num is not None and player_board[i][j].retired == False:
				neighbors = get_covered_neighbors(i, j, player_board)
				num_covered = len(neighbors)
				flag_neigh = []
				for neighbor in neighbors:
					if player_board[neighbor[0]][neighbor[1]].flag == True:
						flag_neigh.append(neighbor)
				num_flagged = len(flag_neigh)
				if hint_num - num_flagged == 0:
					if [i,j] not in retired:
						retired.append([i, j])
					for neighbor in neighbors:
						if neighbor not in flag_neigh:
							if [neighbor[0], neighbor[1], 'uncover'] not in moves:
								moves.append([neighbor[0], neighbor[1], 'uncover'])
				elif hint_num - num_covered == 0:
					if [i, j] not in retired:
						retired.append([i, j])
					for neighbor in neighbors:
						if neighbor not in flag_neigh:
							if [neighbor[0], neighbor[1], 'flag'] not in moves:
								moves.append([neighbor[0], neighbor[1], 'flag'])
							if [neighbor[0], neighbor[1]] not in retired:
								retired.append([neighbor[0], neighbor[1]])
	return moves, retired

"""
def simple_comparisons(player_board):
	num_rows = len(player_board)
	num_cols = len(player_board[0])
	moves = []
	retired = []
	for i in range(num_rows):
		for j in range(num_cols):
			neighbors = get_covered_neighbors(i, j, player_board)
			num_covered = len(neighbors)
			if player_board[i][j].hint_num is not None and player_board[i][j].retired == False:
				hint_num = player_board[i][j].hint_num
				flag_neigh = []
				for neighbor in neighbors:
					if player_board[neighbor[0]][neighbor[1]].flag == True:
						flag_neigh.append(neighbor)
				num_flagged = len(flag_neigh)
				if hint_num - num_flagged == 0:
					retired.append([i, j])
					for neighbor in neighbors:
						if neighbor not in flag_neigh:
							moves.append([neighbor[0], neighbor[1], 'uncover'])
				if hint_num - num_covered == 0:
					retired.append([i, j])
					for neighbor in neighbors:
						if neighbor not in flag_neigh:
							moves.append([neighbor[0], neighbor[1], 'flag'])
							# Can't we automatically retire flagged tiles?
							retired.append([neighbor[0], neighbor[1]])
	return moves, retired
"""

def guess_uncover(player_board):
	num_rows = len(player_board)
	num_cols = len(player_board[0])
	rand_row = random.randint(0, num_rows-1)
	rand_col = random.randint(0, num_cols-1)
	covered = player_board[rand_row][rand_col].hint_num is None
	flagged = player_board[rand_row][rand_col].flag == True
	while not (covered and not flagged):
		rand_row = random.randint(0, num_rows-1)
		rand_col = random.randint(0, num_cols-1)
		covered = player_board[rand_row][rand_col].hint_num is None
		flagged = player_board[rand_row][rand_col].flag == True
	return [rand_row, rand_col, 'uncover']

"""
Iterates through the current state of the board and creates the mine equations for consecutive
uncovered tiles (touching in same row or same column). Creates a "reduced" equation by subtracting
one equation from the other. Computes the extrema of the left hand side of the equation by counting
the number of variables with coefficient 1 (the reduced max, redMax) as well as the number of variables
with coefficient -1 (the reduced min, redMin). If the right hand side of the equation is equal to redMax,
all coefficient 1 positions are mines and all coefficient -1 positions are safe. If the right hand
side is equal to redMin, the reverse is true.

As an example we examine the classic 1-2 formation. Say the bottom left corner of the board is an
uncovered 1 and directly to its right is an uncovered 2. The unique (no duplicates) combined list
of their covered/unflagged neighbors is:

uniqueCov = [ [1,2], [2,2], [3,2] ]

The mine equations for the uncovered 1 and uncovered 2 are respectively:

x_12 + x_22 + 0*x_32 = 1
x_12 + x_22 + x_32 = 2

Where each x variable can take the value 0 or 1. Subtracting the first equation from the second
gives the following reduced equation:

0*x_12 + 0*x_22 + x_32 = 1

redMax = 1 and redMin = 0. The right hand side is equal to redMax, so [3,2] is a mine.
"""
def pattern_finder(player_board):
	num_rows = len(player_board)
	num_cols = len(player_board[0])
	move_found = False
	all_checked = False
	moves = []
	retired_tiles = []
	vertical_checking = False
	i = 0
	j = 0
	while not move_found and not all_checked:
		"""
		First we will iterate through uncovered horizontal neighbors. Once we have
		iterated through all pairs, vertNeigh = True and we iterate through all
		vertical neighbors before terminating.
		"""
		if vertical_checking:
			i_2 = i+1
			j_2 = j
		else:
			i_2 = i
			j_2 = j+1

		if player_board[i][j].retired == False and player_board[i_2][j_2].retired == False and player_board[i][j].hint_num is not None and player_board[i_2][j_2].hint_num is not None:
			neigh_1 = get_covered_neighbors(i, j, player_board)
			flag_neigh_1 = []
			for neighbor in neigh_1:
				if player_board[neighbor[0]][neighbor[1]].flag == True:
					flag_neigh_1.append(neighbor)
			num_flagged_1 = len(flag_neigh_1)

			neigh_2 = get_covered_neighbors(i_2, j_2, player_board)
			flag_neigh_2 = []
			for neighbor in neigh_2:
				if player_board[neighbor[0]][neighbor[1]].flag == True:
					flag_neigh_2.append(neighbor)
			num_flagged_2 = len(flag_neigh_2)

			mines_left_1 = player_board[i][j].hint_num - num_flagged_1
			mines_left_2 = player_board[i_2][j_2].hint_num - num_flagged_2

			if mines_left_1 > 0 and mines_left_2 > 0:
				moves, retired_tiles = eqn_solve(player_board, i, j, i_2, j_2, mines_left_1, mines_left_2, vertical_checking)
			if moves:
				move_found = True

		if not move_found:
			j += 1
			if not vertical_checking and j == num_cols-1:
				j = 0
				i += 1
				if i == num_rows:
					vertical_checking = True
					i = 0
					j = 0
			elif vertical_checking and j == num_cols:
				j = 0
				i += 1
				if i == num_rows-1:
					all_checked = True
	return moves, retired_tiles


"""
Create the mine equations we will use to create the reduced equation. First we generate the
list of unique covered/non-flagged neighbors. A mine equation is a list consisting of 1's and 0's
corresponding to whether or not a tile in uniqueCov is a neighbor of the mine. The last
element in a mine equation list is the right hand side of the equation i.e. the number of
surrounding tiles which still need to be flagged.
"""
def eqn_solve(player_board, i, j, i_2, j_2, mines_left_1, mines_left_2, vertical_checking):
	moves = []
	retired_tiles = []
	neigh_1 = get_covered_neighbors(i, j, player_board)
	non_flagged_1 = []
	for neighbor in neigh_1:
		if player_board[neighbor[0]][neighbor[1]].flag == False:
			non_flagged_1.append(neighbor)
	neigh_2 = get_covered_neighbors(i_2, j_2, player_board)
	non_flagged_2 = []
	for neighbor in neigh_2:
		if player_board[neighbor[0]][neighbor[1]].flag == False:
			non_flagged_2.append(neighbor)
	unique_neigh = []
	for tile in non_flagged_1:
		if tile not in unique_neigh:
			unique_neigh.append(tile)
	for tile in non_flagged_2:
		if tile not in unique_neigh:
			unique_neigh.append(tile)
	neigh_i_vals = [tile[0] for tile in unique_neigh]
	neigh_j_vals = [tile[1] for tile in unique_neigh]
	delta_i = max(neigh_i_vals) - min(neigh_i_vals)
	delta_j = max(neigh_j_vals) - min(neigh_j_vals)
	if vertical_checking:
		constraint = delta_j == 0 and delta_i == len(unique_neigh)-1
	else:
		constraint = delta_i == 0 and delta_j == len(unique_neigh)-1
	"""
	Final constraint: tiles in uniqueCov are all touching and in
	the same row or column (once vertNeigh = True)
	"""
	if constraint:
		eqn_1 = np.empty(len(unique_neigh)+1)
		eqn_2 = np.empty(len(unique_neigh)+1)
		"""
		1 = tile appears in eqn
		0 = tile does not appear in eqn
		"""
		for tile in unique_neigh:
			if tile in neigh_1:
				eqn_1[unique_neigh.index(tile)] = 1
			else:
				eqn_1[unique_neigh.index(tile)] = 0
			if tile in neigh_2:
				eqn_2[unique_neigh.index(tile)] = 1
			else:
				eqn_2[unique_neigh.index(tile)] = 0
		eqn_1[len(eqn_1)-1] = mines_left_1
		eqn_2[len(eqn_2)-1] = mines_left_2
		reduced_eqn = eqn_1 - eqn_2
		reduced_max = 0
		reduced_min = 0
		pos_coeffs = []
		neg_coeffs = []
		"""
		Find extrema of LHS. Mine variables can only take
		values of 0 or 1.
		"""
		for i in range(len(reduced_eqn)-1):
			if reduced_eqn[i] == 1:
				reduced_max += 1
				pos_coeffs.append(i)
			elif reduced_eqn[i] == -1:
				reduced_min -= 1
				neg_coeffs.append(i)
		if reduced_eqn[len(reduced_eqn)-1] == reduced_max:
			for i in pos_coeffs:
				moves.append([unique_neigh[i][0], unique_neigh[i][1], 'flag'])
				retired_tiles.append([unique_neigh[i][0], unique_neigh[i][1]])
			for i in neg_coeffs:
				moves.append([unique_neigh[i][0], unique_neigh[i][1], 'uncover'])
		elif reduced_eqn[len(reduced_eqn)-1] == reduced_min:
			for i in pos_coeffs:
				moves.append([unique_neigh[i][0], unique_neigh[i][1], 'uncover'])
			for i in neg_coeffs:
				moves.append([unique_neigh[i][0], unique_neigh[i][1], 'flag'])
				retired_tiles.append([unique_neigh[i][0], unique_neigh[i][1]])
	return moves, retired_tiles


"""
Iterates through workingBoard and identify tiles which are uncovered and have surrounding non-flagged mines.
When one is found, we store:

(1) All combinations of the possible positions for its remaining surrounding mine(s).
(2) Its equation (list containing all neighbors and the hint number).
(3) Its covered and non-flagged neighbors (if they are not already in uniqueCov)

Mine configurations are created by choosing one of the combinations for each of the identified tiles.
For each mine configuration we create a "mine board" (1 if a mine position, 0 otherwise) and iterate
through the stored equations to determine whether a given mine configuration satisfies all equations
or it is not a possible configuration. We keep a count of how often each mine in uniqueCov appears in
a satisfying configuration. After normalizing the counts by the total number of satisfying configurations,
we have the probability that each tile in uniqueCov is a mine. If a probability is 1.0, we flag that
position. If a probability is 0.0, we uncover that position.
"""
def mine_probs(player_board):
	moves = []
	retired_tiles = []
	all_local_mine_configs = generate_mine_combos(player_board)
	all_configs_num = 1
	for local_mine_config in all_local_mine_configs:
		all_configs_num *= len(local_mine_config)
	print(all_configs_num)
	if all_configs_num < 500000: # for time and memory purposes. Can adjust based on machine code is being run on
		# for each mine config, test if it satisfies all equations and calculate mineProbs
		moves, retired_tiles = config_validation_checking(player_board, all_local_mine_configs)
	return moves, retired_tiles


"""
Generate the combinations of possible positions for the unflagged mines surrounding each relevant
uncovered tile. Also store positions of covered neighbors and create equations to be used in
mine configuration satisfaction checking.
"""
def generate_mine_combos(player_board):
	all_local_mine_configs = []
	num_rows = len(player_board)
	num_cols = len(player_board[0])
	for i in range(num_rows):
		for j in range(num_cols):
			if player_board[i][j].hint_num is not None and player_board[i][j].retired == False:
				neighbors = get_covered_neighbors(i, j, player_board)
				flag_neigh = []
				non_flag_neigh = []
				for neighbor in neighbors:
					if player_board[neighbor[0]][neighbor[1]].flag == True:
						flag_neigh.append(neighbor)
					else:
						non_flag_neigh.append(neighbor)
				mines_left = player_board[i][j].hint_num - len(flag_neigh)
				local_mine_configs_tup = combinations(non_flag_neigh, mines_left)
				local_mine_configs = []
				for local_mine_config in local_mine_configs_tup:
				    local_mine_configs.append(list(local_mine_config))
				all_local_mine_configs.append(local_mine_configs)

	return all_local_mine_configs


"""
Iterate through all mine configurations. For each configuration, iterate through all equations
and make sure that the configuration is consistent with the hint numbers on the board.
"""
def config_validation_checking(player_board, all_local_mine_configs):
	num_rows = len(player_board)
	num_cols = len(player_board[0])
	moves = []
	retired_tiles = []
	mine_probability = np.zeros((num_rows, num_cols))
	local_configs_indices = [0 for i in range(len(all_local_mine_configs))]
	all_global_configs_checked = False
	tot_valid_configs = 0
	i = len(all_local_mine_configs)-1
	all_global_unique = []
	while not all_global_configs_checked:
		global_mine_config = []
		for j in range(len(local_configs_indices)):
			global_mine_config.append(all_local_mine_configs[j][local_configs_indices[j]])
		# print('Not validated (yet)... ', global_mine_config)
		config_grid = np.zeros((num_rows, num_cols))
		for row in range(num_rows):
			for col in range(num_cols):
				if player_board[row][col].flag == True:
					config_grid[row][col] = 1
		for local_mine_config in global_mine_config:
			for mine_pos in local_mine_config:
				config_grid[mine_pos[0]][mine_pos[1]] = 1
		valid_global_config = True
		row = 0
		col = 0
		while valid_global_config and col < num_cols:
			if player_board[row][col].hint_num is not None and player_board[row][col].retired == False:
				above = row-1
				below = row+1
				left = col-1
				right = col+1
				above_available = above >= 0
				below_available = below <= num_rows-1
				left_available = left >= 0
				right_available = right <= num_cols-1
				num_surrounding_mines = 0
				if above_available and config_grid[above][col] == 1:
					num_surrounding_mines += 1
				if below_available and config_grid[below][col] == 1:
					num_surrounding_mines += 1
				if left_available and config_grid[row][left] == 1:
					num_surrounding_mines += 1
				if right_available and config_grid[row][right] == 1:
					num_surrounding_mines += 1
				if above_available and left_available and config_grid[above][left] == 1:
					num_surrounding_mines += 1
				if above_available and right_available and config_grid[above][right] == 1:
					num_surrounding_mines += 1
				if below_available and left_available and config_grid[below][left] == 1:
					num_surrounding_mines += 1
				if below_available and right_available and config_grid[below][right] == 1:
					num_surrounding_mines += 1
				if num_surrounding_mines != player_board[row][col].hint_num:
					valid_global_config = False
			row += 1
			if row == num_rows:
				row = 0
				col += 1

		if valid_global_config:
			# print('I feel validated... and gay!')
			tot_valid_configs += 1
			global_mine_config_unique = []
			for local_mine_config in global_mine_config:
				for mine_pos in local_mine_config:
					if [mine_pos[0], mine_pos[1]] not in global_mine_config_unique:
						global_mine_config_unique.append([mine_pos[0], mine_pos[1]])
					if [mine_pos[0], mine_pos[1]] not in all_global_unique:
						all_global_unique.append([mine_pos[0], mine_pos[1]])
			# print(global_mine_config_unique)
			for mine_pos in global_mine_config_unique:
				mine_probability[mine_pos[0]][mine_pos[1]] += 1

		while local_configs_indices[i] == len(all_local_mine_configs[i])-1 and not all_global_configs_checked:
			i -= 1
			if i < 0:
				all_global_configs_checked = True
		if not all_global_configs_checked:
			local_configs_indices[i] += 1
			for j in range(i+1, len(local_configs_indices)):
				local_configs_indices[j] = 0
				i = len(all_local_mine_configs)-1

	for pos in all_global_unique:
		row = pos[0]
		col = pos[1]
		mine_probability[row][col] /= tot_valid_configs
		# print(mine_probability[row][col])
		if mine_probability[row][col] == 0.0:
			print('gobble gobble')
			moves.append([row, col, 'uncover'])
		elif mine_probability[row][col] == 1.0:
			print('juwacogon')
			moves.append([row, col, 'flag'])
			retired_tiles.append([row, col])

	if not moves:
		print('bazooka')
		min_prob = 1.0
		min_prob_pos = []
		for pos in all_global_unique:
			row = pos[0]
			col = pos[1]
			if mine_probability[row][col] < min_prob:
				min_prob = mine_probability[row][col]
				min_prob_pos = [row, col]
		print(min_prob)
		if min_prob < 0.5:
			min_prob_row = min_prob_pos[0]
			min_prob_col = min_prob_pos[1]
			moves.append([min_prob_row, min_prob_col, 'uncover'])

	return moves, retired_tiles
