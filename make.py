import os
import shutil

src_dir = "./src/content/blog/"
utl_dir = "./typeset/"
tmp_dir = "./.tmp/"

def metaext(src):
    print("  Extracting metadata:")
    with open(src, "r+") as fsrc:
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
            print(f"title: {meta.get("title")}; author: {meta.get("author")}; date: {meta.get("date")}")
            fsrc.seek(0)
            fsrc.truncate()
            fsrc.writelines(lines)
        else:
            print("                Error: no metadata found")

def metainj(dst):
    with open(dst, "r+") as fdst:
        print("   Injecting metadata:")
        manu = fdst.readlines()
        manu.insert(0, f"\\title{{{meta.get("title")}}}\n\\author{{{meta.get("author")}}}\n\\date{{{meta.get("date")}}}\n\\maketitle\n")
        fdst.seek(0)
        fdst.truncate()
        fdst.writelines(manu)

def texcomp(dir):
    print("       Generating PDF:")
    shutil.copy(utl_dir + "drv.ltx", tmp_dir + "index.ltx")
    pwd = os.getcwd()
    os.chdir(tmp_dir)
    os.system("lualatex index.ltx --interaction=batchmode")
    os.chdir(pwd)
    shutil.copy(tmp_dir + "index.tex", dir + "/index.tex")
    shutil.copy(tmp_dir + "index.pdf", dir + "/index.pdf")

def pdfgenr(dir):
    shutil.copytree(dir, tmp_dir)
    metaext(tmp_dir + "index.md")
    print("           Converting:")
    os.system(f"{utl_dir}md2tex {tmp_dir}index.md {tmp_dir}index.tex")
    metainj(tmp_dir + "index.tex")
    texcomp(dir)
    shutil.rmtree(tmp_dir)

# save pwd
cwd = os.getcwd()
print(f"     Making directory: {cwd}")

# make the executable
os.chdir(utl_dir)
os.system("make")

# restore current directory
os.chdir(cwd)

for posts in sorted(os.listdir(src_dir)):
    if not os.path.exists(src_dir + posts + "/index.tex") and not os.path.exists(src_dir + posts + "/index.pdf"):
        print(f"      Processing post: {posts}")
        pdfgenr(src_dir + posts)

# cleanup
os.chdir(utl_dir)
print("          Cleaning up:")
os.system("make clean")
