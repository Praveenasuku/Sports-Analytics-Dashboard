# Data

`nba_elo.csv.gz` is a compact copy of **FiveThirtyEight's NBA Elo dataset**: every NBA and ABA game from 1946 to June 2015 (63,157 games), with each team's Elo rating before and after the game and FiveThirtyEight's pre-game win probability.

- Source: https://github.com/fivethirtyeight/data/tree/master/nba-elo
- License: Creative Commons Attribution 4.0 (CC BY 4.0), FiveThirtyEight
- Background: "The Complete History Of The NBA", FiveThirtyEight, 2015

Each game appears twice, once from each team's side (`_iscopy` = 0 or 1). Only the columns used by this project are kept. Rebuild the file from the source with:

```bash
python -c "from sports.data import download; download()"
```
