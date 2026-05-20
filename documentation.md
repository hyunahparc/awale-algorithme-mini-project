# Technical Documentation - Awale Project

## 1. Introduction

This project implements the Awale board game in Python with an object-oriented architecture. The goal is to provide a playable game engine, several player strategies, a graphical interface, and automatic match statistics.

The implementation follows the same general structure as the Puissance 4 practical work: one model class for the game rules, a common player interface, several bot classes, and a command-line runner.

## 2. Project Structure

- `awale.py`: contains the `Awale` class, which stores the game state and implements the rules.
- `players.py`: contains the player classes: `Human`, `StupidBot`, `GreedyBot`, `MinMax`, `Sommet`, and `MCTS`.
- `gui.py`: contains the Tkinter graphical interface.
- `main.py`: contains the command-line interface, game runner, and statistics functions.
- `README.md`: contains basic usage instructions.

## 3. Data Structures

The board is stored as a list of two lists:

```python
[
    [4, 4, 4, 4, 4, 4],
    [4, 4, 4, 4, 4, 4],
]
```

The first row represents Player 1's side, and the second row represents Player 2's side. Each player has six pits. At the beginning of the game, each pit contains four seeds.

Captured seeds are stored in:

```python
scores = [0, 0]
```

The current player is represented by the integer `1` or `2`. The opponent can be computed with:

```python
3 - player
```

The attributes of `Awale` are private, for example `__board`, `__scores`, and `__current_player`. Access is done through methods such as `get_board()`, `get_scores()`, and `get_current_player()`.

## 4. The `Awale` Class

The `Awale` class is the central model of the project. It is responsible for:

- initializing and resetting the board,
- storing scores,
- storing the current player,
- checking legal moves,
- sowing seeds,
- applying captures,
- detecting the end of the game,
- providing heuristic evaluations for AI players,
- providing a copy of the game state for search algorithms.

Important methods:

- `reset()`: resets the game to the initial state.
- `copy()`: returns an independent copy of the current game.
- `legal_moves(player)`: returns the list of legal moves for a player.
- `can_play(pit, player)`: checks whether a move is legal.
- `play_move(pit)`: applies a move for the current player.
- `get_sowing_path(player, pit)`: returns the sowing path for GUI animation.
- `heuristic_score(player)`: first heuristic used by MinMax.
- `heuristic_mobility(player)`: second heuristic used by MinMax.

## 5. Game Rules Implementation

### Sowing

When a player chooses a pit, all seeds from this pit are picked up. The selected pit becomes empty, and the seeds are distributed one by one in the following order:

```python
[
    (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
    (2, 5), (2, 4), (2, 3), (2, 2), (2, 1), (2, 0),
]
```

If the sowing goes around the board, the original pit is skipped.

### Capture

A capture can happen only if the last seed lands on the opponent's side. Starting from the last pit reached, the game checks backwards on the opponent side. If a pit contains two or three seeds, these seeds are captured. The capture continues backwards as long as the pits contain two or three seeds.

The implementation also prevents a move from capturing all the opponent's remaining seeds.

### Feeding Rule

If the opponent has no seeds, the current player must play a move that gives at least one seed to the opponent. This is checked in `legal_moves()`.

### End of Game

The game ends when:

- a player reaches at least 25 captured seeds,
- the next player has no legal move.

When the game ends because a player cannot move, the remaining seeds are collected and added to the players' scores. The winner is then determined by comparing the scores.

Automatic games also use a maximum turn limit to avoid abnormally long simulations. If the limit is reached, the current score determines the winner.

## 6. Player Classes

All players inherit from `PlayerBase`. This abstract class stores:

- the game instance,
- the player identifier,
- the player name.

Each player must implement:

```python
choose_move()
```

This makes the game loop independent from the type of player. The main loop can simply ask the current player for a move and then apply it to the game.

### Human

The `Human` class represents a human player. In console mode, the player enters a pit number. In GUI mode, the human player selects a pit with the mouse. The GUI stores the clicked pit in the `Human` instance, and `choose_move()` returns this mouse-selected move.

### StupidBot

`StupidBot` chooses randomly among all legal moves.

### GreedyBot

`GreedyBot` is the additional tactical strategy required by the project. It does not search several moves ahead. It only evaluates the current position and chooses the move with the best immediate capture.

## 7. MinMax Algorithm

The `MinMax` class implements a depth-limited MinMax algorithm with optional alpha-beta pruning.

For each legal move, the algorithm:

1. copies the current game state,
2. applies the move on the copy,
3. recursively evaluates the resulting position,
4. selects the maximum score when it is the AI player's turn,
5. selects the minimum score when it is the opponent's turn.

Alpha-beta pruning is used to stop exploring branches that cannot improve the final decision.

The implementation uses `copy()` instead of undoing moves. This is safer for Awale because a move can modify many parts of the game state: board, captures, scores, current player, and end state.

## 8. Heuristics

Two different heuristics are implemented in the `Awale` class.

### Score Heuristic

```python
heuristic_score(player)
```

This heuristic mainly evaluates the score difference between the player and the opponent. It also considers the difference in seeds remaining on the board.

General idea:

```text
10 * captured_score_difference + remaining_seed_difference
```

### Mobility Heuristic

```python
heuristic_mobility(player)
```

This heuristic evaluates the score difference and the number of legal moves available to each player.

General idea:

```text
8 * captured_score_difference + 2 * legal_move_difference
```

This second heuristic is different from the first because it gives importance to the player's ability to keep several playable options.

## 9. Sommet and MCTS

The `Sommet` class models a node in the MCTS search tree. Each node stores:

- a copy of the game state,
- a parent node,
- a list of children,
- the number of visits,
- the accumulated win score,
- the current player,
- the move that created the node.

The `MCTS` class implements Monte Carlo Tree Search with the following steps:

### Selection

The algorithm starts from the root and repeatedly chooses the child with the best UCT score.

### Expansion

If the selected node is not terminal, one unexplored legal move is chosen and added as a new child.

### Simulation

From the expanded node, the game is simulated using random moves until the game ends or a turn limit is reached.

### Backpropagation

The simulation result is propagated back through the parent nodes. A win gives `1.0`, a draw gives `0.5`, and a loss gives `0.0`.

The final move is chosen by selecting the child of the root with the highest number of visits.

## 10. Graphical Interface

The GUI is implemented with Tkinter.

It provides:

- a display of both players' pits,
- score display,
- current player display,
- opponent bot selection,
- a new game button,
- highlighted last move,
- animated seed sowing.

The GUI allows a human player to play against:

- `StupidBot`,
- `GreedyBot`,
- `MinMax`,
- `MCTS`.

For responsiveness, the GUI uses lighter AI parameters than the statistics mode.

## 11. Statistics

Automatic matches can be launched from the command line:

```powershell
python main.py --minmax-depth 2 --mcts-iterations 100 stats --games-count 100
```

The statistics mode compares player types two by two. It alternates the starting player to study the influence of playing first.

The result dictionary separates global matchup results from starting-player influence:

- `player1_wins`: wins by the first strategy passed to the comparison.
- `player2_wins`: wins by the second strategy passed to the comparison.
- `starter_wins`: wins by the player who started the game.
- `second_player_wins`: wins by the player who played second.
- `kind1_wins_as_starter` and `kind1_wins_as_second`: detailed results for the first strategy.
- `kind2_wins_as_starter` and `kind2_wins_as_second`: detailed results for the second strategy.

Example table to complete after running experiments:

| Matchup | Player 1 Wins | Player 2 Wins | Draws |
| --- | ---: | ---: | ---: |
| StupidBot vs GreedyBot | 2 | 97 | 1 |
| StupidBot vs MinMax | 0 | 100 | 0 |
| StupidBot vs MCTS | 1 | 99 | 0 |
| GreedyBot vs MinMax | 50 | 50 | 0 |
| GreedyBot vs MCTS | 31 | 61 | 8 |
| MinMax vs MCTS | 88 | 11 | 1 |

Starting-player influence:

| Matchup | Starter Wins | Second Player Wins | Draws |
| --- | ---: | ---: | ---: |
| StupidBot vs GreedyBot | 48 | 51 | 1 |
| StupidBot vs MinMax | 50 | 50 | 0 |
| StupidBot vs MCTS | 49 | 51 | 0 |
| GreedyBot vs MinMax | 0 | 100 | 0 |
| GreedyBot vs MCTS | 47 | 45 | 8 |
| MinMax vs MCTS | 46 | 53 | 1 |

These results show that stronger strategies generally outperform `StupidBot`. They also show that the starting-player advantage is not uniform. In the `GreedyBot vs MinMax` matchup, the second player won every game in this experiment, while other matchups were more balanced between starter and second player.

## 12. Limits and Possible Improvements

Some possible improvements:

- add more MinMax heuristics,
- use the greedy strategy as the MCTS simulation policy,
- add more detailed rule tests,
- improve the GUI layout,
- increase MinMax depth and MCTS iterations for stronger play.

The current implementation keeps the AI parameters moderate in order to keep automatic statistics and GUI games responsive.
