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
from typing import List, Tuple, Dict
import clean_text
from xai_sdk import Client
from xai_sdk.chat import system, user

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
xai_client = Client(api_key=os.getenv("XAI_API_KEY"), timeout=7200)
print(f"   Time spent on init: {time.time() - start:.1f} s")

def generate(context, provider, model): #for openrouter
    completion = provider.chat.completions.create(
        model=model,
        messages=context
    )
    return completion.choices[0].message.content.strip()

def grok_generate(context, provider, model): #for xai
    """
    e.g. 
    model="grok-3-mini"
    provider=xai_client
    context=[system("You are a highly intelligent AI assistant."),user("What is 101*3?")]
    """
    chat = provider.chat.create(
        model=model,
        messages=context,
    )
    response = chat.sample()
    return response.content.strip()

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
    # return generate([
    #     {"role": "system", "content": f"你在为一篇技术博客确定一个主题。直接用中文输出主题。"},
    #     {"role": "user", "content": f"阅读以下是HackerNews的热门文章，然后写一个可以用于技术博客的主题。这个主题应当是一个通用、普通的技术，不能是一个事件或其它东西。\n\n{topics}\n\n只需要一个主题，直接输出。"},
    # ], deepseek, "deepseek-chat")
    return grok_generate([
        system("你在为一篇技术博客确定一个主题。直接用中文输出主题。"),
        user(f"阅读以下是HackerNews的热门文章，然后写一个可以用于技术博客的主题。这个主题应当是一个通用、普通的技术，不能是一个事件或其它东西。\n\n{topics}\n\n只需要一个主题，直接输出。")
    ], xai_client, "grok-4-1-fast-non-reasoning")

def outline(topic):
    global deepseek
    # return generate([
    #     {"role": "user", "content": f"我要写一篇关于「{topic}」的博客文章。帮我列一个详细的文章提纲。"}
    # ], deepseek, "deepseek-reasoner")
    return grok_generate([
        user(f"我要写一篇关于「{topic}」的博客文章。帮我列一个详细的文章提纲。")
    ], xai_client, "grok-4-1-fast-non-reasoning")

def write_from_outline(outline):
    global deepseek, existing_posts_text
    # return generate([
    #     {"role": "system", "content": "你是一位专业技术博客作者。在写作时请遵循以下中文排版规范：使用全角中文标点；专有名词大小写正确；英文、数字使用半角字符；使用直角引号「」。"},
    #     {"role": "user", "content": f"{outline}\n\n根据这个提纲中关于技术知识的部分，写出一篇技术博客文章。文章中避免出现图片，不能使用任何列表。每一段出现的代码都进行较为详细的解读。在讲述内容时尽量使用段落的语言，语言风格可以略偏专业，但保持清晰。使用Markdown（要求符合Common Markdown规范）输出，使用LaTeX公式（注意：数学的开闭定界符前后不能有字母或数字字符。像x$a + b = c$或$a + b = c$1将无法渲染为数学公式（所有$会被渲染为$）；但x $\\infty$ 1和($\\infty$)会正常渲染），标题尽量只用一级标题 `#` 和二级标题 `##`，不要用分割线。请遵循中文排版规范，使用正确的标点符号。直接输出正文。"}
    # ], deepseek, "deepseek-reasoner")
    return grok_generate([
        system("你是一位专业技术博客作者。在写作时请遵循以下中文排版规范：使用全角中文标点；专有名词大小写正确；英文、数字使用半角字符；使用直角引号「」。"),
        user(f"{outline}\n\n根据这个提纲中关于技术知识的部分，写出一篇技术博客文章。文章中避免出现图片，不能使用任何列表。每一段出现的代码都进行较为详细的解读。在讲述内容时尽量使用段落的语言，语言风格可以略偏专业，但保持清晰。使用Markdown（要求符合Common Markdown规范）输出，使用LaTeX公式（注意：数学的开闭定界符前后不能有字母或数字字符。像x$a + b = c$或$a + b = c$1将无法渲染为数学公式（所有$会被渲染为$）；但x $\\infty$ 1和($\\infty$)会正常渲染），标题尽量只用一级标题 `#` 和二级标题 `##`，不要用分割线。请遵循中文排版规范，使用正确的标点符号。直接输出正文。")
    ], xai_client, "grok-4-1-fast-non-reasoning")

def summary(article):
    global deepseek
    # return generate([
    #     {"role": "system", "content": "你是一个技术博客简介写作者，简介不一定需要涵盖文章的全部内容，能起到一定的提示作用即可。直接输出简介。遵循以下中文排版规范：使用全角中文标点；专有名词大小写正确；英文、数字使用半角字符。注意简介被作为副标题使用，不是一句句子，不要以句号结尾。"},
    #     {"role": "user", "content": f"给这篇文章写一个15字的简短介绍：\n\n{article}"}
    # ], deepseek, "deepseek-chat")
    return grok_generate([
        system("你是一个技术博客简介写作者，简介不一定需要涵盖文章的全部内容，能起到一定的提示作用即可。直接输出简介。遵循以下中文排版规范：使用全角中文标点；专有名词大小写正确；英文、数字使用半角字符。注意简介被作为副标题使用，不是一句句子，不要以句号结尾。"),
        user(f"给这篇文章写一个15字的简短介绍：\n\n{article}")
    ], xai_client, "grok-4-1-fast-non-reasoning")

# LaTeX error handling 
def extract_latex_segments(markdown_text: str) -> List[Tuple[str, int, int]]:
    segments: List[Tuple[str,int,int]] = []
    block_pattern = re.compile(r'(\$\$[\s\S]+?\$\$)', re.DOTALL)
    for m in block_pattern.finditer(markdown_text):
        segments.append((m.group(1), m.start(), m.end()))

    inline_pattern = re.compile(r'(?<!\\)(\$(?:\\.|[^$])+?\$)', re.DOTALL)
    for m in inline_pattern.finditer(markdown_text):
        if any(start <= m.start() < end for _, start, end in segments):
            continue
        segments.append((m.group(1), m.start(), m.end()))

    return segments


def latex_checks(latex_str: str) -> List[str]:
    errors: List[str] = []
    
    def get_line_no(index: int) -> int:
        return latex_str.count('\n', 0, index) + 1

    clean_str = list(latex_str)
    for m in re.finditer(r'\\.', latex_str):
        clean_str[m.start():m.end()] = list("@@")

    verb_pattern = re.compile(r'(\\begin\{verbatim\}.*?\\end\{verbatim\})', re.DOTALL)
    temp_s = "".join(clean_str) 
    clean_str = list(latex_str)
    verb_block = re.compile(r'\\begin\{verbatim\}.*?\\end\{verbatim\}', re.DOTALL)
    for m in verb_block.finditer(latex_str):
        length = m.end() - m.start()
        newlines = latex_str[m.start():m.end()].count('\n')
        clean_str[m.start():m.end()] = list(' ' * (length - newlines) + '\n' * newlines)

    verb_inline = re.compile(r'\\verb(?P<sep>[^a-zA-Z]).*?(?P=sep)')
    temp_s = "".join(clean_str)
    for m in verb_inline.finditer(temp_s):
        length = m.end() - m.start()
        clean_str[m.start():m.end()] = list(' ' * length)

    temp_s = "".join(clean_str)
    for m in re.finditer(r'%.*', temp_s):
        length = m.end() - m.start()
        clean_str[m.start():m.end()] = list(' ' * length)

    cleaned_text = "".join(clean_str)

    masked_text = re.sub(r'\\[{}$%&_]', '__', cleaned_text)

    # 引用前空格
    for m in re.finditer(r'(?<!~)(\s+)\\ref\{', cleaned_text):
        if '\n' not in m.group(1): 
            line = get_line_no(m.start())
            errors.append(f"[Line {line}] '\\ref' 前检测到普通空格，建议使用 '~\\ref{{...}}'。")

    # 省略号
    for m in re.finditer(r'(?<!\.)(\.\.\.|…)(?!\.)', cleaned_text):
        line = get_line_no(m.start())
        errors.append(f"[Line {line}] 检测到省略号 '{m.group(1)}'，建议使用 '\\dots'。")

    # 缩写空格
    for m in re.finditer(r"\b(e\.g|i\.e|etc)\.(\s+)", cleaned_text):
        line = get_line_no(m.start())
        errors.append(f"[Line {line}] 缩写 '{m.group(1)}.' 后看似是普通空格，建议使用 '\\ ' 或 '~'。")

    # 数学模式 ($$)
    temp_math = masked_text
    doubles = list(re.finditer(r'\$\$', temp_math))
    if len(doubles) % 2 != 0:
        line = get_line_no(doubles[-1].start())
        errors.append(f"[Line {line}附近] 块级数学模式 '$$' 数量不匹配。")
    
    temp_math = re.sub(r'\$\$[\s\S]*?\$\$', '', temp_math)
    singles = list(re.finditer(r'(?<!\\)\$', temp_math))
    if len(singles) % 2 != 0:
        line = get_line_no(singles[-1].start())
        errors.append(f"[Line {line}附近] 行内数学模式 '$' 数量不匹配。")

    # 直引号
    if '"' in cleaned_text:
        for m in re.finditer(r'"', cleaned_text):
            line = get_line_no(m.start())
            errors.append(f"[Line {line}] 检测到直引号 '\"'，建议使用 ``...''。")

    # label/footnote 空格
    for m in re.finditer(r"(\s+)\\(label|footnote)\{", cleaned_text):
        if '\n' not in m.group(1):
            line = get_line_no(m.start())
            errors.append(f"[Line {line}] '\\{m.group(2)}' 前检测到空格。")

    # 乘号 x
    for m in re.finditer(r"(?<![a-zA-Z])\b(\d+)\s*x\s*(\d+)\b", cleaned_text):
        line = get_line_no(m.start())
        errors.append(f"[Line {line}] '{m.group(0)}' 中的 'x' 疑似乘号。")

    # 大括号匹配
    stack_braces = []
    for pos, ch in enumerate(masked_text):
        if ch == '{': stack_braces.append(pos)
        elif ch == '}':
            if not stack_braces:
                line = get_line_no(pos)
                errors.append(f"[Line {line}] 多余的 '}}'。")
            else:
                stack_braces.pop()
    if stack_braces:
        line = get_line_no(stack_braces[0])
        errors.append(f"[Line {line}] 未闭合的 '{{'。")

    # Begin/End
    env_stack = []
    for m in re.finditer(r"\\(begin|end)\s*\{([^}]+)\}", cleaned_text):
        cmd, env = m.group(1), m.group(2)
        line = get_line_no(m.start())
        if cmd == 'begin':
            env_stack.append((env, line))
        else:
            if not env_stack:
                errors.append(f"[Line {line}] 多余 '\\end{{{env}}}'。")
            elif env_stack[-1][0] != env:
                errors.append(f"[Line {line}] 环境不匹配：预期 '\\end{{{env_stack[-1][0]}}}'。")
            else:
                env_stack.pop()
    for env, line in env_stack:
        errors.append(f"[Line {line}] 环境 '\\begin{{{env}}}' 未闭合。")

    # 数学内中文标点
    for m in re.finditer(r'\$([^$]+)\$', masked_text):
        if re.search(r'[，。；：！？]', m.group(1)):
            line = get_line_no(m.start())
            errors.append(f"[Line {line}] 数学公式中检测到中文标点。")

    # 中文括号空格
    for m in re.finditer(r'([\u4e00-\u9fa5])\s+\(', cleaned_text):
        line = get_line_no(m.start())
        errors.append(f"[Line {line}] 中文 '{m.group(1)}' 与 '(' 间有多余空格。")

    return errors


def latex_errors(markdown_text: str) -> Dict[Tuple[str, int], List[str]]:
    report = {}
    for seg, start_idx, _ in extract_latex_segments(markdown_text):
        errs = latex_checks(seg)
        if errs:
            report[(seg, start_idx)] = errs
    return report

def modify_latex(markdown_text: str, error_report: Dict[Tuple[str,int], List[str]]) -> str:
    """
    遍历 error_report，按 start_idx 从大到小替换，
    保证后面的替换不影响前面的 start_idx。
    """
    corrected = markdown_text
    items = sorted(error_report.items(), key=lambda x: x[0][1], reverse=True)

    for (seg, start_idx), errs in items:
        end_idx = start_idx + len(seg)
        context = corrected[max(0, start_idx-50): end_idx+50]
        user_msg = (
            f"修正此 LaTeX 片段（包含 $ 定界符）：\n{seg}\n\n"
            "检测到错误：\n- " + "\n- ".join(errs) +
            "\n\n上下文：\n" + context +
            "\n\n请只返回修正后的完整片段，不要添加其它标记。"
        )
        # fixed = generate([
        #     {"role":"system","content":"你是 LaTeX 专家，负责修正以下代码："},
        #     {"role":"user","content":user_msg}
        # ], deepseek, "deepseek-reasoner").strip()
        fixed = grok_generate([
            system("你是 LaTeX 专家，负责修正以下代码："),
            user(user_msg)
        ], xai_client, "grok-4-fast-reasoning").strip()

        # 去掉```，如果不小心生成了
        if fixed.startswith("```") and fixed.endswith("```"):
            fixed = "\n".join(fixed.splitlines()[1:-1]).strip()

        # 给重新生成的丢失的加上 $/$$，如果ds忘记了
        if not fixed.startswith('$'):
            if seg.startswith('$$') and seg.endswith('$$'):
                fixed = '$$' + fixed + '$$'
            elif seg.startswith('$') and seg.endswith('$'):
                fixed = '$' + fixed + '$'

        # 最终替换
        corrected = corrected[:start_idx] + fixed + corrected[end_idx:]

    return corrected

is_latin = lambda ch: '\u0000' <= ch <= '\u007F' or '\u00A0' <= ch <= '\u024F'
is_nonspace_latin = lambda ch: is_latin(ch) and not ch.isspace() and not ch in """*()[]{}"'/-@#"""
is_nonpunct_cjk = lambda ch: not is_latin(ch) and ch not in "·！￥…（）—【】、；：‘’“”，。《》？「」"

# beautify的时候跳过 LaTeX
def beautify_string(text: str) -> str:
    segments = extract_latex_segments(text)
    segments.sort(key=lambda x: x[1])

    result_parts = []
    last_end = 0

    for seg_content, seg_start, seg_end in segments:
        non_latex_part = text[last_end:seg_start]
        processed_part = ""
        for i, char in enumerate(non_latex_part):
            if i > 0 and (
                (is_nonspace_latin(char) and is_nonpunct_cjk(non_latex_part[i-1])) or
                (is_nonspace_latin(non_latex_part[i-1]) and is_nonpunct_cjk(char))
            ):
                processed_part += " "
            processed_part += char
        result_parts.append(processed_part)

        result_parts.append(seg_content)
        last_end = seg_end

    final_part = text[last_end:]
    processed_final_part = ""
    for i, char in enumerate(final_part):
         if i > 0 and (
             (is_nonspace_latin(char) and is_nonpunct_cjk(final_part[i-1])) or
             (is_nonspace_latin(final_part[i-1]) and is_nonpunct_cjk(char))
         ):
            processed_final_part += " "
         processed_final_part += char
    result_parts.append(processed_final_part)

    return "".join(result_parts)

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

start = time.time()
while latex_errors(article):
    print("latex_errors still exist")
    article = modify_latex(article, latex_errors(article))

print(f"      LaTeX errors fixed: time spent {time.time() - start:.1f} s")

start = time.time()
article = beautify_string(article)
print(f"      Article beautified: time spent {time.time() - start:.1f} s")


start = time.time()
print("   Generating summary:")
summary_result = beautify_string(summary(article))
print(f"      Decided Summary: {summary_result}; time spent {time.time() - start:.1f} s")

lines = iter(article.splitlines())
markdown_file = ""
author = random.choice(["杨其臻", "杨子凡", "叶家炜", "黄京", "王思成", "黄梓淳", "马浩琨", "杨岢瑞", "李睿远"])
print(f"        Rolled author: {author}")

for line in lines:
    if line.startswith("# "):
        # Sometimes the LLM does not produce a top-level title
        # So we simply use the aforementioned topic instead
        # title = line[1:].strip().split("：")[0]

        metadata = "\n".join([
            "---",
            f'title: "{topic}"',
            f'author: "{author}"',
            f'date: "{datetime.datetime.now().strftime("%b %d, %Y")}"',
            f'description: "{summary_result}"',
            'latex: true',
            'pdf: true',
            "---",
        ]) + "\n"

        markdown_file += metadata
        break

markdown_file += clean_text.clean_text(lines)

with open(f"{path_to}/index.md", "w", encoding="utf-8") as f:
    f.write(markdown_file)

print(f"     Composed article: {path_to}/index.md")
