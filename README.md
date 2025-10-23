# ghstat

Automatically plot total lines of code (LoC) written.

![](https://gist.githubusercontent.com/casperdcl/aac90b8313a905e146459c81cabade7d/raw/ghstats-5.svg)

![](https://gist.githubusercontent.com/casperdcl/aac90b8313a905e146459c81cabade7d/raw/ghstats-a.png)

<details><summary>Full breakdown</summary><img src="https://gist.githubusercontent.com/casperdcl/aac90b8313a905e146459c81cabade7d/raw/ghstats-b-full.png"/></details>

## Usage

### Workflow

Requirements:

- `python3`
  + e.g. `uses: actions/setup-python@v2`
- secrets
  + a [personal access token][PAT] with scopes:
    + `repo`
    + `read:user` (optional)
    + `gist` (optional)
  + a [gist] ID which will store the generated graphs (optional)

[PAT]: https://github.com/settings/tokens
[gist]: https://docs.github.com/en/free-pro-team@latest/github/writing-on-github/editing-and-sharing-content-with-gists

Example:

```yaml
name: ghstat
on:
  push:
  schedule:
    - cron: '0 0 * * *'  # every midnight
jobs:
  ghstat:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/setup-python@v2
    - uses: casperdcl/ghstat@v2
      with:
        github-token: ${{ secrets.GH_TOKEN }}
        gist-id: ${{ secrets.GIST_ID }}
        # user: casperdcl  # default inferred from github-token
        # author: 'Casper da Costa-Luis'  # for `git log --author`, default inferred
        # repos-incl: '' # space separated list (e.g. myuser/arepo myorg/arepo)
        # repos-skip: '' # space separated list (e.g. myuser/arepo myorg/arepo conda-forge)
        # lang-names: '' # space separated list (e.g. conf:INI cuh:Cuda)
```

Using a `GIST_ID` of `aac90b8313a905e146459c81cabade7d`, the result is visible at https://gist.github.com/casperdcl/aac90b8313a905e146459c81cabade7d.

### Running locally

Python and `${GH_TOKEN}` are required; other env vars are optional.

```bash
python -m pip install -r requirements.txt
GH_TOKEN=... \
  AUTHOR=... \
  GH_USER=... \
  REPOS_INCL=... \
  REPOS_SKIP=... \
  GH_GIST_ID=... \
  LANG_NAMES=... \
  bash ghstat.sh
```
