import os

def clean_text(lines):
	# `lines` is an iterator over the lines of a file (without "\n").
	out = ""
	for line in lines:
		if line.startswith("---") \
			or (line.startswith("#") and any([wd in line for wd in ["引言", "总结", "结语"]])): continue
		if line.startswith("#") and any([(n + "、") in line for n in "一二三四五六七八九十"]):
			mark, text = line.split(" ", 1)
			text = text.split("、", 1)[1]
			line_ = f"{mark} {text}"
		else:
			line_ = line
		out += line_ + "\n"
	return out

if __name__ == "__main__":
	src_dir = "./src/content/blog/"
	for date in os.listdir(src_dir):
		file = os.path.join(src_dir, date, "index.md")
		with open(file, "r", encoding="utf-8") as f:
			lines = iter(f.read().splitlines())
		three_dashes_count = 0
		metadata = ""
		for line in lines:
			if line.startswith("---"): three_dashes_count += 1
			metadata += line + "\n"
			if three_dashes_count == 2: break
		cleaned = clean_text(lines)
		with open(file, "w", encoding="utf-8") as f:
			f.write(metadata + cleaned)
