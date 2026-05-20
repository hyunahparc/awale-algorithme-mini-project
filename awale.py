from __future__ import annotations


class Awale:
    """Model of the Awale game.

    This class must contain the rules only: board state, legal moves,
    sowing, captures, scores, end of game and heuristics.
    """

    NB_PLAYERS = 2
    NB_PITS = 6
    INITIAL_SEEDS = 4

    def __init__(self) -> None:
        self.__board: list[list[int]] = []
        self.__scores: list[int] = []
        self.__current_player = 1
        self.__finished = False
        self.__winner = 0
        self.reset()

    def __repr__(self) -> str:
        return (
            f"Awale(scores={self.__scores}, "
            f"current_player={self.__current_player})"
        )

    def reset(self) -> None:
        """Reset the game to the initial position."""
        self.__board = [
            [self.INITIAL_SEEDS for _ in range(self.NB_PITS)],
            [self.INITIAL_SEEDS for _ in range(self.NB_PITS)],
        ]
        self.__scores = [0, 0]
        self.__current_player = 1
        self.__finished = False
        self.__winner = 0

    def copy(self) -> "Awale":
        """Return an independent copy of the current game."""
        copied = Awale()
        copied.__board = [row[:] for row in self.__board]
        copied.__scores = self.__scores[:]
        copied.__current_player = self.__current_player
        copied.__finished = self.__finished
        copied.__winner = self.__winner
        return copied

    def get_board(self) -> list[list[int]]:
        return [row[:] for row in self.__board]

    def get_scores(self) -> list[int]:
        return self.__scores[:]

    def get_current_player(self) -> int:
        return self.__current_player

    def is_finished(self) -> bool:
        return self.__finished

    def get_winner(self) -> int:
        return self.__winner

    def get_opponent(self, player: int) -> int:
        self.__check_player(player)
        return 3 - player

    def seeds_of_player(self, player: int) -> int:
        self.__check_player(player)
        return sum(self.__board[player - 1])

    def is_side_empty(self, player: int) -> bool:
        return self.seeds_of_player(player) == 0

    def legal_moves(self, player: int | None = None) -> list[int]:
        """Return all legal pit indexes for the given player."""
        player = player or self.__current_player
        self.__check_player(player)

        moves = [
            pit
            for pit in range(self.NB_PITS)
            if self.__board[player - 1][pit] > 0
        ]

        opponent = self.get_opponent(player)
        if not self.is_side_empty(opponent):
            return moves

        return [
            pit
            for pit in moves
            if self.__would_feed_opponent(player, pit)
        ]

    def list_possible_moves(self) -> list[int]:
        """Compatibility name, close to the TP structure."""
        return self.legal_moves()

    def can_play(self, pit: int, player: int | None = None) -> bool:
        player = player or self.__current_player
        self.__check_player(player)
        self.__check_pit(pit)
        return pit in self.legal_moves(player)

    def get_sowing_path(self, player: int, pit: int) -> list[tuple[int, int]]:
        """Return the positions reached by seeds for display purposes."""
        self.__check_player(player)
        self.__check_pit(pit)

        positions = [
            (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
            (2, 5), (2, 4), (2, 3), (2, 2), (2, 1), (2, 0),
        ]

        start = (player, pit)
        current_index = positions.index(start)
        seeds = self.__board[player - 1][pit]
        path = []

        while seeds > 0:
            current_index = (current_index + 1) % len(positions)
            position = positions[current_index]

            if position == start:
                continue

            path.append(position)
            seeds -= 1

        return path

    def play_move(self, pit: int) -> None:
        """Play one move for the current player."""
        if self.__finished:
            raise RuntimeError("The game is already finished.")
        if not self.can_play(pit):
            raise ValueError(f"Illegal move: pit {pit}.")

        player = self.__current_player

        final_position = self.__sow(player, pit)
        captured = self.__capture(player, final_position)
        self.__scores[player - 1] += captured
        self.__update_game_end()

        if not self.__finished:
            self.__current_player = self.get_opponent(player)

    def immediate_gain(self, player: int, pit: int) -> int:
        """Return the number of seeds captured by a move, without changing self."""
        copied = self.copy()
        before = copied.get_scores()[player - 1]
        copied.__current_player = player
        copied.play_move(pit)
        after = copied.get_scores()[player - 1]
        return after - before

    def heuristic_score(self, player: int) -> int:
        """First heuristic: captured seeds and remaining seeds difference."""
        self.__check_player(player)
        opponent = self.get_opponent(player)
        score_diff = self.__scores[player - 1] - self.__scores[opponent - 1]
        seeds_diff = self.seeds_of_player(player) - self.seeds_of_player(opponent)
        return 10 * score_diff + seeds_diff

    def heuristic_mobility(self, player: int) -> int:
        """Second heuristic: score difference and number of available moves."""
        self.__check_player(player)
        opponent = self.get_opponent(player)
        score_diff = self.__scores[player - 1] - self.__scores[opponent - 1]
        mobility_diff = len(self.legal_moves(player)) - len(self.legal_moves(opponent))
        return 8 * score_diff + 2 * mobility_diff

    def print_board(self) -> None:
        """Print a simple console view for debugging."""
        top = " ".join(f"{seeds:2d}" for seeds in reversed(self.__board[1]))
        bottom = " ".join(f"{seeds:2d}" for seeds in self.__board[0])
        print()
        print("      Player 2")
        print(f"   {top}")
        print(f"   {bottom}")
        print("      Player 1")
        print(f"Scores: P1={self.__scores[0]} P2={self.__scores[1]}")
        print(f"Turn: P{self.__current_player}")
        print()

    def __sow(self, player: int, pit: int) -> tuple[int, int]:
        """Sow seeds and return the final position as (player_side, pit)."""
        self.__check_player(player)
        self.__check_pit(pit)

        positions = [
            (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
            (2, 5), (2, 4), (2, 3), (2, 2), (2, 1), (2, 0),
        ]

        start = (player, pit)
        index = positions.index(start)
        seeds = self.__board[player - 1][pit]
        self.__board[player - 1][pit] = 0

        current_index = index
        final_position = start

        while seeds > 0:
            current_index = (current_index + 1) % len(positions)
            side, current_pit = positions[current_index]

            if (side, current_pit) == start:
                continue

            self.__board[side - 1][current_pit] += 1
            seeds -= 1
            final_position = (side, current_pit)

        return final_position

    def __capture(self, player: int, final_position: tuple[int, int]) -> int:
        """Capture seeds according to the Awale rules."""
        positions = self.__capture_positions(player, final_position)
        captured = sum(self.__board[side - 1][pit] for side, pit in positions)

        opponent = self.get_opponent(player)
        if captured == self.seeds_of_player(opponent):
            return 0

        for side, pit in positions:
            self.__board[side - 1][pit] = 0

        return captured

    def __capture_positions(
        self, player: int, final_position: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """Return positions that would be captured."""
        opponent = self.get_opponent(player)
        side, pit = final_position

        if side != opponent:
            return []

        positions = [
            (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
            (2, 5), (2, 4), (2, 3), (2, 2), (2, 1), (2, 0),
        ]

        index = positions.index((side, pit))
        captured_positions = []

        while True:
            current_side, current_pit = positions[index]

            if current_side != opponent:
                break

            seeds = self.__board[current_side - 1][current_pit]
            if seeds not in (2, 3):
                break

            captured_positions.append((current_side, current_pit))
            index = (index - 1) % len(positions)

        return captured_positions

    def __would_feed_opponent(self, player: int, pit: int) -> bool:
        """Return True if this move gives at least one seed to the opponent."""
        opponent = self.get_opponent(player)
        copied = self.copy()
        copied.__sow(player, pit)
        return copied.seeds_of_player(opponent) > 0

    def __update_game_end(self) -> None:
        """Update finished state and winner."""
        if self.__scores[0] >= 25 or self.__scores[1] >= 25:
            self.__finished = True
            self.__set_winner_from_scores()
            return

        next_player = self.get_opponent(self.__current_player)
        if not self.legal_moves(next_player):
            self.__collect_remaining_seeds()
            self.__finished = True
            self.__set_winner_from_scores()

    def __collect_remaining_seeds(self) -> None:
        """Collect remaining seeds at the end of the game."""
        for player in (1, 2):
            self.__scores[player - 1] += sum(self.__board[player - 1])
            self.__board[player - 1] = [0 for _ in range(self.NB_PITS)]

    def __set_winner_from_scores(self) -> None:
        if self.__scores[0] > self.__scores[1]:
            self.__winner = 1
        elif self.__scores[1] > self.__scores[0]:
            self.__winner = 2
        else:
            self.__winner = 0

    def __check_player(self, player: int) -> None:
        if player not in (1, 2):
            raise ValueError("Player must be 1 or 2.")

    def __check_pit(self, pit: int) -> None:
        if not 0 <= pit < self.NB_PITS:
            raise IndexError(f"Invalid pit index: {pit}.")
