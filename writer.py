from openai import OpenAI
from bs4 import BeautifulSoup
import requests
import random
import time
import datetime
import os
import glob
import yaml
import re
import subprocess
import tempfile

path_to = f'src/content/blog/{datetime.datetime.now().strftime("%Y-%m-%d")}'

if os.path.exists(path_to):
    print(f"   Skipping directory: {path_to}")
    exit(0)
else:
    os.makedirs(path_to, exist_ok=True)
    print(f"     Making directory: {path_to}")

start = time.time()
print("    Connecting remote:")
deepseek = OpenAI(base_url="https://api.deepseek.com", api_key=os.environ.get("DS_APIKEY"))
print(f"   Time spent on init: {time.time() - start:.1f} s")

def generate(context, provider, model):
    completion = provider.chat.completions.create(
        model=model,
        messages=context
    )
    return completion.choices[0].message.content.strip()

def scrape_website(url, css_selector):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        elements = soup.select(css_selector)
        return elements
    else: return []

# Get existing blog posts
def get_existing_blog_posts():
    blog_posts = []
    blog_paths = glob.glob("src/content/blog/*/index.md")

    for path in blog_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Parse frontmatter
                if content.startswith('---'):
                    _, frontmatter, markdown = content.split('---', 2)
                    metadata = yaml.safe_load(frontmatter)
                    blog_posts.append({
                        'title': metadata.get('title', ''),
                        'description': metadata.get('description', '')
                    })
        except Exception as e:
            print(f"        Error reading: {path}; {e}")

    return blog_posts

# Get existing blog posts
existing_posts = get_existing_blog_posts()
existing_posts_text = "\n".join([post["title"] for post in existing_posts])
print(f"              Loading: {len(existing_posts)} existing blog posts")

topics = [topic.get_text(strip=True) for topic in scrape_website("https://news.ycombinator.com/", ".titleline")]
topics_text = "\n".join(random.choices(topics, k=random.randint(5, len(topics))))
print(f"              Scraped: {len(topics)} topics")

def extract_topic(topics):
    global deepseek, existing_posts_text
    return generate([
        {"role": "system", "content": "你在为一篇技术博客确定一个主题。直接用中文输出主题。"},
        {"role": "user", "content": f"阅读以下是HackerNews的热门文章，然后写一个可以用于技术博客的主题。这个主题应当是一个通用、普通的技术，不能是一个事件或其它东西。\n\n{topics}\n\n以下是已有的博客文章，请避免选择相似的主题：\n{existing_posts_text}\n\n只需要一个主题，直接输出。"},
    ], deepseek, "deepseek-chat")

def outline(topic):
    global deepseek
    return generate([
        {"role": "user", "content": f"我要写一篇关于「{topic}」的博客文章。帮我列一个详细的文章提纲。"}
    ], deepseek, "deepseek-reasoner")

def write_from_outline(outline):
    global deepseek, existing_posts_text
    return generate([
        {"role": "system", "content": "你是一位专业技术博客作者。在写作时请遵循以下中文排版规范：使用全角中文标点；专有名词大小写正确；英文、数字使用半角字符；使用直角引号「」。"},
        {"role": "user", "content": f"{outline}\n\n根据这个提纲中关于技术知识的部分，写出一篇技术博客文章。文章中避免出现图片，不能使用任何列表。每一段出现的代码都进行较为详细的解读。在讲述内容时尽量使用段落的语言，语言风格可以略偏专业，但保持清晰。使用Markdown（要求符合Common Markdown规范）输出，使用LaTeX公式（注意：数学的开闭定界符前后不能有字母或数字字符。像x$a + b = c$或$a + b = c$1将无法渲染为数学公式（所有$会被渲染为$）；但x $\\infty$ 1和($\\infty$)会正常渲染），标题尽量只用一级标题 `#` 和二级标题 `##`，不要用分割线。请遵循中文排版规范，使用正确的标点符号。直接输出正文。"}
    ], deepseek, "deepseek-reasoner")

def summary(article):
    global deepseek
    return generate([
        {"role": "system", "content": "你是一个技术博客简介写作者，简介不一定需要涵盖文章的全部内容，能起到一定的提示作用即可。直接输出简介。遵循以下中文排版规范：使用全角中文标点；专有名词大小写正确；英文、数字使用半角字符。注意简介被作为副标题使用，不是一句句子，不要以句号结尾。"},
        {"role": "user", "content": f"给这篇文章写一个15字的简短介绍：\n\n{article}"}
    ], deepseek, "deepseek-chat")

# LaTeX error handling
def remove_latex_comments(latex_str: str) -> str:
    lines = latex_str.splitlines()
    cleaned_lines = []
    for line in lines:
        m = re.search(r'(?<!\\)%', line)
        if m:
            line = line[:m.start()]
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def check_balanced_braces(latex_str: str) -> (bool, list):
    stack = []
    errors = []
    for index, char in enumerate(latex_str):
        if char == '{':
            stack.append(index)
        elif char == '}':
            if not stack:
                errors.append(f"位置 {index}: 右大括号 '}}' 没有对应的左大括号")
            else:
                stack.pop()
    if stack:
        for pos in stack:
            errors.append(f"位置 {pos}: 左大括号 '{{' 没有对应的右大括号")
    return (len(errors) == 0), errors

def check_environment_matching(latex_str: str) -> (bool, list):
    errors = []
    env_stack = []
    pattern = re.compile(r'\\(begin|end)\s*{([^}]+)}')
    for m in pattern.finditer(latex_str):
        cmd = m.group(1)
        env = m.group(2).strip()
        pos = m.start()
        if cmd == "begin":
            env_stack.append((env, pos))
        else:  # cmd == "end"
            if not env_stack:
                errors.append(f"位置 {pos}: \\end{{{env}}} 没有对应的 \\begin")
            else:
                last_env, last_pos = env_stack.pop()
                if last_env != env:
                    errors.append(f"位置 {last_pos} 的 \\begin{{{last_env}}} 与位置 {pos} 的 \\end{{{env}}} 不匹配")
    if env_stack:
        for env, pos in env_stack:
            errors.append(f"位置 {pos}: \\begin{{{env}}} 没有对应的 \\end")
    return (len(errors) == 0), errors

def run_static_checks(latex_snippet: str) -> list:
    cleaned = remove_latex_comments(latex_snippet)
    errors = []
    ok_braces, brace_errors = check_balanced_braces(cleaned)
    ok_env, env_errors = check_environment_matching(cleaned)
    if not ok_braces:
        errors.extend(["大括号错误: " + err for err in brace_errors])
    if not ok_env:
        errors.extend(["环境匹配错误: " + err for err in env_errors])
    return errors

def check_with_pdflatex(latex_snippet: str) -> list:
    """
    call pdflatex for compilation checking and return the error messages detected in the compilation log.
    """
    template = r"""
\documentclass{article}
\usepackage{amsmath}
\begin{document}
%s
\end{document}
    """ % latex_snippet
    
    errors = []
    with tempfile.TemporaryDirectory() as tmpdirname:
        tex_file = os.path.join(tmpdirname, "temp.tex")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(template)
        try:
            proc = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=tmpdirname, timeout=15
            )
            output = proc.stdout.decode("utf-8") + proc.stderr.decode("utf-8")
            for line in output.splitlines():
                if line.startswith("!"):
                    errors.append(line.strip())
            if proc.returncode != 0 and not errors:
                errors.append("pdflatex 返回非 0 错误码，编译可能存在问题。")
        except Exception as e:
            errors.append(f"调用 pdflatex 编译时出错: {e}")
    return errors

def extract_latex_segments(markdown_text: str) -> list:
    """
    extract latex segments from markdown
    """
    segments = []
    block_pattern = re.compile(r'\$\$([\s\S]+?)\$\$', re.MULTILINE)
    segments.extend(block_pattern.findall(markdown_text))
    inline_pattern = re.compile(r'(?<!\$)\$([^$\n]+?)\$(?!\$)')
    segments.extend(inline_pattern.findall(markdown_text))
    return segments

def latex_errors(markdown_text: str) -> dict:
    segments = extract_latex_segments(markdown_text)
    report = {}
    for idx, seg in enumerate(segments):
        seg = seg.strip()
        static_errors = run_static_checks(seg)
        pdflatex_errors = check_with_pdflatex(seg)
        report[f"公式段 {idx+1}"] = {
            "原始内容": seg,
            "静态检测错误": static_errors,
            "pdflatex 检测错误": pdflatex_errors
        }
    return report

def modify_latex(markdown_text: str, error):
    global deepseek
    return generate([
        {"role": "system", "content": "你是LaTeX校验员。以下是一段Markdown文本，其中的LaTeX代码有错误，请基于报错修正。同时文本要遵循以下中文排版规范：使用全角中文标点；专有名词大小写正确；英文、数字使用半角字符。直接在输出中输出文本内容。"},
        {"role": "user", "content": f"<原文>\n{markdown_text}\n</原文>\n\n<报错>\n{error}\n</报错>"}
    ], deepseek, "deepseek-reasoner")

is_latin = lambda ch: '\u0000' <= ch <= '\u007F' or '\u00A0' <= ch <= '\u024F'
is_nonspace_latin = lambda ch: is_latin(ch) and not ch.isspace() and not ch in """*()[]{}"'/-@#"""
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

start = time.time()
print("     Generating topic:")
topic = beautify_string(extract_topic(topics_text))
print(f"     Determined topic: {topic}; time spent {time.time() - start:.1f} s")

start = time.time()
print("   Generating outline:")
outline_result = beautify_string(outline(topic))
print(f"   Determined outline: time spent {time.time() - start:.1f} s")

start = time.time()
print("   Generating article:")
article = write_from_outline(outline_result)
print(f"      Article written: time spent {time.time() - start:.1f} s")

if latex_errors(article):
    print("      latex_errors exist")
    start = time.time()
    article = modify_latex(article, latex_errors(article))
    print(f"      LaTeX errors fixed: time spent {time.time() - start:.1f} s")

start = time.time()
article = beautify_string(article)
print(f"      Article beautified: time spent {time.time() - start:.1f} s")


start = time.time()
print("   Generating summary:")
summary_result = beautify_string(summary(article))
print(f"      Decided Summary: {summary_result}; time spent {time.time() - start:.1f} s")

lines = iter(article.split("\n"))
markdown_file = ""
author = random.choice(["杨其臻", "杨子凡", "叶家炜", "黄京"])
print(f"        Rolled author: {author}")

for line in lines:
    if line.startswith("# "):
        title = line[1:].strip().split("：")[0]

        metadata = "\n".join([
            "---",
            f'title: "{title}"',
            f'author: "{author}"',
            f'date: "{datetime.datetime.now().strftime("%b %d, %Y")}"',
            f'description: "{summary_result}"',
            f'latex: true',
            f'pdf: true',
            "---",
        ]) + "\n"

        markdown_file += metadata
        break

for line in lines:
    if line.startswith("---") \
        or (line.startswith("#") and any([wd in line for wd in ["引言", "总结", "结语"]])): continue
    markdown_file += line + "\n"

with open(f"{path_to}/index.md", "w", encoding="utf-8") as f:
    f.write(markdown_file)

print(f"     Composed article: {path_to}/index.md")