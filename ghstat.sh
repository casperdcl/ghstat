#!/usr/bin/env bash
set -eo pipefail
usage() {
  cat <<EOF
Usage:
  ghstat.sh
Env:
  REPO_SLUGS
  AUTHOR
  GITHUB_TOKEN
EOF
}
if [[ -z "$REPO_SLUGS" || -z "$AUTHOR" || -z "$GITHUB_TOKEN" ]]; then
  usage
  exit 1
fi
this="$(dirname $0)"

echo '[1/2] clone ...'
for repo in ${REPO_SLUGS}; do
  [[ -d "$this/$repo" ]] || git clone --single-branch https://${GITHUB_TOKEN}@github.com/$repo "$this/$repo"
done >>/dev/null

echo '[2/2] processing ...'
[[ -f languages.yml ]] || wget https://github.com/github/linguist/raw/master/lib/linguist/languages.yml
for repo in ${REPO_SLUGS}; do
  git -C "$this/$repo" log --format="" -M -C -C --author="$AUTHOR" --numstat | sed -r "s/(\t.*\t)/\1${this/\//\\\/}\/${repo/\//\\\/}\//"
done |
  python -m tqdm --unit commits |
  python "$this/ghstat.py"
