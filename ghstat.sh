#!/usr/bin/env bash
set -eo pipefail
usage() {
  cat <<EOF
Usage:
  ghstat.sh
Env:
  GH_TOKEN    : must have read access to all repos
  AUTHOR      : git log --author
  GH_USER     : username to automatically search repos for
  REPOS_INCL  : list of repos
  REPOS_SKIP  : list of repos to skip (when GH_USER is given)
EOF
}
ghjq() { # <endpoint> <filter>
  # filter all pages of authenitcated requests to https://api.github.com
  gh api --paginate "$1" | jq -r "$2"
}

if [[ -z "$GH_USER" && -n "$GH_TOKEN" ]]; then
  GH_USER=$(ghjq user .login)
fi
if [[ -z "$GH_USER$REPOS_INCL" || -z "$AUTHOR" || -z "$GH_TOKEN" ]]; then
  usage
  exit 1
fi
this="$(dirname $0)"

getrepos() { # <user>
  ghjq users/$1/repos .[].full_name
}
getprs() { # <user>
  ghjq "search/issues?q=is:pr+author:$1+is:merged" \
    '.items[].repository_url | sub(".*github.com/repos/"; "")'
}
getsubs() { # <user>
  ghjq users/$1/subscriptions .[].full_name
}
getorgs() { # <user>
  ghjq users/$1/orgs .[].login
}
getorgrepos() { # <org>
  ghjq orgs/$1/repos .[].full_name
}
iscontrib() { # <user> <repo>
  if [[ $(ghjq repos/$2/contributors "[.[].login | test(\"$1\")] | any") == "true" ]]; then
    echo $2
  fi
}

if [[ -n "$GH_USER" ]]; then
  echo 1>&2 "[1/4] detecting repos"
  repos="$(
    getrepos $GH_USER | tqdm --desc "> [1/5] user repos" --unit repos
    getprs $GH_USER | tqdm --desc "> [2/5] pulls" --unit PRs
    getsubs $GH_USER | tqdm --desc "> [3/5] watching" --unit repos
    for org in "$(getorgs $GH_USER | tqdm --desc "> [4/5] membership" --unit orgs)"; do
      getorgrepos $org
    done | tqdm --desc "> [4/5] org repos" --unit repos
  )"
  repos="$(echo "$repos" | sort -u | comm -23 - <(for i in $REPOS_INCL; do echo $i; done | sort -u))"
  repos="$(echo "$repos" | sort -u | comm -23 - <(for i in $REPOS_SKIP; do echo $i; done | sort -u))"
  total="$(echo $repos | wc -w)"
  REPOS_INCL="$REPOS_INCL $(
    i=0
    for repo in $repos; do
      i=$((i + 1))
      iscontrib $GH_USER $repo |
        tqdm --bar-format "[2/4] querying detected: $i/$total: $repo: {n} ({elapsed})"
    done
  )"
fi

for repo in ${REPOS_INCL}; do
  [[ -d "$this/$repo" ]] || git clone --single-branch https://${GH_TOKEN}@github.com/$repo "$this/$repo" 2>&1 >>/dev/null
  echo $repo
done | tqdm --desc "[3/4] clone" --unit repos --total $(echo $REPOS_INCL | wc -w) --mininterval 5 --null

[[ -f languages.yml ]] || wget https://github.com/github/linguist/raw/master/lib/linguist/languages.yml
for repo in ${REPOS_INCL}; do
  git -C "$this/$repo" log --format="" -M -C -C --author="$AUTHOR" --numstat |
    sed -r "s/(\t.*\t)/\1${this/\//\\\/}\/${repo/\//\\\/}\//"
done |
  tqdm --desc "[4/4] processing" --unit commits |
  python "$this/ghstat.py"
