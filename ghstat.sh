#!/usr/bin/env bash
set -eo pipefail
usage() {
  cat <<EOF
Usage:
  ghstat.sh
Env:
  REPO_SLUGS  : list of repos
  USER  : username to automatically search repos for
  USER_RSKIP  : list of repos to skip (when USER is given)
  AUTHOR  : git log --author
  GITHUB_TOKEN
EOF
}
if [[ -z "$USER$REPO_SLUGS" || -z "$AUTHOR" || -z "$GITHUB_TOKEN" ]]; then
  usage
  exit 1
fi
this="$(dirname $0)"

getrepos() { # <user>
  gh api --paginate users/$1/repos | jq -r '.[].full_name'
}
getprs() { # <user>
  gh api --paginate "search/issues?q=is:pr+author:$1+is:merged" |
    jq -r '.items[].repository_url | sub(".*github.com/repos/"; "")'
}
getsubs() { # <user>
  gh api --paginate users/$1/subscriptions | jq -r '.[].full_name'
}
getorgs() { # <user>
  gh api --paginate users/$1/orgs | jq -r '.[].login'
}
getorgrepos() { # <org>
  gh api --paginate orgs/$1/repos | jq -r '.[].full_name'
}
iscontrib() { # <user> <repo>
  if [[ $(gh api --paginate repos/$2/contributors | jq "[.[].login | test(\"$1\")] | any") == "true" ]]; then
    echo $2
  fi
}

if [[ -n "$USER" ]]; then
  echo 1>&2 "[1/4] detecting repos"
  repos="$(
    getrepos $USER | tqdm --desc "> [1/5] user repos" --unit repos
    getprs $USER | tqdm --desc "> [2/5] pulls" --unit PRs
    getsubs $USER | tqdm --desc "> [3/5] watching" --unit repos
    for org in "$(getorgs $USER | tqdm --desc "> [4/5] membership" --unit orgs)"; do
      getorgrepos $org
    done | tqdm --desc "> [4/5] org repos" --unit repos
  )"
  repos="$(echo "$repos" | sort -u | comm -23 - <(for i in $REPO_SLUGS; do echo $i; done | sort -u))"
  repos="$(echo "$repos" | sort -u | comm -23 - <(for i in $USER_RSKIP; do echo $i; done | sort -u))"
  total="$(echo $repos | wc -w)"
  REPO_SLUGS="$REPO_SLUGS $(
    i=0
    for repo in $repos; do
      i=$((i + 1))
      iscontrib $USER $repo |
        tqdm --bar-format "[2/4] querying detected: $i/$total: $repo: {n} ({elapsed})"
    done
  )"
fi

for repo in ${REPO_SLUGS}; do
  [[ -d "$this/$repo" ]] || git clone --single-branch https://${GITHUB_TOKEN}@github.com/$repo "$this/$repo" 2>&1 >>/dev/null
  echo $repo
done | tqdm --desc "[3/4] clone" --unit repos --null

[[ -f languages.yml ]] || wget https://github.com/github/linguist/raw/master/lib/linguist/languages.yml
for repo in ${REPO_SLUGS}; do
  git -C "$this/$repo" log --format="" -M -C -C --author="$AUTHOR" --numstat |
    sed -r "s/(\t.*\t)/\1${this/\//\\\/}\/${repo/\//\\\/}\//"
done |
  tqdm --desc "[4/4] processing" --unit commits |
  python "$this/ghstat.py"
