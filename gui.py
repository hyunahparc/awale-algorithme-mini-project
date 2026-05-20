from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from awale import Awale
from players import GreedyBot, Human, MCTS, MinMax, PlayerBase, StupidBot


class AwaleGUI:
    """Tkinter interface for displaying and playing an Awale game."""

    def __init__(self, game: Awale, player1: PlayerBase, player2: PlayerBase) -> None:
        self.__game = game
        self.__players = {
            1: player1,
            2: player2,
        }
        self.__last_move: tuple[int, int] | None = None
        self.__animation_board: list[list[int]] | None = None
        self.__animation_position: tuple[int, int] | None = None
        self.__waiting_for_bot = False

        self.__window = tk.Tk()
        self.__window.title("Awale")

        self.__bot_choice = tk.StringVar(value=player2.__class__.__name__)
        tk.Label(self.__window, text="Opponent").grid(row=0, column=0, sticky="e", padx=5)
        tk.OptionMenu(
            self.__window,
            self.__bot_choice,
            "StupidBot",
            "GreedyBot",
            "MinMax",
            "MCTS",
            command=lambda _choice: self.__restart_game(),
        ).grid(row=0, column=1, columnspan=2, sticky="we", padx=5)

        tk.Button(
            self.__window,
            text="New game",
            command=self.__restart_game,
        ).grid(row=0, column=3, columnspan=2, sticky="we", padx=5)

        self.__status_label = tk.Label(self.__window, text="", font=("Arial", 14))
        self.__status_label.grid(row=1, column=0, columnspan=6, pady=10)

        self.__score_label = tk.Label(self.__window, text="", font=("Arial", 12))
        self.__score_label.grid(row=2, column=0, columnspan=6, pady=5)

        self.__pit_buttons: dict[tuple[int, int], tk.Button] = {}
        self.__create_board()
        self.__refresh()

    def run(self) -> None:
        self.__window.mainloop()

    def __create_board(self) -> None:
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

    def __refresh(self) -> None:
        board = self.__animation_board or self.__game.get_board()
        scores = self.__game.get_scores()

        status = f"Turn: Player {self.__game.get_current_player()}"
        if self.__last_move is not None:
            player, pit = self.__last_move
            status += f" | Last move: Player {player}, pit {pit}"
        self.__status_label.config(text=status)
        self.__score_label.config(text=f"Scores - Player 1: {scores[0]} | Player 2: {scores[1]}")

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

        if self.__game.is_finished():
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

        if current_player != 1:
            return

        if not self.__game.can_play(pit, current_player):
            messagebox.showwarning("Illegal move", "This pit cannot be played.")
            return

        human_player = self.__players[current_player]
        if isinstance(human_player, Human):
            human_player.set_mouse_move(pit)
            pit = human_player.choose_move()

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

        if not self.__game.is_finished() and self.__game.get_current_player() != 1:
            self.__window.after(700, self.__play_bot_turn_if_needed)
            return

        self.__waiting_for_bot = False

    def __play_bot_turn_if_needed(self) -> None:
        if self.__game.is_finished():
            return

        current_player = self.__game.get_current_player()
        if current_player == 1:
            self.__waiting_for_bot = False
            return

        move = self.__players[current_player].choose_move()
        self.__start_sowing_animation(
            current_player,
            move,
            lambda selected=move, player=current_player: self.__finish_bot_move(selected, player),
        )

    def __finish_bot_move(self, move: int, player: int) -> None:
        self.__animation_board = None
        self.__animation_position = None
        self.__game.play_move(move)
        self.__last_move = (player, move)
        self.__waiting_for_bot = False
        self.__refresh()

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
            1: Human(self.__game, 1),
            2: self.__build_bot(self.__bot_choice.get(), self.__game, 2),
        }
        self.__last_move = None
        self.__animation_board = None
        self.__animation_position = None
        self.__waiting_for_bot = False
        self.__refresh()

    def __build_bot(self, bot_name: str, game: Awale, identifier: int) -> PlayerBase:
        normalized_name = bot_name.lower()
        if normalized_name in ("stupidbot", "stupid"):
            return StupidBot(game, identifier)
        if normalized_name == "minmax":
            return MinMax(game, identifier, max_depth=1)
        if normalized_name == "mcts":
            return MCTS(game, identifier, iterations=50)
        return GreedyBot(game, identifier)
