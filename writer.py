from openai import OpenAI
from bs4 import BeautifulSoup
import requests
import random
import time
import datetime
import os
import glob
import yaml

path_to = f'src/content/blog/{datetime.datetime.now().strftime("%Y-%m-%d")}'

if os.path.exists(path_to):
    print("Article already generated today.")
    exit(0)
else:
    os.makedirs(path_to, exist_ok=True)
    print(f"Created directory {path_to}")

start = time.time()
print("Connecting to LLM API ...")
deepseek = OpenAI(base_url="https://api.deepseek.com", api_key=os.environ.get("DS_APIKEY"))
print(f"Initialized LLM API. ({time.time() - start:.1f}s)")

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
            print(f"Error reading {path}: {e}")
    
    return blog_posts

# Get existing blog posts
existing_posts = get_existing_blog_posts()
existing_posts_text = "\n".join([f"标题: {post['title']}\n描述: {post['description']}" for post in existing_posts])
print(f"Loaded {len(existing_posts)} existing blog posts.")

topics = [topic.get_text(strip=True) for topic in scrape_website("https://news.ycombinator.com/", ".titleline")]
topics_text = "\n".join(random.choices(topics, k=random.randint(5, len(topics))))
print(f"Scraped {len(topics)} topics from Hacker News.")

def extract_topic(topics):
    global deepseek, existing_posts_text
    return generate([
        {"role": "system", "content": "你在为一篇技术博客确定一个主题。直接用中文输出主题。"},
        {"role": "user", "content": f"阅读以下是HackerNews的热门文章，然后写一个可以用于技术博客的主题。这个主题应当是一个通用、普通的技术，不能是一个事件或其它东西。\n\n{topics}\n\n以下是已有的博客文章，请避免选择相似的主题：\n\n{existing_posts_text}\n\n只需要一个主题，直接输出。"},
    ], deepseek, "deepseek-chat")

def outline(topic):
    global deepseek
    return generate([
        {"role": "user", "content": f"我要写一篇关于「{topic}」的博客文章。帮我列一个详细的文章提纲。"}
    ], deepseek, "deepseek-reasoner")

def write_from_outline(outline):
    global deepseek, existing_posts_text
    return generate([
        {"role": "system", "content": "你是一位专业技术博客作者。在写作时请遵循以下中文排版规范：1) 中文与英文、数字之间需要有空格；2) 中文标点与英文、数字之间不加空格；3) 使用全角中文标点；4) 专有名词大小写正确；5) 英文、数字使用半角字符；6) 使用直角引号「」。"},
        {"role": "user", "content": f"{outline}\n\n根据这个提纲中关于技术知识的部分，写出一篇技术博客文章。文章中避免出现图片，避免使用列表。每一段出现的代码都进行较为详细的解读。在讲述内容时尽量使用段落的语言，语言风格可以略偏专业，但保持清晰。\n\n以下是已有的博客文章，请确保你的内容与它们不重复：\n\n{existing_posts_text}\n\n使用Markdown（要求符合Common Markdown规范）输出，使用LaTeX公式（注意：数学的开闭定界符前后不能有字母或数字字符。像x$a + b = c$或$a + b = c$1将无法渲染为数学公式（所有$会被渲染为$）；但x $\\infty$ 1和($\\infty$)会正常渲染），标题尽量只用一级标题 `#` 和二级标题 `##`，不要用分割线。直接输出正文。"}
    ], deepseek, "deepseek-reasoner")

def summary(article):
    global deepseek
    return generate([
        {"role": "system", "content": "你是一个技术博客简介写作者，简介不一定需要涵盖文章的全部内容，能起到一定的提示作用即可。直接输出简介。请遵循中文排版规范，确保中英文之间有空格，使用正确的标点符号。"},
        {"role": "user", "content": f"给这篇文章写一个15字的简短介绍：\n\n{article}"}
    ], deepseek, "deepseek-chat")

start = time.time()
print("Generating topic ...")
topic = extract_topic(topics_text)
print(f"Determined topic ({time.time() - start:.1f}s): {topic}")

start = time.time()
print("Generating outline ...")
outline_result = outline(topic)
print(f"Outline generated ({time.time() - start:.1f}s).")

start = time.time()
print("Generating article ...")
article = write_from_outline(outline_result)
print(f"Article generated ({time.time() - start:.1f}s).")

start = time.time()
print("Generating summary ...")
summary_result = summary(article)
print(f"Summary ({time.time() - start:.1f}s): {summary_result}")

lines = iter(article.split("\n"))
markdown_file = ""
author = random.choice(["杨其臻", "杨子凡", "叶家炜", "黄京"])

for line in lines:
    if line.startswith("# "):
        title = line[1:].strip()
        print(f"Detected title: {title}")

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
        print(f"Injecting metadata:\n{metadata.strip()}")

        markdown_file += metadata
        break

for line in lines:
    if line.startswith("---"): continue
    markdown_file += line + "\n"

with open(f"{path_to}/index.md", "w", encoding="utf-8") as f:
    f.write(markdown_file)

print(f"Markdown file generated at {path_to}/index.md")
