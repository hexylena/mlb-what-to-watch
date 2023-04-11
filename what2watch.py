import json
import glob
import random
import os
from datetime import datetime, timedelta
from sportsipy.mlb.boxscore import Boxscores, Boxscore
import argparse
import itertools


TAG_DEFS = {
    'pitchers-duel': 'Both of the teams scored ≤2 runs.',
    'high-scoring': 'Either the combined run count was over 15, or at least one side was over 9.',
    'big-inning': 'More than 5 runs in a single inning',
    'comeback': 'After trailing by ≥4 runs, a team comes back to within 1 run or surpasses.',
    'extra-innings': '>9 innings.',
    'extra-extra-innings': '≥13 innings.',
    'flip-flop': 'The lead changes more than 3 times.'
}

TAG_COLORS = {
    k: f'#{c[0]}{c[0]}{c[1]}{c[1]}{c[2]}{c[2]}'
    for k, c
    in zip(sorted(TAG_DEFS.keys()), itertools.permutations('FCAF', 3))
}

HASHTAGS = {
    "ARI": "Diamondbacks",
    "ATL": "Braves",
    "BAL": "Orioles",
    "BOS": "RedSox",
    "CHC": "Cubs",
    "CHW": "WhiteSox",
    "CIN": "Reds",
    "CLE": "Guardians",
    "COL": "Rockies",
    "DET": "Tigers",
    "HOU": "Astros",
    "KCR": "Royals",
    "LAA": "Angels",
    "LAD": "Dodgers",
    "MIA": "Marlins",
    "MIL": "Brewers",
    "MIN": "Twins",
    "NYM": "Mets",
    "NYY": "Yankees",
    "OAK": "Athletics",
    "PHI": "Phillies",
    "PIT": "Pirates",
    "SDP": "Padres",
    "SEA": "Mariners",
    "SFG": "Giants",
    "STL": "Cardinals",
    "TBR": "Rays",
    "TEX": "Rangers",
    "TOR": "BlueJays",
    "WSN": "Nationals",
}

def getBoxscore(then):
    if not os.path.exists('data'):
        os.makedirs('data')
    fn = f"data/{then.isoformat()}.json"
    if os.path.exists(fn):
        with open(fn, "r") as handle:
            return json.load(handle)

    games_then = Boxscores(then)

    data = []
    for key in games_then.games.keys():
        print(key)
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
                    "home_hashtag": HASHTAGS[game["home_abbr"]],
                    "away_hashtag": HASHTAGS[game["away_abbr"]],
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
    if len(leads) > 3:
        t.append("flip-flop")

    # Extra innings
    if max(len(home), len(away)) >= 13:
        t.append('extra-extra-innings')
    elif max(len(home), len(away)) > 9:
        t.append('extra-innings')

    return t


def color4tag(tag):
    return TAG_COLORS[tag]


def renderPlain(data):
    out = ""
    for d in sorted(data, key=lambda x: -len(x['tags'])):
        where = f"{d['away_name']:>22s} @ {d['home_name']:<22s}"
        out += f"{where} {', '.join(d['tags'])}\n"
    return out

def renderToot(data, standalone, date):
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape()
    )
    template = env.get_template("mlb.toot")

    games = sorted(data, key=lambda x: -len(x['tags']))

    kw = dict(games=games, tag_defs=TAG_DEFS,
                standalone=standalone, date=date)
    return template.render(**kw)


def renderHtml(data, standalone, date):
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape()
    )
    template = env.get_template("mlb.html")

    games = sorted(data, key=lambda x: -len(x['tags']))

    with open('.git/refs/heads/main', 'r') as handle:
        git_commit = handle.read().strip()[0:12]

    kw = dict(games=games, tag_defs=TAG_DEFS,
                color=color4tag, git_commit=git_commit,
                standalone=standalone, date=date)

    return template.render(**kw)


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
        "--toot",
        action='store_true',
        help='Send toot.'
    )
    parser.add_argument(
        "--sesv2",
        action='store_true',
        help='Return output in sesv2 json'
    )
    parser.add_argument(
        "--github-pages",
        action='store_true',
        help='Make the HTML report standalone (head/body/etc.) and store it in docs'
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

    print(then)

    data = getBoxscore(then)
    for d in data:
        d['tags'] = tags(d['box'])
        del d['box']

        if 'home_hashtag' not in d:
            d.update({
                "home_hashtag": HASHTAGS[d["home_abbr"]],
                "away_hashtag": HASHTAGS[d["away_abbr"]],
            })

    if args.json:
        print(json.dumps(data))
    elif args.toot:
        from mastodon import Mastodon
        server = 'https://galaxians.garden'
        token = os.environ['FEDI_ACCESS_TOKEN']
        mastodon = Mastodon(
            access_token = token,
            api_base_url = server
        )
        tooter = mastodon.toot(renderToot(data, True, then))
        print("tooted: ", tooter['uri'])
    elif args.html:
        if args.github_pages:
            with open(f'docs/{then.isoformat()}.html', 'w') as handle:
                handle.write(renderHtml(data, True, then))

            with open(f'docs/index.md', 'w') as handle:
                handle.write("# MLB: What to Watch\n\n")
                for f in sorted(glob.glob("docs/*.html")):
                    handle.write(f"- [{f[5:-5]}]({f[5:]})\n")
        else:
            print(renderHtml(data, False, then))
    elif args.sesv2:
        # import boto3
        # from botocore.exceptions import ClientError
        SENDER = "Galaxians Sports <mlb@galaxians.org>"
        AWS_REGION = "eu-central-1"
        SUBJECT = "MLB: What to Watch"
        CHARSET = "UTF-8"
        # client = boto3.client('ses',region_name=AWS_REGION)
        # # Try to send the email.
        # try:
            # #Provide the contents of the email.
            # response = client.send_email(
        z = dict(
            ListManagementOptions={
                'ContactListName': 'HelkiaContactList',
                'TopicName': 'MLB-W2W'
            },
            Destination={
                'ToAddresses': ["helena.rasche+blah@gmail.com"]
            },
            Content={
                'Simple': {
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': renderHtml(data, False, then),
                        },
                        'Text': {
                            'Charset': CHARSET,
                            'Data': renderPlain(data),
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                }
            },
            FromEmailAddress=SENDER,
        )
        print(json.dumps(z))
        # Display an error if something goes wrong.
        # except ClientError as e:
            # print(e.response['Error']['Message'])
        # else:
            # print("Email sent! Message ID:"),
            # print(response['MessageId'])

    else:
        print(renderPlain(data))
