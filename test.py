is_latin = lambda ch: '\u0000' <= ch <= '\u007F' or '\u00A0' <= ch <= '\u024F'
is_nonspace_latin = lambda ch: is_latin(ch) and not ch.isspace() and not ch in "*()[]\{\}"
is_nonpunct_cjk = lambda ch: not is_latin(ch) and ch not in "·！￥…（）—【】、；：‘’“”，。《》？「」"

def beautify_string(text):
    res = ""
    for idx in range(len(text)):
        if idx and (
            (is_nonspace_latin(text[idx])     and is_nonpunct_cjk(text[idx - 1])) or
            (is_nonspace_latin(text[idx - 1]) and is_nonpunct_cjk(text[idx]))
        ): res += " "
        res += text[idx]
    return res

for i in range(1, 10):
	content = open(f"./src/content/blog/2025-04-0{i}/index.md", "r", encoding="utf-8").read()
	open(f"./src/content/blog/2025-04-0{i}/index.md", "w+", encoding="utf-8").write(beautify_string(content))
