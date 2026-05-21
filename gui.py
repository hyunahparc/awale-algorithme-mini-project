from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from awale import Awale
from players import GreedyBot, Human, MCTS, MinMax, PlayerBase, StupidBot


class AwaleGUI:
    """Tkinter interface for displaying and playing an Awale game."""

    def __init__(
        self,
        game: Awale,
        player1: PlayerBase,
        player2: PlayerBase,
        minmax_heuristic: str = "score",
    ) -> None:
        self.__game = game
        self.__players = {
            1: player1,
            2: player2,
        }
        self.__minmax_heuristic = minmax_heuristic
        self.__last_move: tuple[int, int] | None = None
        self.__animation_board: list[list[int]] | None = None
        self.__animation_position: tuple[int, int] | None = None
        self.__waiting_for_bot = False
        self.__game_over_announced = False

        self.__window = tk.Tk()
        self.__window.title("Awale")

        self.__player1_choice = tk.StringVar(value=self.__player_label(player1, minmax_heuristic))
        self.__player2_choice = tk.StringVar(value=self.__player_label(player2, minmax_heuristic))

        tk.Label(self.__window, text="Player 1").grid(row=0, column=0, sticky="e", padx=5)
        tk.OptionMenu(
            self.__window,
            self.__player1_choice,
            "Human",
            "StupidBot",
            "GreedyBot",
            "MinMax score",
            "MinMax mobility",
            "MCTS",
        ).grid(row=0, column=1, columnspan=2, sticky="we", padx=5)

        tk.Label(self.__window, text="Player 2").grid(row=0, column=3, sticky="e", padx=5)
        tk.OptionMenu(
            self.__window,
            self.__player2_choice,
            "StupidBot",
            "GreedyBot",
            "MinMax score",
            "MinMax mobility",
            "MCTS",
        ).grid(row=0, column=4, columnspan=2, sticky="we", padx=5)

        tk.Button(
            self.__window,
            text="New game",
            command=self.__restart_game,
        ).grid(row=1, column=0, columnspan=6, sticky="we", padx=5, pady=5)

        self.__status_label = tk.Label(self.__window, text="", font=("Arial", 14))
        self.__status_label.grid(row=2, column=0, columnspan=6, pady=10)

        self.__player1_label: tk.Label | None = None
        self.__player2_label: tk.Label | None = None
        self.__pit_buttons: dict[tuple[int, int], tk.Button] = {}
        self.__create_board()
        self.__refresh()

    def run(self) -> None:
        self.__window.mainloop()

    def __create_board(self) -> None:
        self.__player2_label = tk.Label(self.__window, text="", font=("Arial", 12))
        self.__player2_label.grid(row=3, column=0, columnspan=6, pady=(5, 0))
        for pit in range(Awale.NB_PITS):
            button = tk.Button(
                self.__window,
                width=8,
                height=3,
                state=tk.DISABLED,
                command=lambda selected=pit: self.__on_pit_clicked(selected),
            )
            button.grid(row=4, column=pit, padx=5, pady=5)
            self.__pit_buttons[(2, pit)] = button

        for pit in range(Awale.NB_PITS):
            button = tk.Button(
                self.__window,
                width=8,
                height=3,
                command=lambda selected=pit: self.__on_pit_clicked(selected),
            )
            button.grid(row=5, column=pit, padx=5, pady=5)
            self.__pit_buttons[(1, pit)] = button

        self.__player1_label = tk.Label(self.__window, text="", font=("Arial", 12))
        self.__player1_label.grid(row=6, column=0, columnspan=6, pady=(0, 5))

    def __refresh(self) -> None:
        board = self.__animation_board or self.__game.get_board()
        scores = self.__game.get_scores()

        status = f"Turn: Player {self.__game.get_current_player()}"
        if self.__last_move is not None:
            player, pit = self.__last_move
            status += f" | Last move: Player {player}, pit {pit}"
        self.__status_label.config(text=status)
        if self.__player1_label is not None:
            self.__player1_label.config(text=f"Player 1 - Score: {scores[0]}")
        if self.__player2_label is not None:
            self.__player2_label.config(text=f"Player 2 - Score: {scores[1]}")

        for pit in range(Awale.NB_PITS):
            player1_color = "SystemButtonFace"
            player2_color = "SystemButtonFace"

            if self.__animation_position == (1, pit):
                player1_color = "#c8f7c5"
            elif self.__last_move == (1, pit):
                player1_color = "#d7f0ff"

            if self.__animation_position == (2, pit):
                player2_color = "#c8f7c5"
            elif self.__last_move == (2, pit):
                player2_color = "#ffe2b8"

            self.__pit_buttons[(1, pit)].config(text=str(board[0][pit]), bg=player1_color)
            self.__pit_buttons[(2, pit)].config(text=str(board[1][pit]), bg=player2_color)

        if self.__game.is_finished() and not self.__game_over_announced:
            self.__game_over_announced = True
            winner = self.__game.get_winner()
            if winner == 0:
                message = "Draw"
            else:
                message = f"Player {winner} wins"
            messagebox.showinfo("Game over", message)

    def __on_pit_clicked(self, pit: int) -> None:
        if self.__waiting_for_bot:
            return

        current_player = self.__game.get_current_player()
        player = self.__players[current_player]

        if not isinstance(player, Human):
            return
        if current_player != 1:
            return

        if not self.__game.can_play(pit, current_player):
            messagebox.showwarning("Illegal move", "This pit cannot be played.")
            return

        player.set_mouse_move(pit)
        pit = player.choose_move()

        self.__last_move = (current_player, pit)
        self.__refresh()
        self.__waiting_for_bot = True
        self.__start_sowing_animation(
            current_player,
            pit,
            lambda selected=pit, player=current_player: self.__finish_human_move(selected, player),
        )

    def __finish_human_move(self, pit: int, player: int) -> None:
        self.__animation_board = None
        self.__animation_position = None
        self.__game.play_move(pit)
        self.__last_move = (player, pit)
        self.__refresh()

        self.__waiting_for_bot = False
        self.__continue_automatic_game()

    def __continue_automatic_game(self) -> None:
        if self.__game.is_finished():
            return

        current_player = self.__game.get_current_player()
        if isinstance(self.__players[current_player], Human):
            return

        self.__waiting_for_bot = True
        self.__window.after(700, self.__play_computer_turn)

    def __play_computer_turn(self) -> None:
        if self.__game.is_finished():
            self.__waiting_for_bot = False
            return

        current_player = self.__game.get_current_player()
        player = self.__players[current_player]
        if isinstance(player, Human):
            self.__waiting_for_bot = False
            return

        move = player.choose_move()
        self.__start_sowing_animation(
            current_player,
            move,
            lambda selected=move, player_id=current_player: self.__finish_computer_move(selected, player_id),
        )

    def __finish_computer_move(self, move: int, player: int) -> None:
        self.__animation_board = None
        self.__animation_position = None
        self.__game.play_move(move)
        self.__last_move = (player, move)
        self.__waiting_for_bot = False
        self.__refresh()
        self.__continue_automatic_game()

    def __start_sowing_animation(
        self,
        player: int,
        pit: int,
        on_finished,
    ) -> None:
        path = self.__game.get_sowing_path(player, pit)
        self.__animation_board = self.__game.get_board()
        self.__animation_board[player - 1][pit] = 0
        self.__animation_position = (player, pit)
        self.__last_move = (player, pit)
        self.__refresh()
        self.__animate_sowing_step(path, 0, on_finished)

    def __animate_sowing_step(self, path, index: int, on_finished) -> None:
        if self.__animation_board is None:
            return

        if index >= len(path):
            self.__window.after(200, on_finished)
            return

        side, pit = path[index]
        self.__animation_board[side - 1][pit] += 1
        self.__animation_position = (side, pit)
        self.__refresh()
        self.__window.after(220, lambda: self.__animate_sowing_step(path, index + 1, on_finished))

    def __restart_game(self) -> None:
        self.__game = Awale()
        self.__players = {
            1: self.__build_player(self.__player1_choice.get(), self.__game, 1),
            2: self.__build_player(self.__player2_choice.get(), self.__game, 2),
        }
        self.__last_move = None
        self.__animation_board = None
        self.__animation_position = None
        self.__waiting_for_bot = False
        self.__game_over_announced = False
        self.__refresh()
        self.__continue_automatic_game()

    def __build_player(self, player_name: str, game: Awale, identifier: int) -> PlayerBase:
        normalized_name = player_name.lower()
        if normalized_name == "human":
            return Human(game, identifier)
        if normalized_name in ("stupidbot", "stupid"):
            return StupidBot(game, identifier)
        if normalized_name in ("minmax score", "minmax"):
            self.__minmax_heuristic = "score"
            return MinMax(game, identifier, max_depth=1, heuristic=self.__minmax_heuristic)
        if normalized_name == "minmax mobility":
            self.__minmax_heuristic = "mobility"
            return MinMax(game, identifier, max_depth=1, heuristic=self.__minmax_heuristic)
        if normalized_name == "mcts":
            return MCTS(game, identifier, iterations=50)
        return GreedyBot(game, identifier)

    def __player_label(self, player: PlayerBase, minmax_heuristic: str) -> str:
        if isinstance(player, Human):
            return "Human"
        if isinstance(player, MinMax):
            return f"MinMax {minmax_heuristic}"
        return player.__class__.__name__
