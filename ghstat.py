import sys, os, collections, re, functools, subprocess
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
        lang_names[ext.lstrip(".")] = lang
        lang_colours[lang] = v.get("color", None)


re_lang = re.compile(r"^\s*language:\s+(.*)", flags=re.M).search
def fn2lang(fn):
    try:
        assert os.path.exists(fn)
        res = subprocess.check_output(["github-linguist", fn]).decode("U8")
        return re_lang(res).group(1)
    except:
        ext = os.path.basename(fn).rsplit(".", 1)[-1]
        return lang_names.get(ext, ext)  # TODO actually use fn & langs.*.


clean = functools.partial(re.compile(r"\{.*? => (.*?)\}").sub, r"\1")
clean_whole = functools.partial(re.compile(r".*? => (.*?)").sub, r"\1")
stats = sum(
    (
        collections.Counter(
            (fn2lang(clean_whole(clean(f.rstrip()))),) * int(c)
        )
        for i in sys.stdin
        for c, f in [i.split("\t")[::2]]
        if c != "-"
    ),
    collections.Counter(),
)

d = sorted(
    (
        (k, v)
        for k, v in stats.items()
        if k.lower() not in {"licence", "license", "postscript", "csv", "svg",}
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
