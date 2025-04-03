import os
import sys
import shutil
import hashlib

src_dir = "./src/content/blog/"
pbl_dir = "./public/blog/"
bch_dir = "./public/batch/"
utl_dir = "./typeset/"
fnt_dir = "./typeset/font/"
sty_dir = "./typeset/macro"
tmp_dir = "./.tmp/"

bch_size = 5

class File():
	def __init__(self, path: str):
		self.path = path
		self.dir = os.path.dirname(self.path)
		self.filename = os.path.basename(self.path)
		os.makedirs(self.dir, exist_ok=True)
	def read(self):
		with open(self.path, "r", encoding="utf-8") as f:
			content = f.read()
		return content
	def readlines(self):
		with open(self.path, "r", encoding="utf-8") as f:
			lines = f.readlines()
		return lines
	def write(self, content: str):
		with open(self.path, "w+", encoding="utf-8") as f:
			f.write(content)
	def writelines(self, lines: list):
		with open(self.path, "w+", encoding="utf-8") as f:
			f.writelines(lines)

def hash_str(s):
	return hashlib.sha256(s.encode()).hexdigest()

def metaext(src):
	print("  Extracting metadata:")
	lines = File(src).readlines()
	global meta
	meta = {}
	inmd = False
	fpos = -1
	for line in lines:
		fpos += 1
		if line.strip() == "---":
			lines[fpos] = ""
			if inmd: break
			else: inmd = True
		else:
			if ":" not in line: continue
			key, val = line.split(":", 1)
			lines[fpos] = ""
			meta[key.strip()] = val.strip()
	if len(meta):
		print("title: %s; author: %s; date: %s" % (meta.get("title"), meta.get("author"), meta.get("date")))
		File(src).writelines(lines)
	else:
		print("                Error: no metadata found")

def metainj(dst):
	print("   Injecting metadata:")
	manu = File(dst).readlines()
	manu.insert(0, "\\title{%s}\n\\author{%s}\n\\date{%s}\n\\maketitle\n" % (meta.get("title"), meta.get("author"), meta.get("date")))
	File(dst).writelines(manu)

def texcomp(drv):
	print("       Generating PDF:")
	shutil.copy(utl_dir + drv, tmp_dir + "index.ltx")
	for fonts in os.listdir(fnt_dir):
		shutil.copy(fnt_dir + fonts, tmp_dir + fonts)
	for macro in os.listdir(sty_dir):
		shutil.copy(sty_dir + macro, tmp_dir + macro)
	pwd = os.getcwd()
	os.chdir(tmp_dir)
	os.system("lualatex index.ltx --interaction=batchmode")
	os.chdir(pwd)

def pdfgenr(post):
	shutil.copytree(src_dir + post, tmp_dir, dirs_exist_ok=True)
	metaext(tmp_dir + "index.md")
	print("           Converting:")
	os.system(f"{utl_dir}md2tex {tmp_dir}index.md {tmp_dir}index.tex")
	metainj(tmp_dir + "index.tex")
	texcomp("drvpst.ltx")
	shutil.copy(tmp_dir + "index.tex", pbl_dir + post + "/index.tex")
	shutil.copy(tmp_dir + "index.pdf", pbl_dir + post + "/index.pdf")
	shutil.rmtree(tmp_dir)

def post():
	# Compiles each post, specifically converts the .md file to a .tex file
	# and compiles the .tex, finally moving .tex and .pdf to the public dir
	cwd = os.getcwd()
	print(f"     Making directory: {cwd}")
	os.chdir(utl_dir)
	os.system("make")
	os.chdir(cwd)
	# For each of the posts in the source directory
	for post in sorted(os.listdir(src_dir)):
		# Get hash of the markdown file content
		hsh = hash_str(File(src_dir + post + "/index.md").read())
		# If it is already compiled and the hash matches
		if all([
			os.path.exists(pbl_dir + post + p) for p in ["/index.tex", "/index.pdf", "/sha256"]
		]) and File(pbl_dir + post + "/sha256").read() == hsh:
			print(f"        Skipping post: {post} #{hsh}")
			continue
		print(f"      Processing post: {post}")
		# Write markdown hash to file `sha256`
		File(pbl_dir + post + "/sha256").write(hsh)
		# Compile PDF
		pdfgenr(post)
	# Cleaning
	os.chdir(utl_dir)
	print("          Cleaning up:")
	os.system("make clean")

def batch():
	# This function compiles several files sequentially into one batch version
	# The number of files in each batch are defined in `bch_size`, remaining
	# files not reaching that number will not be included as a new batch.
	cwd = os.getcwd()
	print(f"     Making directory: {cwd}")
	# Reading all posts (date strings)
	posts = sorted(os.listdir(src_dir))
	# Extracting batch ID and hash from preexisting batch directory
	compiled = [i.split(".")[0].split("_") for i in sorted(os.listdir(bch_dir))]
	compiled_hsh = {
		int(i[1]): i[2] for i in compiled
	}
	# Generating each batch
	for bch_id, bch_start in enumerate(range(0, len(posts), bch_size)):
		# For remaining files at the end not reaching the size of a batch
		if bch_start + bch_size > len(posts): break
		# Current range of indices and hash of date strings
		bch_range = list(range(bch_start, bch_start + bch_size))
		hsh = hash_str(" ".join([posts[i] for i in bch_range]))[-6:]
		existing_hsh = compiled_hsh.get(bch_id)
		# If this batch is already present
		if existing_hsh:
			if existing_hsh == hsh:
				print(f"       Skipping batch: {bch_id} #{hsh}")
				continue
			else:
				print(f"    Removing obsolete: {bch_id} #{existing_hsh} -> #{hsh}")
				os.remove(f"{bch_dir}compilation_{bch_id}_{existing_hsh}.pdf")
		print(f"     Processing batch: {bch_id} #{hsh}")
		filename = f"compilation_{bch_id}_{hsh}"
		# Writing index.tex to be compiled
		File(f"{tmp_dir}index.tex").writelines([
			# Title
			"\\mlytitle{" + f"c13n \\#{bch_id}" + "}",
			*[
				# Dump file contents from each post directory
				File(f"{pbl_dir}{posts[i]}/index.tex").read()
				for i in bch_range
			]
		])
		# Compiling and cleaning
		texcomp("drvmly.ltx")
		shutil.copy(tmp_dir + "index.pdf", bch_dir + filename.lower() + ".pdf")
		shutil.rmtree(tmp_dir)

if len(sys.argv) != 2:
	print("make: Incorrect options...")
elif sys.argv[1] == "post":
	post()
elif sys.argv[1] == "batch":
	batch()
else:
	print("make: Doing nothing...")
