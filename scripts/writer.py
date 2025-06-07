from openai import OpenAI
from bs4 import BeautifulSoup
import requests
import random
import time
import datetime
import os
import glob
import yaml
import clean_text

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
article = beautify_string(write_from_outline(outline_result))
print(f"      Article written: time spent {time.time() - start:.1f} s")

start = time.time()
print("   Generating summary:")
summary_result = beautify_string(summary(article))
print(f"      Decided Summary: {summary_result}; time spent {time.time() - start:.1f} s")

lines = iter(article.splitlines())
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
