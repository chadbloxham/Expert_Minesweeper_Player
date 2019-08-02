# ======================================================================
# Student: Chad Bloxham
#
# Date of minimal submission: 11/4/2018
#
# Date of draft submission: 11/19/2018
#
# Date of final submission: 12/9/2018
#
# ======================================================================


"""

This file implements the class MyAI, which stores information regarding a
game of Minesweeper as it is being played.

The class function getAction() returns an instance of the Action class, which holds a move
(FLAG or UNCOVER or LEAVE) and a board position at which to perform the move.

In World.py, an instance of MyAI is declared and getAction() is repeatedly called in the 
class function run() until it returns a losing move (a mine is uncovered) or returns 
the move LEAVE.

In Main.py, an instance of World is declared (creating an initialzied board) 
and run() is called on the declared World. The board is outputted to the command
line with the most recent move represented if the proper arguments are inputted.

"""

from AI import AI
from Action import Action
import numpy as np
from itertools import combinations

class MyAI( AI ):

	def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
		self.totalMines = totalMines
		"""
		self.workingBoard will be used to represent the current state of
		the board.

		-2 = covered tile which is not flagged.
		-1 = covered tile which is flagged.
		0...8 = uncovered tile with hint revealing number of surrounding mines.

		Before the game begins, every tile is covered and not flagged.
		"""		
		self.workingBoard = np.zeros((colDimension, rowDimension)) - 2
		
		"""
		self.lastIndices will store the position of the last returned move.
		We need it to update the state of the board as the game progresses.
		"""
		self.lastIndices = [startX, startY]

		"""
		self.safeTiles and self.mineTiles will be filled with positions of
		tiles which do not contain mines and tiles which do, respectively.
		The helper functions will use the current state of the board to
		determine these positions.
		"""
		self.safeTiles = []
		self.mineTiles = []
		pass

		
	def getAction(self, number: int) -> "Action Object":

		# update working board with newest hint
		self.workingBoard[self.lastIndices[0], self.lastIndices[1]] = number
		
		# return a move if there are safe positions or mine positions
		if len(self.mineTiles) != 0:
			c = self.mineTiles[0][0]
			r = self.mineTiles[0][1]
			self.lastIndices = self.mineTiles[0]
			self.mineTiles.pop(0)
			return Action(AI.Action.FLAG, c, r)

		if len(self.safeTiles) != 0:
			c = self.safeTiles[0][0]
			r = self.safeTiles[0][1]
			self.lastIndices = self.safeTiles[0]
			self.safeTiles.pop(0)
			return Action(AI.Action.UNCOVER, c, r)
 
		# otherwise, call the helper functions until a safe or mine position is found
		moveFound = False
		self.safeTiles, self.mineTiles = board_comparisons(self.workingBoard)
		if len(self.safeTiles) != 0 or len(self.mineTiles) != 0:
			moveFound = True
		if not moveFound:
			self.safeTiles, self.mineTiles = eqn_solve(self.workingBoard)
			if len(self.safeTiles) != 0 or len(self.mineTiles) != 0:
				moveFound = True
		if not moveFound:
			self.safeTiles, self.mineTiles = mine_probs(self.workingBoard)
		
		if len(self.mineTiles) != 0:
			c = self.mineTiles[0][0]
			r = self.mineTiles[0][1]
			self.lastIndices = self.mineTiles[0]
			self.mineTiles.pop(0)
			return Action(AI.Action.FLAG, c, r)

		if len(self.safeTiles) != 0:
			c = self.safeTiles[0][0]
			r = self.safeTiles[0][1]
			self.lastIndices = self.safeTiles[0]
			self.safeTiles.pop(0)
			return Action(AI.Action.UNCOVER, c, r)

		# if the helper functions returned nothing, see if we have won
		numCoveredTiles = get_num_covered(self.workingBoard)
		if numCoveredTiles == self.totalMines:
			return Action(AI.Action.LEAVE)
		else: # we must make a guess
			guess = guess_tile(self.workingBoard)
			self.lastIndices = guess
			c = guess[0]
			r = guess[1]
			return Action(AI.Action.UNCOVER, c, r)

"""

HELPER FUNCTIONS

"""

"""
Returns all in-bounds neighbors of a tile with column,row values [c,r].
Optional arguments for returning only flagged and/or covered neighbors
"""
def get_neighbors(workingBoard, c, r, flagged = False, cov = False):
	neighbors = []
	left = c-1
	right = c+1
	up = r+1
	down = r-1
	colDim = workingBoard.shape[0]
	rowDim = workingBoard.shape[1]
	# Boolean values to determine whether neighbors are in-bounds
	canMoveLeft = left >= 0
	canMoveRight = right <= colDim-1
	canMoveUp = up <= rowDim-1
	canMoveDown = down >= 0
	# if in-bounds, include in neighbor list
	if canMoveLeft:
		neighbors.append([left,r])
	if canMoveRight:
		neighbors.append([right,r])
	if canMoveUp:
		neighbors.append([c,up])
	if canMoveDown:
		neighbors.append([c,down])
	if canMoveLeft and canMoveUp:
		neighbors.append([left,up])
	if canMoveLeft and canMoveDown:
		neighbors.append([left,down])
	if canMoveRight and canMoveUp:
		neighbors.append([right,up])
	if canMoveRight and canMoveDown:
		neighbors.append([right,down])
	# return subset of neighbors if optional argument(s) are True
	flaggedNeigh = []
	covNeigh = []
	if flagged == True:
		for tile in neighbors:
			col = tile[0]
			row = tile[1]
			if workingBoard[col,row] == -1:
				flaggedNeigh.append(tile)
	if cov == True:
		for tile in neighbors:
			col = tile[0]
			row = tile[1]
			if workingBoard[col,row] == -2:
				covNeigh.append(tile)
	if flagged == True and cov == True:
		combined = flaggedNeigh + covNeigh
		return combined
	if flagged == True:
		return flaggedNeigh
	if cov == True:
		return covNeigh
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
def board_comparisons(workingBoard):
	safeTiles = []
	mineTiles = []
	moveFound = False
	c = 0
	r = 0
	colDim = workingBoard.shape[0]
	rowDim = workingBoard.shape[1]
	while not moveFound and c < colDim:
		#check for expansion around a zero
		if workingBoard[c, r] == 0:
			safeTiles = get_neighbors(workingBoard, c, r, cov = True)
		if len(safeTiles) != 0:
			moveFound = True
		else:
			flagCovNeigh = get_neighbors(workingBoard, c, r, cov = True, flagged = True)
			numFlagCov = len(flagCovNeigh)
		#check for tiles which must be mines
		if not moveFound and workingBoard[c,r] == numFlagCov:
			mineTiles = get_neighbors(workingBoard, c, r, cov = True)
		if len(mineTiles) != 0:
			moveFound = True
		else:
			flagNeigh = get_neighbors(workingBoard, c, r, flagged = True)
			numFlagged = len(flagNeigh)
		#check for tiles which must be safe
		if not moveFound and workingBoard[c,r] == numFlagged:
			safeTiles = get_neighbors(workingBoard, c, r, cov = True)
		if len(safeTiles) != 0:
			moveFound = True
		if not moveFound:
			r += 1
		if r == rowDim:
			r = 0
			c += 1
	return safeTiles, mineTiles


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
def eqn_solve(workingBoard):
	safeTiles = []
	mineTiles = []
	solved = False
	vertNeigh = False
	c = 0
	r = 0
	colDim = workingBoard.shape[0]
	rowDim = workingBoard.shape[1]
	while not solved and c < colDim:
		"""
		First we will iterate through uncovered horizontal neighbors. Once we have
		iterated through all pairs, vertNeigh = True and we iterate through all
		vertical neighbors before terminating.
		"""
		if vertNeigh:
			c2 = c
			r2 = r+1
		else:
			c2 = c+1
			r2 = r

		flaggedNeigh1 = get_neighbors(workingBoard, c, r, flagged = True)
		numFlagged1 = len(flaggedNeigh1)
		flaggedNeigh2 = get_neighbors(workingBoard, c2, r2, flagged = True)
		numFlagged2 = len(flaggedNeigh2)

		minesLeft1 = workingBoard[c,r] - numFlagged1
		minesLeft2 = workingBoard[c2,r2] - numFlagged2
		const1 = workingBoard[c,r] > 0 and minesLeft1 > 0
		const2 = workingBoard[c2,r2] > 0 and minesLeft2 > 0
		"""
		In order to make valid equations each tile must be uncovered and
		have at least one unflagged mine in its neighbors
		"""
		if const1 and const2:
			safeTiles, mineTiles = reduce_eqn(workingBoard, c, r, c2, r2, minesLeft1, minesLeft2, vertNeigh)
				
		if len(safeTiles) != 0 or len(mineTiles) != 0:
			solved = True
		if not solved:
			r += 1
			if vertNeigh and r == rowDim - 1:
				r = 0
				c += 1
			elif r == rowDim:
				r = 0
				c += 1
				"""
				We have exhausted all horizontal neighbors.
				Restart iteration for vertical neighbors.
				"""
				if c == colDim - 1:
					vertNeigh = True
					r = 0
					c = 0
	return safeTiles, mineTiles


"""
Create the mine equations we will use to create the reduced equation. First we generate the
list of unique covered/non-flagged neighbors. A mine equation is a list consisting of 1's and 0's
corresponding to whether or not a tile in uniqueCov is a neighbor of the mine. The last 
element in a mine equation list is the right hand side of the equation i.e. the number of 
surrounding tiles which still need to be flagged.
"""
def reduce_eqn(workingBoard, c, r, c2, r2, minesLeft1, minesLeft2, vertNeigh):
	safeTiles = []
	mineTiles = []
	# create (unique) list of all neighbors
	covNeigh1 = get_neighbors(workingBoard, c, r, cov = True)
	covNeigh2 = get_neighbors(workingBoard, c2, r2, cov = True)
	uniqueCov = []
	for tile in covNeigh1:
		if tile not in uniqueCov:
			uniqueCov.append(tile)
	for tile in covNeigh2:
		if tile not in uniqueCov:
			uniqueCov.append(tile)
	xVals = [tile[0] for tile in uniqueCov]
	yVals = [tile[1] for tile in uniqueCov]
	dx = max(xVals) - min(xVals)
	dy = max(yVals) - min(yVals)
	if vertNeigh:
		constraint = dx == 0 and dy == len(uniqueCov)-1
	else:
		constraint = dy == 0 and dx == len(uniqueCov)-1
	"""
	Final constraint: tiles in uniqueCov are all touching and in
	the same row or column (once vertNeigh = True)
	"""
	if constraint:
		eqn1 = np.empty(len(uniqueCov)+1)
		eqn2 = np.empty(len(uniqueCov)+1)
		"""
		1 = tile appears in eqn
		0 = tile does not appear in eqn
		"""
		for tile in uniqueCov:
			if tile in covNeigh1:
				eqn1[uniqueCov.index(tile)] = 1
			else:
				eqn1[uniqueCov.index(tile)] = 0
			if tile in covNeigh2:
				eqn2[uniqueCov.index(tile)] = 1
			else:
				eqn2[uniqueCov.index(tile)] = 0
		eqn1[len(eqn1)-1] = minesLeft1
		eqn2[len(eqn2)-1] = minesLeft2
		reduced = eqn1 - eqn2
		redMax = 0
		redMin = redMax
		posOnes = []
		negOnes = []
		"""
		Find extrema of LHS. Mine variables can only take
		values of 0 or 1.
		"""
		for i in range(len(reduced)-1):
			if reduced[i] == 1:
				redMax += 1
				posOnes.append(i)
			elif reduced[i] == -1:
				redMin -= 1
				negOnes.append(i)
		if reduced[len(reduced)-1] == redMax:
			for i in posOnes:
				mineTiles.append(uniqueCov[i])
			for i in negOnes:
				safeTiles.append(uniqueCov[i])
		elif reduced[len(reduced)-1] == redMin:
			for i in posOnes:
				safeTiles.append(uniqueCov[i])
			for i in negOnes:
				mineTiles.append(uniqueCov[i])
	return safeTiles, mineTiles


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
def mine_probs(workingBoard):
	safeTiles = []
	mineTiles = []
	# generate list of combinations use to create mine configs
	# also generate uniqueCov and equations of identified tile
	allCombos, eqns, uniqueCov = generate_mine_combos(workingBoard)
	numConfigs = 1
	for combos in allCombos:
		numConfigs *= len(combos)
	if len(uniqueCov) > 0 and numConfigs < 50000: # in order to be computationally feasible
		# for each mine config, test if it satisfies all equations and calculate mineProbs
		safeTiles, mineTiles = sat_checking(workingBoard, allCombos, eqns, uniqueCov)
	return safeTiles, mineTiles


"""
Generate the combinations of possible positions for the unflagged mines surrounding each relevant 
uncovered tile. Also store positions of covered neighbors and create equations to be used in
mine configuration satisfaction checking.
"""
def generate_mine_combos(workingBoard):
	allCombos = []
	eqns = []
	uniqueCov = []
	colDim = workingBoard.shape[0]
	rowDim = workingBoard.shape[1]
	for c in range(colDim):
		for r in range(rowDim):
			flaggedNeigh = get_neighbors(workingBoard, c, r, flagged = True)
			numFlagged = len(flaggedNeigh)
			minesLeft = workingBoard[c,r] - numFlagged
			# must be uncovered and have unflagged mines
			if workingBoard[c,r] > 0 and minesLeft > 0:
				neighbors = get_neighbors(workingBoard, c, r)
				eqn = neighbors
				eqn.append(workingBoard[c,r])
				eqns.append(eqn)
				covNeigh = get_neighbors(workingBoard, c, r, cov = True)
				for tile in covNeigh:
					if tile not in uniqueCov:
						uniqueCov.append(tile)
				combos = list(combinations(covNeigh, int(minesLeft)))
				allCombos.append(combos)
	return allCombos, eqns, uniqueCov


"""
Iterate through all mine configurations. For each configuration, iterate through all equations
and make sure that the configuration is consistent with the hint numbers on the board.
"""
def sat_checking(workingBoard, allCombos, eqns, uniqueCov):
	colDim = workingBoard.shape[0]
	rowDim = workingBoard.shape[1]
	safeTiles = []
	mineTiles = []
	mineProbs = [0 for i in range(len(uniqueCov))]
	inds = [0 for i in range(len(allCombos))] # index for each list of combination
	allConfigsMade = False
	numSatConfigs = 0
	while not allConfigsMade:
		# create the mine configuration
		mineConfig = []
		for i in range(len(allCombos)):
			mineConfig.append(allCombos[i][inds[i]])
		"""
		create the mine grid by including already flagged mines and those
		included by the configuration
		"""
		mineGrid = np.zeros((colDim, rowDim))
		for c in range(colDim):
			for r in range(rowDim):
				if workingBoard[c,r] == -1:
					mineGrid[c,r] = 1
		for combo in mineConfig:
			for tile in combo:
				c = tile[0]
				r = tile[1]
				mineGrid[c, r] = 1
		# satisfaction checking
		satConfig = True
		eqnNum = 0
		while satConfig and eqnNum < len(eqns):
			mineSum = 0
			eqn = eqns[eqnNum]
			# count number of surrounding mines
			for i in range(len(eqn)-1):
				c = eqn[i][0]
				r = eqn[i][1]
				mineSum += mineGrid[c,r]
			# if number of mines is same as hint, eqn is satisfied
			if mineSum == eqn[len(eqn)-1]:
				eqnNum += 1
			else:
				satConfig = False
		"""
		If all equations are satisfied, increment the count of positions
		which appear in this configuration.
		"""
		if satConfig:
			numSatConfigs += 1
			for i in range(len(uniqueCov)):
				c = uniqueCov[i][0]
				r = uniqueCov[i][1]
				if mineGrid[c,r] == 1:
					mineProbs[i] += 1
		"""
		To create the next configuration, update the index into each list of
		combinations. We will perform a kind of backtracking method once an index
		or multiple indices reach their limit. Once all indices have, we have made
		all configurations.
		"""
		j = len(inds)-1 # index corresponding to a list of position combinations
		while inds[j] + 1 == len(allCombos[j]) and not allConfigsMade:
			if j == 0:
				allConfigsMade = True
			else:
				j -= 1
		# we found an index that can be incremented. Subsequent lists start over
		inds[j] += 1 
		for i in range(j+1, len(inds)):
			inds[i] = 0
	# probability 1.0 tiles are mines and 0.0 tiles are safe
	for i in range(len(mineProbs)):
		mineProbs[i] /= numSatConfigs
		if mineProbs[i] == 1.0:
			mineTiles.append(uniqueCov[i])
		elif mineProbs[i] == 0.0:
			safeTiles.append(uniqueCov[i])
	return safeTiles, mineTiles


"""
Iterate through board and count the number of covered
tiles, both flagged and unflagged.
"""
def get_num_covered(workingBoard):
	coveredTiles = 0
	colDim = workingBoard.shape[0]
	rowDim = workingBoard.shape[1]
	for c in range(colDim):
		for r in range(rowDim):
			if workingBoard[c,r] < 0:
				coveredTiles += 1
	return coveredTiles


"""
Iterate through board until a covered, non-flagged tile is
found and return this to be used as a guess.
"""
def guess_tile(workingBoard):
	guess = []
	guessFound = False
	c = 0
	r = 0
	colDim = workingBoard.shape[0]
	rowDim = workingBoard.shape[1]
	while not guessFound and c < colDim:
		if workingBoard[c,r] == -2:
			guess = [c,r]
			guessFound = True
		if not guessFound:
			r += 1
		if r == rowDim:
			r = 0
			c += 1
	return guess
