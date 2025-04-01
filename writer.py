from openai import OpenAI
from bs4 import BeautifulSoup
import requests
import random
import time
import datetime
import os

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

topics = [topic.get_text(strip=True) for topic in scrape_website("https://news.ycombinator.com/", ".titleline")]
topics_text = "\n".join(random.choices(topics, k=random.randint(5, len(topics))))
print(f"Scraped {len(topics)} topics from Hacker News.")

def extract_topic(topics):
	global deepseek
	return generate([
		{"role": "system", "content": "你在为一篇技术博客确定一个主题。直接用中文输出主题。"},
		{"role": "user", "content": f"阅读以下是 HackerNews 的热门文章，然后写一个可以用于技术博客的主题。这个主题应当是一个通用、普通的技术，不能是一个事件或其它东西。\n\n{topics}\n\n只需要一个主题，直接输出。"},
	], deepseek, "deepseek-chat")

def outline(topic):
	global deepseek
	return generate([
		{"role": "user", "content": f"我要写一篇关于「{topic}」的博客文章。帮我列一个详细的文章提纲。"}
	], deepseek, "deepseek-reasoner")

def write_from_outline(outline):
	global deepseek
	return generate([
		{"role": "user", "content": f"{outline}\n\n根据这个提纲中关于技术知识的部分，写出一篇技术博客文章。文章中避免出现图片，避免使用列表。每一段出现的代码都进行较为详细的解读。在讲述内容时尽量使用段落的语言，语言风格可以略偏专业，但保持清晰。使用markdown输出，使用latex公式，标题尽量只用一级标题 `#` 和二级标题 `##`，不要用分割线。直接输出正文。"}
	], deepseek, "deepseek-reasoner")

def summary(article):
	global deepseek
	return generate([
		{"role": "system", "content": "你是一个技术博客简介写作者，简介不一定需要涵盖文章的全部内容，能起到一定的提示作用即可。直接输出简介。"},
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
