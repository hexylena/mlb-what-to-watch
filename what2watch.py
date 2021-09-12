import json
import os
from datetime import datetime, timedelta
from sportsipy.mlb.boxscore import Boxscores, Boxscore
import argparse


def getBoxscore(then):
    fn = f"data/{then.isoformat()}.json"
    if os.path.exists(fn):
        with open(fn, "r") as handle:
            return json.load(handle)

    games_then = Boxscores(then)

    data = []
    for key in games_then.games.keys():
        for game in games_then.games[key]:
            # print(game['home_abbr'], game['away_abbr'], game['boxscore'])
            box = Boxscore(game["boxscore"])
            # print(box, dir(box))
            data.append(
                {
                    "home_abbr": game["home_abbr"],
                    "away_abbr": game["away_abbr"],
                    "home_name": game["home_name"],
                    "away_name": game["away_name"],
                    "time": box.time,
                    "box": box.summary,
                }
            )

    with open(fn, "w") as handle:
        json.dump(data, handle)
    return data

def fN(d):
    return [0 if x is None else x for x in d]


def weave(home, away):
    cur_home = 0
    cur_away = 0
    for i, (h, a) in enumerate(zip(home, away)):
        cur_away = sum(away[0 : i + 1])
        yield ("top", "away", i + 1, cur_home, cur_away, getleader(cur_home, cur_away))
        cur_home = sum(home[0 : i + 1])
        yield ("bot", "home", i + 1, cur_home, cur_away, getleader(cur_home, cur_away))


def getleader(h, a):
    if h > a:
        return "home"
    elif a > h:
        return "away"
    else:
        return "none"


def tags(box):
    home = fN(box["home"])
    away = fN(box["away"])
    sh = sum(home)
    ah = sum(away)

    t = []
    # Boring game
    if sh <= 2 and ah <= 2:
        t.append("pitchers-duel")

    # High scoring (together over 15) OR (one side ≥ 9)
    if sh + ah > 15 or sh > 9 or ah > 9:
        t.append("high-scoring")

    # Big inning (more than 5 in one inning)
    if any(x >= 5 for x in home) or any(x >= 5 for x in away):
        t.append("big-inning")

    # comeback (one team is behind by ≥4 and then comes within -1 point or beats)
    comeback_condition = None
    comeback = False
    for tb, howy, inning, cur_home, cur_away, leader in weave(home, away):
        # print(tb, inning, comeback_condition, cur_away - cur_home)

        if comeback_condition is None:
            if abs(cur_home - cur_away) >= 4:
                comeback_condition = leader
        else:
            # If the leader has changed, or the leader hasn't, and the
            # difference has shrunk to 1 or 0 (i.e. trailing by 1, or tied.)
            if leader != comeback_condition or abs(cur_home - cur_away) <= 1:
                comeback = True

    if comeback:
        t.append("comeback")

    # Flip-flop (lead changes more than 3 times)
    leads = []
    for tb, howy, inning, cur_home, cur_away, leader in weave(home, away):
        # If our side is winning
        if cur_home > cur_away:
            # And the last inning we weren't winning (i.e. remove runs of the
            # same value, to make analysis simpler.)
            if len(leads) == 0 or leads[-1] != "home":
                leads.append("home")
        elif cur_away > cur_home:
            if len(leads) == 0 or leads[-1] != "away":
                leads.append("away")

    # Extra innings
    if max(len(home), len(away)) > 9:
        t.append('extra-innings')

    if max(len(home), len(away)) >= 13:
        t.append('extra-extra-innings')

    if len(leads) > 3:
        t.append("flip-flop")

    return t



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="What to watch: MLB")
    parser.add_argument(
        "--date",
        help="Must be ISO formatted date, e.g. 2021-12-31, defaults to yesterday",
    )
    parser.add_argument(
        "--html",
        action='store_true',
        help='Return output as HTML that could be sent in an email'
    )
    parser.add_argument(
        "--json",
        action='store_true',
        help='Return output in JSON'
    )
    args = parser.parse_args()

    if args.date:
        then = datetime.fromisoformat(args.date).date()
    else:
        # yesterday by default
        then = datetime.today().date() - timedelta(days=1)

    data = getBoxscore(then)
    for d in data:
        d['tags'] = tags(d['box'])
        del d['box']

    if args.json:
        print(json.dumps(data))
    elif args.html:
        print("A daily digest of what's worth your time<br /><br />")
        games = sorted(data, key=lambda x: -len(x['tags']))
        print("<b>Go on ball, get outta here ⚾️</b><br />")
        print("<table>")
        for i, d in enumerate([x for x in games if len(x['tags']) > 0]):
            bkg = "#ffffff" if i % 2 == 0 else "#f6f8fa"
            print(f"""<tr style="background-color: {bkg}"><td style="padding: 6px 13px; text-align: right; border: 1px solid #d0d7de"><b>{d['away_name']}</b></td><td style="border: 1px solid #d0d7de">@</td><td style="padding: 6px 13px;border: 1px solid #d0d7de"><b>{d['home_name']}</b></td> <td style="padding: 6px 13px;border: 1px solid #d0d7de">{d['time']}</td> <td style="padding: 6px 13px;border: 1px solid #d0d7de">{', '.join(d['tags'])}</td></tr>""")
        print("</table>")

        print("<br/><b>Probably not 👎</b><br />")
        for d in [x for x in games if len(x['tags']) == 0]:
            where = f"{d['away_name']:>22s} @ {d['home_name']:<22s}"
            print(f"{where} ({d['time']})<br />")

        print(f"""<br/><br/><a href="https://github.com/hexylena/mlb-what-to-watch">hexylena/mlb-what-to-watch</a>""")
    else:
        for d in sorted(data, key=lambda x: -len(x['tags'])):
            where = f"{d['away_name']:>22s} @ {d['home_name']:<22s}"
            print(f"{where} {', '.join(d['tags'])}")
