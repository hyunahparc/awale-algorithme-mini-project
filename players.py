from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import Optional

from awale import Awale


class PlayerBase(ABC):
    """Common interface for human players and bots."""

    def __init__(self, game: Awale, identifier: int, name: Optional[str] = None) -> None:
        if identifier not in (1, 2):
            raise ValueError("Player identifier must be 1 or 2.")
        self._game = game
        self._identifier = identifier
        self._name = name or f"Player {identifier}"

    def get_identifier(self) -> int:
        return self._identifier

    def get_name(self) -> str:
        return self._name

    def get_game(self) -> Awale:
        return self._game

    @abstractmethod
    def choose_move(self) -> int:
        raise NotImplementedError


class Human(PlayerBase):
    """Console human player placeholder.

    The final project can connect this class to the graphical interface.
    """

    def __init__(self, game: Awale, identifier: int, name: Optional[str] = None) -> None:
        super().__init__(game, identifier, name)
        self.__mouse_move: Optional[int] = None

    def set_mouse_move(self, pit: int) -> None:
        self.__mouse_move = pit

    def choose_move(self) -> int:
        moves = self._game.legal_moves(self._identifier)

        if self.__mouse_move is not None:
            pit = self.__mouse_move
            self.__mouse_move = None
            if pit in moves:
                return pit
            raise ValueError("The selected pit is not playable.")

        while True:
            raw = input(f"{self._name}, choose a pit among {moves}: ").strip()
            try:
                pit = int(raw)
            except ValueError:
                print("Please enter a valid pit number.")
                continue
            if pit in moves:
                return pit
            print("This pit is not playable.")


class StupidBot(PlayerBase):
    """Random bot."""

    def choose_move(self) -> int:
        return random.choice(self._game.legal_moves(self._identifier))


class GreedyBot(PlayerBase):
    """Simple tactical bot based only on the current position."""

    def choose_move(self) -> int:
        moves = self._game.legal_moves(self._identifier)
        if not moves:
            raise RuntimeError("No move is possible.")
        return max(moves, key=lambda pit: self._game.immediate_gain(self._identifier, pit))


class MinMax(PlayerBase):
    """MinMax player with optional alpha-beta pruning."""

    def __init__(
        self,
        game: Awale,
        identifier: int,
        max_depth: int = 4,
        use_alpha_beta: bool = True,
        heuristic: str = "score",
        name: Optional[str] = None,
    ) -> None:
        super().__init__(game, identifier, name or f"MinMax {identifier}")
        if max_depth <= 0:
            raise ValueError("Max depth must be positive.")
        if heuristic not in ("score", "mobility"):
            raise ValueError("Heuristic must be 'score' or 'mobility'.")
        self.__max_depth = max_depth
        self.__use_alpha_beta = use_alpha_beta
        self.__heuristic = heuristic

    def choose_move(self) -> int:
        moves = self._game.legal_moves(self._identifier)
        if not moves:
            raise RuntimeError("No move is possible.")

        _, best_move = self.__minmax(
            self._game.copy(),
            self.__max_depth,
            self._identifier,
            -math.inf,
            math.inf,
        )

        if best_move is None:
            return random.choice(moves)
        return best_move

    def evaluate(self, game: Awale, player: Optional[int] = None) -> int:
        player = player or self._identifier
        if self.__heuristic == "score":
            return game.heuristic_score(player)
        return game.heuristic_mobility(player)

    def __minmax(
        self,
        game: Awale,
        depth: int,
        current_player: int,
        alpha: float,
        beta: float,
    ) -> tuple[int, Optional[int]]:
        if depth == 0 or game.is_finished():
            return self.evaluate(game, self._identifier), None

        moves = game.legal_moves(current_player)
        if not moves:
            return self.evaluate(game, self._identifier), None

        maximizing = current_player == self._identifier
        best_move = moves[0]

        if maximizing:
            best_score = -math.inf

            for move in moves:
                copied = game.copy()
                copied.play_move(move)

                score, _ = self.__minmax(
                    copied,
                    depth - 1,
                    copied.get_current_player(),
                    alpha,
                    beta,
                )

                if score > best_score:
                    best_score = score
                    best_move = move

                alpha = max(alpha, best_score)
                if self.__use_alpha_beta and beta <= alpha:
                    break

            return int(best_score), best_move

        best_score = math.inf

        for move in moves:
            copied = game.copy()
            copied.play_move(move)

            score, _ = self.__minmax(
                copied,
                depth - 1,
                copied.get_current_player(),
                alpha,
                beta,
            )

            if score < best_score:
                best_score = score
                best_move = move

            beta = min(beta, best_score)
            if self.__use_alpha_beta and beta <= alpha:
                break

        return int(best_score), best_move

    def optimal_move(self) -> int:
        return self.choose_move()

    def minmax_algorithm(self) -> int:
        return self.choose_move()


class Sommet:
    """Sommet of the MCTS game tree."""

    def __init__(
        self,
        game: Awale,
        parent: Optional["Sommet"] = None,
        current_player: int = 1,
        move: Optional[int] = None,
    ) -> None:
        self.__game = game
        self.__parent = parent
        self.__children: list[Sommet] = []
        self.__visits = 0
        self.__wins = 0.0
        self.__current_player = current_player
        self.__move = move

    def get_game(self) -> Awale:
        return self.__game

    def get_parent(self) -> Optional["Sommet"]:
        return self.__parent

    def get_children(self) -> list["Sommet"]:
        return self.__children[:]

    def get_visits(self) -> int:
        return self.__visits

    def get_wins(self) -> float:
        return self.__wins

    def get_current_player(self) -> int:
        return self.__current_player

    def get_move(self) -> Optional[int]:
        return self.__move

    def is_terminal(self) -> bool:
        return self.__game.is_finished()

    def is_fully_expanded(self) -> bool:
        explored = {child.get_move() for child in self.__children}
        return set(self.__game.legal_moves(self.__current_player)).issubset(explored)

    def update(self, result: float) -> None:
        self.__visits += 1
        self.__wins += result

    def add_child(self, child: "Sommet") -> None:
        self.__children.append(child)


class MCTS(PlayerBase):
    """Monte Carlo Tree Search player."""

    def __init__(
        self,
        game: Awale,
        identifier: int,
        iterations: int = 500,
        temperature: float = math.sqrt(2),
        name: Optional[str] = None,
    ) -> None:
        super().__init__(game, identifier, name or f"MCTS {identifier}")
        if iterations <= 0:
            raise ValueError("Iterations must be positive.")
        if temperature < 0:
            raise ValueError("Temperature must be positive or zero.")
        self.__iterations = iterations
        self.__temperature = temperature

    def __uct_score(self, parent: Sommet, child: Sommet) -> float:
        if child.get_visits() == 0:
            return math.inf

        exploitation = child.get_wins() / child.get_visits()
        exploration = self.__temperature * math.sqrt(
            math.log(max(1, parent.get_visits())) / child.get_visits()
        )
        return exploitation + exploration

    def choose_move(self) -> int:
        moves = self._game.legal_moves(self._identifier)
        if not moves:
            raise RuntimeError("No move is possible.")

        root = Sommet(
            self._game.copy(),
            current_player=self._identifier,
        )

        for _ in range(self.__iterations):
            selected = self.selection(root)
            expanded = self.expansion(selected)
            winner = self.simulation(expanded)
            self.backpropagation(expanded, winner)

        children = root.get_children()
        if not children:
            return random.choice(moves)

        best_child = max(
            children,
            key=lambda child: (
                child.get_visits(),
                child.get_wins() / child.get_visits() if child.get_visits() else 0,
            ),
        )

        move = best_child.get_move()
        if move is None:
            return random.choice(moves)

        return move

    def selection(self, root: Sommet) -> Sommet:
        current = root

        while current.is_fully_expanded() and current.get_children():
            current = max(
                current.get_children(),
                key=lambda child: self.__uct_score(current, child),
            )

        return current

    def expansion(self, node: Sommet) -> Sommet:
        if node.is_terminal():
            return node

        explored_moves = {child.get_move() for child in node.get_children()}
        possible_moves = node.get_game().legal_moves(node.get_current_player())

        unexplored_moves = [
            move for move in possible_moves
            if move not in explored_moves
        ]

        if not unexplored_moves:
            return node

        move = random.choice(unexplored_moves)
        copied = node.get_game().copy()
        copied.play_move(move)

        child = Sommet(
            copied,
            parent=node,
            current_player=copied.get_current_player(),
            move=move,
        )

        node.add_child(child)
        return child

    def simulation(self, node: Sommet) -> int:
        copied = node.get_game().copy()
        max_turns = 300
        turn_count = 0

        while not copied.is_finished() and turn_count < max_turns:
            current_player = copied.get_current_player()
            moves = copied.legal_moves(current_player)

            if not moves:
                break

            move = random.choice(moves)
            copied.play_move(move)
            turn_count += 1

        if copied.is_finished():
            return copied.get_winner()

        scores = copied.get_scores()
        if scores[0] > scores[1]:
            return 1
        if scores[1] > scores[0]:
            return 2
        return 0

    def backpropagation(self, node: Sommet, winner: int) -> None:
        current: Optional[Sommet] = node

        while current is not None:
            player_who_played = 3 - current.get_current_player()

            if winner == 0:
                result = 0.5
            elif winner == player_who_played:
                result = 1.0
            else:
                result = 0.0

            current.update(result)
            current = current.get_parent()

    def mcts_algorithm(self) -> int:
        return self.choose_move()
