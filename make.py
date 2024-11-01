import os
import sys
import shutil
import hashlib

src_dir = "./src/content/blog/"
pbl_dir = "./public/blog/"
bch_dir = "./src/content/batch/"
utl_dir = "./typeset/"
fnt_dir = "./typeset/font/"
tmp_dir = "./.tmp/"

bch_size = 5

def hash_str(s):
    return hashlib.sha256(s.encode()).hexdigest()

def metaext(src):
    print("  Extracting metadata:")
    with open(src, "r+", encoding="utf-8") as fsrc:
        lines = fsrc.readlines()
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
            fsrc.seek(0)
            fsrc.truncate()
            fsrc.writelines(lines)
        else:
            print("                Error: no metadata found")

def metainj(dst):
    with open(dst, "r+", encoding="utf-8") as fdst:
        print("   Injecting metadata:")
        manu = fdst.readlines()
        manu.insert(0, "\\title{%s}\n\\author{%s}\n\\date{%s}\n\\maketitle\n" % (meta.get("title"), meta.get("author"), meta.get("date")))
        fdst.seek(0)
        fdst.truncate()
        fdst.writelines(manu)

def texcomp(drv):
    print("       Generating PDF:")
    shutil.copy(utl_dir + drv, tmp_dir + "index.ltx")
    for fonts in os.listdir(fnt_dir):
        shutil.copy(fnt_dir + fonts, tmp_dir + fonts)
    pwd = os.getcwd()
    os.chdir(tmp_dir)
    os.system("lualatex index.ltx --interaction=batchmode")
    os.chdir(pwd)

def pdfgenr(dir):
    shutil.copytree(dir, tmp_dir)
    metaext(tmp_dir + "index.md")
    print("           Converting:")
    os.system(f"{utl_dir}md2tex {tmp_dir}index.md {tmp_dir}index.tex")
    metainj(tmp_dir + "index.tex")
    texcomp("drvpst.ltx")
    shutil.copy(tmp_dir + "index.tex", dir + "/index.tex")
    shutil.copy(tmp_dir + "index.pdf", dir + "/index.pdf")
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
        with open(src_dir + post + "/index.md", "r", encoding="utf-8") as f:
            hsh = hash_str(f.read())
        # If it is already compiled and the hash matches
        if all([ os.path.exists(pbl_dir + post + p) for p in ["/index.tex", "/index.pdf", "/sha256"] ]):
            with open(pbl_dir + post + "/sha256", "r", encoding="utf-8") as f:
                if f.read() == hsh:
                    print(f"      Skipping post: {post}, with hash {hsh}, already compiled")
                    continue
        print(f"      Processing post: {post}")
        # Write markdown hash to file `sha256`
        with open(pbl_dir + post + "/sha256", "w+", encoding="utf-8") as sha:
            sha.write(hash_str(hsh))
        # Compile PDF
        pdfgenr(pbl_dir + post)
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
        int(i[1]): int(i[2]) for i in compiled
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
                print(f"   Skipping existing batch #{bch_id} with same hash {hsh}")
                continue
            else:
                print(f"   Removing older version of existing batch #{bch_id} with hash {existing_hsh} (new hash {hsh})")
                os.remove(f"{bch_dir}compilation_{bch_id}_{existing_hsh}.pdf")
        print(f"   Processing batch #{bch_id} with hash {hsh}")
        filename = f"compilation_{bch_id}_{hsh}"
        os.mkdir(tmp_dir)
        # Writing index.tex to be compiled
        with open(f"{tmp_dir}index.tex", "w+", encoding="utf-8") as f:
            f.write("\\mlytitle{" + f"c13n \\#{bch_id}" + "}\n")
            for i in bch_range:
                # Dump file contents from each post directory
                with open(f"{src_dir}{posts[i]}/index.tex", "r", encoding="utf-8") as item:
                    f.write(item.read())
                f.write("\n")
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
