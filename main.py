from __future__ import annotations

import argparse
from itertools import combinations

from awale import Awale
from gui import AwaleGUI
from players import GreedyBot, Human, MCTS, MinMax, PlayerBase, StupidBot


def play_game(
    player1: PlayerBase,
    player2: PlayerBase,
    display: bool = True,
    max_turns: int = 300,
) -> int:
    """Play one game and return the winner."""
    game = player1.get_game()
    players = {1: player1, 2: player2}
    turn_count = 0

    while not game.is_finished() and turn_count < max_turns:
        current = game.get_current_player()
        move = players[current].choose_move()
        game.play_move(move)
        turn_count += 1

        if display:
            print(f"{players[current].get_name()} plays pit {move}")
            game.print_board()

    if not game.is_finished():
        scores = game.get_scores()
        if scores[0] > scores[1]:
            return 1
        if scores[1] > scores[0]:
            return 2
        return 0

    return game.get_winner()


def build_player(
    kind: str,
    game: Awale,
    identifier: int,
    minmax_depth: int = 2,
    mcts_iterations: int = 100,
) -> PlayerBase:
    if kind == "human":
        return Human(game, identifier, f"Human {identifier}")
    if kind == "stupid":
        return StupidBot(game, identifier, f"StupidBot {identifier}")
    if kind == "greedy":
        return GreedyBot(game, identifier, f"GreedyBot {identifier}")
    if kind == "minmax":
        return MinMax(game, identifier, max_depth=minmax_depth, name=f"MinMax {identifier}")
    if kind == "mcts":
        return MCTS(game, identifier, iterations=mcts_iterations, name=f"MCTS {identifier}")
    raise ValueError(f"Unknown player type: {kind}.")


def compare_players(
    kind1: str,
    kind2: str,
    games_count: int = 10,
    minmax_depth: int = 2,
    mcts_iterations: int = 100,
    max_turns: int = 300,
) -> dict[str, int]:
    """Run several games between two player types."""
    stats = {
        "player1_wins": 0,
        "player2_wins": 0,
        "draws": 0,
        "starter_wins": 0,
        "second_player_wins": 0,
        "kind1_wins_as_starter": 0,
        "kind1_wins_as_second": 0,
        "kind2_wins_as_starter": 0,
        "kind2_wins_as_second": 0,
    }

    for game_index in range(games_count):
        game = Awale()
        if game_index % 2 == 0:
            player1 = build_player(kind1, game, 1, minmax_depth, mcts_iterations)
            player2 = build_player(kind2, game, 2, minmax_depth, mcts_iterations)
        else:
            player1 = build_player(kind2, game, 1, minmax_depth, mcts_iterations)
            player2 = build_player(kind1, game, 2, minmax_depth, mcts_iterations)

        winner = play_game(player1, player2, display=False, max_turns=max_turns)
        if winner == 0:
            stats["draws"] += 1
        else:
            if winner == 1:
                stats["starter_wins"] += 1
            else:
                stats["second_player_wins"] += 1

            if game_index % 2 == 0:
                if winner == 1:
                    stats["player1_wins"] += 1
                    stats["kind1_wins_as_starter"] += 1
                else:
                    stats["player2_wins"] += 1
                    stats["kind2_wins_as_second"] += 1
            else:
                if winner == 1:
                    stats["player2_wins"] += 1
                    stats["kind2_wins_as_starter"] += 1
                else:
                    stats["player1_wins"] += 1
                    stats["kind1_wins_as_second"] += 1

    return stats


def run_game(args: argparse.Namespace) -> None:
    game = Awale()
    player1 = build_player(args.player1, game, 1, args.minmax_depth, args.mcts_iterations)
    player2 = build_player(args.player2, game, 2, args.minmax_depth, args.mcts_iterations)
    game.print_board()
    winner = play_game(player1, player2, display=True, max_turns=args.max_turns)
    print(f"Winner: {winner}")


def run_gui(args: argparse.Namespace) -> None:
    game = Awale()
    player1 = Human(game, 1)
    player2 = build_player(args.opponent, game, 2, args.gui_minmax_depth, args.gui_mcts_iterations)
    gui = AwaleGUI(game, player1, player2)
    gui.run()


def main_gui() -> None:
    args = argparse.Namespace(
        opponent="greedy",
        gui_minmax_depth=1,
        gui_mcts_iterations=50,
    )
    run_gui(args)


def run_stats(args: argparse.Namespace) -> None:
    for player1, player2 in combinations(args.players, 2):
        stats = compare_players(
            player1,
            player2,
            games_count=args.games_count,
            minmax_depth=args.minmax_depth,
            mcts_iterations=args.mcts_iterations,
            max_turns=args.max_turns,
        )
        print(f"{player1} vs {player2}: {stats}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Awale game with MinMax, MCTS and GUI")
    parser.add_argument("--minmax-depth", type=int, default=2)
    parser.add_argument("--mcts-iterations", type=int, default=100)
    parser.add_argument("--max-turns", type=int, default=300)

    subparsers = parser.add_subparsers(dest="mode", required=True)

    gui_parser = subparsers.add_parser("gui", help="Start the graphical interface")
    gui_parser.add_argument(
        "--opponent",
        choices=("stupid", "greedy", "minmax", "mcts"),
        default="greedy",
    )
    gui_parser.add_argument("--gui-minmax-depth", type=int, default=1)
    gui_parser.add_argument("--gui-mcts-iterations", type=int, default=50)

    game_parser = subparsers.add_parser("game", help="Play one console game")
    game_parser.add_argument(
        "--player1",
        choices=("human", "stupid", "greedy", "minmax", "mcts"),
        default="stupid",
    )
    game_parser.add_argument(
        "--player2",
        choices=("human", "stupid", "greedy", "minmax", "mcts"),
        default="greedy",
    )

    stats_parser = subparsers.add_parser("stats", help="Run automatic statistics")
    stats_parser.add_argument("--games-count", type=int, default=20)
    stats_parser.add_argument(
        "--players",
        nargs="+",
        choices=("stupid", "greedy", "minmax", "mcts"),
        default=("stupid", "greedy", "minmax", "mcts"),
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "gui":
        run_gui(args)
    elif args.mode == "game":
        run_game(args)
    elif args.mode == "stats":
        run_stats(args)


if __name__ == "__main__":
    main()
