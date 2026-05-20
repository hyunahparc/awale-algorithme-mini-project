# Awale Project

Python implementation of the Awale game, following the object-oriented structure.

## Files

- `awale.py`: game model, board state, legal moves, sowing, capture rules, scores and heuristics.
- `players.py`: player classes: `Human`, `StupidBot`, `GreedyBot`, `MinMax`, `Sommet`, `MCTS`.
- `gui.py`: Tkinter graphical interface with pit selection, bot choice and sowing animation.
- `main.py`: command-line entry point for GUI, console games and statistics.

## Run

Start the GUI:

```powershell
python main.py gui
```

Start the GUI against a specific bot:

```powershell
python main.py gui --opponent minmax
python main.py gui --opponent mcts
```

Run one console game:

```powershell
python main.py game --player1 stupid --player2 greedy
python main.py game --player1 human --player2 minmax
```

Run statistics:

```powershell
python main.py stats --games-count 20
python main.py --minmax-depth 2 --mcts-iterations 100 stats --games-count 100
```

## Default Parameters

- Console/statistics MinMax depth: `2`
- GUI MinMax depth: `1`
- Console/statistics MCTS iterations: `100`
- GUI MCTS iterations: `50`
- Maximum turns per automatic game: `300`

The turn limit avoids abnormally long automatic games. If the limit is reached, the current score determines the winner.

## Implemented Players

- `Human`: chooses moves through console input or GUI clicks.
- `StupidBot`: chooses randomly among legal moves.
- `GreedyBot`: chooses the move with the best immediate capture.
- `MinMax`: uses MinMax with alpha-beta pruning and two heuristics.
- `MCTS`: uses Monte Carlo Tree Search with random simulations.

## MinMax Heuristics

- `heuristic_score`: evaluates the difference between captured seeds and remaining seeds.
- `heuristic_mobility`: evaluates score difference and legal move availability.

## MCTS

The MCTS implementation uses the following steps:

1. Selection with UCT.
2. Expansion of one unexplored move.
3. Random simulation until game end or turn limit.
4. Backpropagation of the result through the `Sommet` tree.

## GUI

The interface is built with Tkinter. It displays:

- the two rows of pits,
- current scores,
- current player,
- last played move,
- animated seed sowing,
- opponent bot selection.

## Useful Checks

Compile the files:

```powershell
python -m py_compile awale.py players.py main.py gui.py
```

Quick statistics test:

```powershell
python main.py stats --games-count 2
```
