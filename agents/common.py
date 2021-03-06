import numpy as np
from enum import Enum
from typing import Optional, Callable, Tuple
from gmpy2 import mpz, popcount, bit_test


# Initialize data types
Board = np.ndarray
BoardPiece = np.int8
PlayerAction = np.int
Bitmap = np.int

# Initialize constant variables
NO_PLAYER = BoardPiece(0)  # board[i, j] == NO_PLAYER where position is empty
PLAYER1 = BoardPiece(1)  # board[i, j] == PLAYER1 where player 1 has a piece
PLAYER2 = BoardPiece(2)  # board[i, j] == PLAYER2 where player 2 has a piece


class GameState(Enum):
    """
    Define the possible game states for reference. Make GameState an Enum so
    that it can be iterated through, reducing the chance of errors.
    """

    IS_WIN = 1
    IS_DRAW = -1
    STILL_PLAYING = 0


class SavedState:
    """ Can be used to store any extra info I want stored """
    pass


# This provides the type hints for the generate_move function family
GenMove = Callable[[Board, BoardPiece, Optional[SavedState]],
                   Tuple[PlayerAction, Optional[SavedState]]]


def initialize_game_state() -> Board:
    """ Initializes a connect four game board

    :return: ndarray, shape (6, 7) and data type (dtype) BoardPiece,
             initialized to 0 (NO_PLAYER).
    """

    return np.ones((6, 7), dtype=BoardPiece) * NO_PLAYER


def pretty_print_board(board: Board) -> str:
    """
    Converts the game board into a string that can be printed to
    neatly display the current game state. When printed, the piece
    at board[0, 0] should be in the lower-left position.

    :param board: 2d array representing current state of the game
    :return: string representing the current state of the game
    """

    # Define board shape
    bd_shp = board.shape

    # Top is full row of underscores
    length_row = 3 * bd_shp[0] + 3
    board_str = '_' * length_row + '\n'

    # For each row in the board
    for row in range(bd_shp[0] - 1, -1, -1):
        board_str += '|'

        # For each column in the board
        # Iterate in reverse order so that the bottom left corner is (0,0)
        for col in range(bd_shp[1]):
            curr_pos = board[row, col]
            # If the value is zero, position is empty
            if curr_pos == 0:
                board_str += '   '
            # If the value is one, position belongs to player 1 (X)
            elif curr_pos == 1:
                board_str += 'X  '
            # If the value is two, position belongs to player 2 (O)
            elif curr_pos == 2:
                board_str += 'O  '
            else:
                print('The board contains an invalid entry')

        board_str = board_str[:-2] + '|\n'

    # Add a separating row
    board_str += '|' + (length_row-2)*'=' + '|\n'
    # Add a row that shows the column numbers
    columns = np.arange(bd_shp[1])
    board_str += '|'
    for col in columns[:-1]:
        board_str += str(col) + '  '

    # Join
    # '  '.join(list(range()))
    board_str += str(columns[-1]) + '|\n'

    return board_str


def bitmap_to_board(board: Bitmap, mask: Bitmap, bd_shp: Tuple) -> Board:
    """ Converts the bitmap board into an nd.array for printing purposes.

    :param board: bitmap representing positions of current player
    :param mask: bitmap representing positions of both players
    :param bd_shp: tuple providing the shape of the game board (rows, cols)

    :return: array representing the current state of the game
    """

    # Generate an empty board
    board_arr = initialize_game_state()

    # Pad the bitmaps if they are not full length
    board_size = (bd_shp[0] + 1) * bd_shp[1] - 1
    mask_str = bin(mask)[2:]
    # print(mask.bit_length())
    if mask.bit_length() != board_size:
        add_str = '0' * (board_size - mask.bit_length())
        mask_str = add_str + mask_str
    # print(mask_str)
    board_str = bin(board)[2:]
    # print(board.bit_length())
    if board.bit_length() != board_size:
        add_str = '0' * (board_size - board.bit_length())
        board_str = add_str + board_str
    # print(board_str)

    # The first position in the bitmap represents the top-right array position
    bit_pos = len(mask_str)
    for cnt, bit in enumerate(mask_str):
        row = bit_pos % bd_shp[1] - 1
        col = bit_pos // bd_shp[1]
        # print(bit_pos)
        # print(row)
        # print(col)
        # print('Loop count', cnt+1)
        # print('')
        if row == (bd_shp[0]):
            bit_pos -= 1
            continue
        elif bit == '1':
            if board_str[cnt] == '1':
                board_arr[row, col] = BoardPiece(1)
            else:
                board_arr[row, col] = BoardPiece(2)
        bit_pos -= 1

    return board_arr


def string_to_board(pp_board: str) -> Board:
    """
    Converts a string representing the game state to an nd.array game board

    :param pp_board: string representing the current state of the game
    :return: 2d array representing current state of the game
    """

    # Initialize an empty board
    board_arr = initialize_game_state()
    # Initialize the column and row positions
    pos = 0
    col = 0
    row = board_arr.shape[0]

    row_entries = False
    for char in pp_board:
        if char == '_' or char == '=':
            continue

        if char == '|':
            row_entries = not row_entries
            col = 0
            pos = 0
        elif char == '\n':
            row -= 1

        # Break after all rows have been checked
        if row < 0:
            break

        if row_entries:
            if char == 'X':
                board_arr[row, col] = 1
            elif char == 'O':
                board_arr[row, col] = 2

            pos += 1
            col = pos // 3

    return board_arr


def apply_action(board: Board, col: PlayerAction, player: BoardPiece):
    """
    This function is used only in the main function. Applies the action by
    modifying board in place. Sets board[i, action] = player, where i is the
    lowest open row.

    :param board: 2d array representing current state of the game
    :param col: the column the current player played their piece in
    :param player: the player making the current move (active player)

    :return: None
    """

    # Modify board in place by applying player action
    board[top_row(board, col), col] = player


def apply_action_cp(board: Bitmap, mask: Bitmap, col: PlayerAction,
                    board_shape: Tuple) -> [Bitmap, Bitmap]:
    """
    This function is used for move searches, not for game play. Copies the
    board, and sets board[i, action] = player, where i is the lowest open row.
    The modified board and mask are returned.

    :param board: bitmap representing positions of current player
    :param mask: bitmap representing positions of both players
    :param col: the column the current player played their piece in
    :param board_shape: tuple representing the game board shape (rows, cols)

    :return: returns two bitmaps
        next_player = bitmap representing positions of next player to play
        new_mask = bitmap representing updated positions of both players
    """

    # If the column is full, raise an Exception
    board_rows = board_shape[0]
    top_mask = mpz(bin((1 << (board_rows - 1)) << (col * (board_rows + 1))))
    if (mask & top_mask) != 0:
        board_arr = bitmap_to_board(board, mask, board_shape)
        print('Column selected is {}'.format(col))
        print(pretty_print_board(board_arr))
        raise IndexError
    # top_mask = (1 << (board_rows - 1)) << (col * (board_rows + 1))
    # if (int(mask) & top_mask) != 0:
    #     raise IndexError
    # Define a new mask by applying the action
    new_mask = mask | (mask + (1 << (col * (board_rows + 1))))
    # Set the bit mask for the next player
    next_player = board ^ mask

    return next_player, new_mask


def connect_four(board_map: Bitmap, board_rows: int) -> bool:
    """
    Identify whether the current bitmap of the board results in a win
    for the whom it belongs to.

    :param board_map: bitmap representing positions of current player
    :param board_rows: the number of rows in the game board

    :return: True if the current player has four adjacent pieces,
             False otherwise
    """

    # Define the shift constants
    v_shift = 1
    h_shift = board_rows + 1
    d_shift = board_rows + 2
    b_shift = board_rows

    # Vertical check
    m = board_map & (board_map >> v_shift)
    if m & (m >> (2 * v_shift)):
        return True
    # Horizontal check
    m = board_map & (board_map >> h_shift)
    if m & (m >> (2 * h_shift)):
        return True
    # Diagonal \ check
    m = board_map & (board_map >> d_shift)
    if m & (m >> (2 * d_shift)):
        return True
    # Diagonal / check
    m = board_map & (board_map >> b_shift)
    if m & (m >> (2 * b_shift)):
        return True
    # # Nothing found
    # return False


def board_to_bitmap(board: Board, player: BoardPiece) -> [Bitmap, Bitmap]:
    """ Converts the nd.array board into a bitmap for faster calculations.

    Bitmap used to improve computation speed so that agent can train faster.
    The left-most bit in the bitmap represents the last position in the array
    board. The array board positions count from the top-right, down each row
    before moving to the next column. There is a sentinel row at the top of
    the array board. In the 6x7 board, the first bit is position 48, which is
    the top (sentinel row) in the right-most column. The next bit is position
    47, which represents the second row from the top, in the right-most column,
    etc...

    :param board: 2d array representing current state of the game
    :param player: the player who made the last move (active player)

    :return: two bitmaps representing active player's positions and the positions
             containing pieces of either player (mask)
    """

    # Initialize the bitmaps as strings (converted to int in return)
    position, mask = '', ''
    bd_shp = board.shape

    # Build the bitmap backwards, starting with the right-most column
    for col in range(bd_shp[1] - 1, -1, -1):
        # Add 0-bits to sentinel row to avoid rollover errors
        mask += '0'
        position += '0'

        # Start with top row
        for row in range(bd_shp[0] - 1, -1, -1):
            mask += ('1' if board[row, col] != NO_PLAYER else '0')
            position += ('1' if board[row, col] == player else '0')

    # return Bitmap(position, 2), Bitmap(mask, 2)
    return mpz(position, base=2), mpz(mask, base=2)


def check_end_state(board: Bitmap, mask: Bitmap, board_shp: Tuple
                    ) -> GameState:
    """
    Returns the current game state for the active player, i.e. has their last
    action won (GameState.IS_WIN) or drawn (GameState.IS_DRAW) the game,
    or is play still on-going (GameState.STILL_PLAYING)?

    :param board: bitmap representing positions of current player
    :param mask: bitmap representing positions of both players
    :param board_shp: the shape of the game board

    :return: GameState class constant indicating new state of game
    """

    # If connect_four returns True, the active player won
    if connect_four(board, board_shp[0]):
        return GameState.IS_WIN
    # If the game is not won, and there are no empty spots, the game is a draw
    elif popcount(mask) == board_shp[0] * board_shp[1]:
        return GameState.IS_DRAW
    # If the game is neither won, nor drawn, continue playing
    else:
        return GameState.STILL_PLAYING


def top_row(board: Board, col: PlayerAction):
    """
    Returns the highest row containing a board piece for the given column.
    Used to update the game state and determine the top row that must be
    checked to determine a win.

    :param board: 2d array representing current state of the game
    :param col: the column the last piece was played in

    :return: returns the index of the highest row containing a board piece
    """

    play_col = board[:, col]
    if play_col[-1] != 0:
        raise IndexError('This column is full')
    else:
        return min(np.argwhere(play_col == 0)[0])


# TODO: this function doesn't work properly, and the test doesn't catch it
def check_top_row(mask: Bitmap, col: PlayerAction, board_shp: Tuple) -> bool:
    """ Checks whether the top row of the given column is full

    :param mask: bitmap representing positions of both players
    :param col: the column to be checked
    :param board_shp: the shape of the game board

    :return: True if the top row is full, False if it is empty
    """

    bit_pos = col * board_shp[1] + board_shp[0] - 1
    return bit_test(mask, bit_pos)


# def valid_actions(mask: Bitmap, board_shp: Tuple) -> np.ndarray:
def valid_actions(mask: Bitmap, board_shp: Tuple) -> list:

    """ Determines which actions are valid for the current game state

    :param mask: bitmap representing positions of both players
    :param board_shp: the shape of the game board

    :return: array of valid actions
    """

    # actions = np.ndarray(0)
    actions = []
    for col in range(board_shp[1]):
        bit_pos = col * board_shp[1] + board_shp[0] - 1
        if not bit_test(mask, bit_pos):
            # actions = np.append(actions, col)
            actions.append(col)

    return actions
