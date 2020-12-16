import sys, os, collections, re, functools
import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plt, tqdm, yaml


def ccycle():
    while True:
        for i in range(10):
            yield "C%d" % i


lang_names = {}
lang_colours = {}
langs = yaml.safe_load(open("languages.yml"))
for lang, v in langs.items():
    for ext in v.get("extensions", v.get("filenames", [])):
        ext = ext.lstrip(".")
        if ext in lang_names:
            lang_names[ext] = ext
            lang_colours[ext] = None
        else:
            lang_names[ext] = lang
        lang_colours[lang] = v.get("color", None)
lang_names.update(md="Markdown", mmd="Markdown", txt="Text", cfg="INI")
lang_names["1"] = "Roff"

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
    return lang_names.get(ext, ext)


stats = collections.Counter()
for k, v in (
    (fn2lang(f), int(c)) for i in sys.stdin for c, f in [i.split("\t")[::2]] if c != "-"
):
    stats[k] += v

d = sorted(
    (
        (k, v)
        for k, v in stats.items()
        if k.lower() not in {"licence", "license", "postscript", "csv", "svg"}
    ),
    key=lambda kv: kv[1],
    reverse=True,
)
print(d)

# plt.barh([i for i, _ in d], [i for _, i in d], log=True)
# plt.xlabel("inserted lines")
# plt.ylabel("extension")

thresh = sum(v for _, v in d) * 0.005
o = [(k, v) for k, v in d if v < thresh]
d = [(k, v) for k, v in d if v >= thresh] + [("Other", sum(dict(o).values()))]

plt.figure(figsize=(14, 7))

plt.subplot(121)
c = ccycle()
plt.pie(
    [v for _, v in d],
    labels=[
        "{} {}".format(k, tqdm.tqdm.format_sizeof(v) if v > 99 else v) for k, v in d
    ],
    colors=[lang_colours.get(k) or next(c) for k, _ in d],
)
plt.title("Inserted lines (99.5%)")

plt.subplot(122)
c = ccycle()
plt.pie(
    [v for _, v in o],
    labels=[
        "{} {}".format(k, tqdm.tqdm.format_sizeof(v) if v > 99 else v) for k, v in o
    ],
    colors=[lang_colours.get(k) or next(c) for k, _ in o],
)
plt.title("Other (0.5%)")

plt.tight_layout()
plt.savefig("ghstats.png")
