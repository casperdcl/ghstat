"""
Plot graphs of lines of code per language.
Requires stdin from `git log --format="" --numstat`.

Usage:
  ghstat [options] [<lang_names>...]

Options:
  --output-svg FILE  : [default: ghstats-5.svg]
  --output-pie FILE  : [default: ghstats-a.png]
  --output-barh FILE  : [default: ghstats-b-full.png]
  --log LEVEL  : [default: INFO]

Arguments:
  <lang_names>  : mapping extension to name (e.g. "conf:INI")
"""
import collections
import functools
import logging
import os
import re
import sys
from math import sqrt

import matplotlib.pyplot as plt
import yaml
from argopt import argopt
from tqdm import tqdm

log = logging.getLogger("ghstat")

try:
    langs = yaml.safe_load(open("languages.yml"))
except FileNotFoundError:
    log.error(
        "please download"
        " https://github.com/github/linguist/raw/master/lib/linguist/languages.yml"
    )
    raise


def ccycle():
    """`matplotlib` colour cycle generator"""
    while True:
        for i in range(10):
            yield "C%d" % i


@functools.lru_cache()
def warn_unknown(ext):
    """warns at most once about a given file extension"""
    log.warning("Unknown extension:%s", ext)


class TqdmStream:
    """`tqdm`-safe logging stream"""

    @staticmethod
    def write(msg):
        tqdm.write(msg, end="")

    @staticmethod
    def flush():
        sys.stderr.flush()


args = argopt(__doc__).parse_args()
logging.basicConfig(
    level=getattr(logging, args.log.upper(), logging.INFO), stream=TqdmStream
)
log.debug(args)
lang_names = {}
lang_colours = {}
for lang, v in langs.items():
    for ext in v.get("extensions", v.get("filenames", [])):
        ext = ext.lstrip(".")
        if ext in lang_names:
            lang_names[ext] = ext
            lang_colours[ext] = None
        else:
            lang_names[ext] = lang
        lang_colours[lang] = v.get("color", None)
lang_names.update(
    md="Markdown",
    mmd="Markdown",
    txt="Text",
    cfg="INI",
    dvc="DVC",
    h="C++",
    latex="TeX",
    bashrc="Shell",
    profile="Shell",
    php="PHP",
    m="Matlab",
    makefile="Makefile",
    gradlew="Gradle",
    gitmodules="Git Config",
    mailmap="Git Attributes",
    dockerignore="Dockerfile",
    licence=".skip",
    license=".skip",
    pdf=".skip",
    csv=".skip",
    svg=".skip",
    eps=".skip",
)
lang_names["1"] = "Roff"
lang_names.update(i.split(":", 1) for i in args.lang_names)
lang_dflt = lang_names.get(".default", None)  # None for ext.lower()

clean = functools.partial(re.compile(r"\{.*? => (.*?)\}").sub, r"\1")
clean_whole = functools.partial(re.compile(r".*? => (.*?)").sub, r"\1")


def fn2lang(fn):
    fn = os.path.basename(clean_whole(clean(fn.rstrip())))
    if "." in fn:
        base, ext = fn.rsplit(".", 1)
    else:
        base, ext = "", fn
    if base.lower().startswith("cmake") and ext.lower() == "txt":
        return "CMake"
    if base == "" and ext.lower().startswith("bash_"):
        return "Shell"
    res = lang_names.get(ext, lang_names.get(ext.lower(), None))
    if not res:
        warn_unknown(ext)
        return lang_dflt or ext.lower()
    return res


stats = collections.Counter()
for k, v in (
    (fn2lang(f), int(c)) for i in sys.stdin for c, f in [i.split("\t")[::2]] if c != "-"
):
    stats[k] += v
log.info("skipping: %d lines", stats.pop(".skip", 0))

d = sorted(
    ((k, v) for k, v in stats.items() if v > 0), key=lambda kv: kv[1]  # reverse=True,
)
log.info(d)

plt.figure(figsize=(8, len(d) * 1 / 5 + 1))
c = ccycle()
values = [v for _, v in d]
labels = [k + " " + (tqdm.format_sizeof if v > 99 else str)(v) for k, v in d]
colours = [lang_colours.get(k) or next(c) for k, _ in d]
total = sum(values)
plt.barh(range(len(values)), values, tick_label=labels, color=colours, log=True)
[i.set(backgroundcolor="#ffffff80") for i in plt.gca().get_yticklabels()]
plt.gca().xaxis.tick_top()
plt.gca().xaxis.set_label_position("top")
plt.xlabel("%s lines of code written" % tqdm.format_sizeof(total))
plt.ylim(-0.5, len(d) - 0.5)
plt.tight_layout()
plt.savefig(args.output_barh, transparent=True)

plt.figure(figsize=(8, 8))
value_other = sum(values[:-15])
plt.pie(
    values[-15:] + [value_other],
    labels=labels[-15:]
    + ["Other " + (tqdm.format_sizeof if value_other > 99 else str)(value_other)],
    colors=colours[-15:] + ["black"],
    textprops={"backgroundcolor": "#ffffff80"},
)
plt.title("%s lines of code written" % tqdm.format_sizeof(total))
plt.tight_layout()
plt.savefig(args.output_pie, transparent=True)

# SVG
width = 800
svg_bars = [
    (k, sqrt(v) * width / sum(map(sqrt, values)), c)
    for k, v, c in zip(labels, values, colours)
][::-1]


def svg_langbar(offset, title, width, colour):
    # <rect x="{offset}" y="8" width="{width}" height="10" fill="white"/>
    return f"""
  <rect mask="url(#ghstat-bar)" x="{offset}" y="0"
   width="{width}" height="8" fill="{colour}"/>
  <text x="{offset}" y="16" font-family="Monospace" font-size="8" fill="black"
   transform="rotate({25 if len(title) * 7 > width else 0}, {offset}, 16)"
   >{title}</text>"""


svg_bars = "".join(
    svg_langbar(sum(v for _, v, _ in svg_bars[:i]), *svg_bars[i])
    for i in range(len(svg_bars))
).lstrip()
with open(args.output_svg, "w") as fd:
    fd.write(
        f"""
<svg class="bar" xmlns="http://www.w3.org/2000/svg" width="{width}" height="48">
  <mask id="ghstat-bar">
    <rect x="0" y="0" width="{width}" height="8" fill="white" rx="5"/>
  </mask>
  <rect mask="url(#ghstat-bar)" x="0" y="0" width="{width}" height="8" fill="#d1d5da"/>
  {svg_bars}
</svg>
"""
    )
