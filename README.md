# MLB: What to Watch

> People ask me what I do in winter when there's no baseball. I'll tell you what I do. I stare out the window and wait for spring. -Roger Hornsby

**Spoiler-free tagging of old MLB games to guide you in what's fun to watch**

For folx in the UTC±2 TZ, MLB games are generally inconveniently late, and you often end up watching them the next day. Maybe it's a good day and the Jays are on a winning streak, maybe they're travelling today and you just want to watch A game, ANY game, something fun!

This repo provides a script to tag games based on which ones might be interesting to watch, depending on your mood. By default it'll fetch the box scores for yesterday and tag them based on several criteria in a way that *should* be spoiler free.

```
$ python what2watch.py
        Boston Red Sox @ Chicago White Sox      high-scoring, big-inning, comeback, extra-innings, flip-flop
  San Francisco Giants @ Chicago Cubs           high-scoring, big-inning
         Texas Rangers @ Oakland Athletics      big-inning, comeback
     Toronto Blue Jays @ Baltimore Orioles      high-scoring, comeback
      New York Yankees @ New York Mets          big-inning, comeback
     Toronto Blue Jays @ Baltimore Orioles      high-scoring, big-inning
  Washington Nationals @ Pittsburgh Pirates     high-scoring
       Cincinnati Reds @ St. Louis Cardinals    comeback
      Colorado Rockies @ Philadelphia Phillies
     Milwaukee Brewers @ Cleveland Indians
        Tampa Bay Rays @ Detroit Tigers
    Los Angeles Angels @ Houston Astros
    Kansas City Royals @ Minnesota Twins
         Miami Marlins @ Atlanta Braves
      San Diego Padres @ Los Angeles Dodgers
  Arizona Diamondbacks @ Seattle Mariners
```

Alternatively you can provide a specific date:

```
$ python what2watch.py --date 2021-04-01
```

Providing the `--json` flag returns machine readable data:

```
$ python what2watch.py --date 2021-09-11 --json
[
  {"home_abbr": "CHC", "away_abbr": "SFG", "home_name": "Chicago Cubs", "away_name": "San Francisco Giants", "time": "1:20 p.m. Local", "tags": ["high-scoring", "big-inning"]},
  {"home_abbr": "OAK", "away_abbr": "TEX", "home_name": "Oakland Athletics", "away_name": "Texas Rangers", "time": "1:07 p.m. Local", "tags": ["big-inning", "comeback"]},
  ...
]
```

## Tags

Tag                   | Metric
---                   | ---
`pitchers-duel`       | final score ≤2 for both sides
`high-scoring`        | Combined run count over 15 OR one side ≥ 9
`comeback`            | One side is behind by ≥4 and then comes within -1 point or beats
`big-inning`          | More than 5 runs in one inning
`flip-flop`           | Lead changes more than 3 times
`extra-innings`       | >9 innings
`extra-extra-innings` | ≥13 innings


## License

AGPL-3.0-OR-LATER
