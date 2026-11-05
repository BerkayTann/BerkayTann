"""GitHub GraphQL API'den profil verisini çeker ve JSON'a yazar.

Kullanım:  GH_USER=BerkayTann GH_TOKEN=... python generators/fetch_data.py out.json
           python generators/fetch_data.py out.json --mock     (sahte veriyle test)
Not: Özel repo katkılarının sayılması için GH_TOKEN bir PAT olmalı (read:user + repo)
ve profilde "Private contributions" açık olmalı.
"""
import datetime as dt
import json
import os
import random
import sys
import urllib.request

API = "https://api.github.com/graphql"


def gql(token, query, variables=None):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-readme"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    if "errors" in data:
        raise SystemExit(f"GraphQL hatası: {data['errors']}")
    return data["data"]


CAL = "contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}"


def fetch(user, token):
    base = gql(token, """query($l:String!){user(login:$l){createdAt followers{totalCount}
      repositories(ownerAffiliations:OWNER,isFork:false,first:100,orderBy:{field:PUSHED_AT,direction:DESC}){totalCount nodes{stargazerCount
        languages(first:6,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}""", {"l": user})["user"]
    created = dt.datetime.fromisoformat(base["createdAt"].replace("Z", "+00:00")).year
    now = dt.datetime.now(dt.timezone.utc)
    parts = []
    for y in range(created, now.year + 1):
        parts.append(f'y{y}:contributionsCollection(from:"{y}-01-01T00:00:00Z",to:"{y}-12-31T23:59:59Z")'
                     f'{{totalCommitContributions totalPullRequestContributions totalIssueContributions restrictedContributionsCount {CAL}}}')
    cols = gql(token, "query($l:String!){user(login:$l){" + " ".join(parts) + "}}", {"l": user})["user"]
    days, years, commits, prs, issues = {}, {}, 0, 0, 0
    for key, c in cols.items():
        y = int(key[1:])
        years[y] = c["contributionCalendar"]["totalContributions"]
        for w in c["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                if d["date"].startswith(str(y)):
                    days[d["date"]] = d["contributionCount"]
        if y >= now.year - 1:  # son iki takvim yılı
            commits += c["totalCommitContributions"]
            prs += c["totalPullRequestContributions"]
            issues += c["totalIssueContributions"]
    langs, stars = {}, 0
    for r in base["repositories"]["nodes"]:
        stars += r["stargazerCount"]
        for e in r["languages"]["edges"]:
            n = e["node"]
            langs.setdefault(n["name"], [0, n["color"] or "#8b949e"])
            langs[n["name"]][0] += e["size"]
    return {"user": user, "repos": base["repositories"]["totalCount"], "stars": stars, "followers": base["followers"]["totalCount"],
            "commits": commits, "prs": prs, "issues": issues, "years": years, "days": days,
            "langs": sorted(([k, v[0], v[1]] for k, v in langs.items()), key=lambda x: -x[1])}


def mock(user):
    rnd = random.Random(3)
    today = dt.date.today()
    days, years = {}, {}
    d = today - dt.timedelta(days=3 * 365)
    while d <= today:
        c = rnd.choice([0, 0, 0, 1, 2, 3, 5, 8]) if d < today - dt.timedelta(days=9) else rnd.choice([1, 2, 4, 6])
        days[d.isoformat()] = c
        years[d.year] = years.get(d.year, 0) + c
        d += dt.timedelta(days=1)
    return {"user": user, "repos": 27, "stars": 3, "followers": 5, "commits": 640, "prs": 12, "issues": 4, "years": years, "days": days,
            "langs": [["JavaScript", 52000, "#f1e05a"], ["TypeScript", 38000, "#3178c6"], ["C#", 21000, "#178600"], ["CSS", 9000, "#563d7c"], ["HTML", 6000, "#e34c26"]]}


if __name__ == "__main__":
    out = sys.argv[1]
    user = os.environ.get("GH_USER", "BerkayTann")
    data = mock(user) if "--mock" in sys.argv else fetch(user, os.environ["GH_TOKEN"])
    with open(out, "w") as f:
        json.dump(data, f)
    print(f"yazıldı: {out} ({len(data['days'])} gün, {len(data['years'])} yıl)")
