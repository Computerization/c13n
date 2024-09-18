## About the `md2tex` utility

### Features

This is a Markdown to (La)TeX parser implemented in C, based on MD4C, with the following features:

* **Compliance**: It is compliant to the latest version of [CommonMark specification](http://spec.commonmark.org/) thanks to MD4C. Currently, we supports CommonMark 0.31.

* **Extensions**: It supports some widely used extensions, namely: table, strikethrough, underline, and TeX style equations.

* **Lenience**: It follows completely the GIGO philosophy (garbage in, garbage out). It sees any sequence of bytes as valid input. It will not throw any error when parsing.

* **Performance**: It is very fast, parsing most of our posts in less than 1 ms.

* **Portability**: It is tested to run on Mach-O, iOS, and Linux. It should run on Windows, BSDs, and all other POSIX-compliant OSes which has a working C compiler.

* **Encoding**: It understands UTF-8 to determine word boundaries, and case-insensitive matching of a link reference label (Unicode case folding). However, it will *not* translate HTML entities and numeric character references.

### Build Instructions

#### POSIX-compliant OSes

Make sure you have a working C compiler (Clang/GCC/...) and standard library (GLibC/musl/...), together with GNU Make and sed tools.

Then simply run make to generate the executable `md2tex`.

#### Windows

You can install Cygwin and follow the same step, or you can use the fragile way.

```sh
cc -o md2tex md2tex.c md4c.c -O2 -Wall
```

### MarkDown Spec

Generally, you should conform to the CommonMark spec when writing posts. However, because of the additional extensions, there are some extra rules.

#### Table

It supports [GitHub-style tables](https://github.com/github/docs/blob/main/content/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-tables.md).

Note that in the generated (La)TeX manuscript, the align information of the columns are currently ignored, and default to left align. It may be supported in the future.

#### Strikethrough

It supports `~delete~` (~~delete~~).

#### Underline

Underscore denotes an underline instead of an ordinary emphasis or strong emphasis. Thus, to get *italics* and **bold**, use `*` instead.

#### TeX-style Equation

TeX like inline math spans (`$...$`) and display math spans (`$$...$$`) ate supported. You are not required to escape ordinary dollars signs in most cases.

```Markdown
This is an inline math span: $a + b = c$.

This is a display math span:
$$
  a + b = c.
$$

This is a dollar sign: $, 12$; equivalent to \$, 12\$.

This is a double dollar sign: $$; equivalent to \$\$.

Common knowledge: math spans cannot be nested.
$$foo $bar$ baz$$ is equivalent to \$\$foo $bar$ baz\$\$ which only bar is rendered as equation.

Note: the opening delimiter or closing delimiter cannot be preceded or followed by an alphanumeric character.
x$a + b = c$ or $a + b = c$y will not be rendered as math (all $ rendered as \$)
```

#### Appendix

This resulted TeX manuscript for reference:

<details>

```TeX
\chapter{About the \verb!md2tex! utility}
\section{Features}
This is a Markdown to (La)TeX parser implemented in C, based on MD4C, with the following features:\par
\begin{enumerate}
\item \textbf{Compliance}: It is compliant to the latest version of \href{http://spec.commonmark.org/}{CommonMark specification} thanks to MD4C. Currently, we supports CommonMark 0.31.
\item \textbf{Extensions}: It supports some widely used extensions, namely: table, strikethrough, underline, and TeX style equations.
\item \textbf{Lenience}: It follows completely the GIGO philosophy (garbage in, garbage out). It sees any sequence of bytes as valid input. It will not throw any error when parsing.
\item \textbf{Performance}: It is very fast, parsing most of our posts in less than 1 ms.
\item \textbf{Portability}: It is tested to run on Mach-O, iOS, and Linux. It should run on Windows, BSDs, and all other POSIX-compliant OSes which has a working C compiler.
\item \textbf{Encoding}: It understands UTF-8 to determine word boundaries, and case-insensitive matching of a link reference label (Unicode case folding). However, it will \textit{not} translate HTML entities and numeric character references.
\end{enumerate}
\section{Build Instructions}
\subsection{POSIX-compliant OSes}
Make sure you have a working C compiler (Clang/GCC/...) and standard library (GLibC/musl/...), together with GNU Make and sed tools.\par
Then simply run make to generate the executable \verb!md2tex!.\par
\subsection{Windows}
You can install Cygwin and follow the same step, or you can use the fragile way.\par
\begin{verbatim}[language=sh]
cc -o md2tex md2tex.c md4c.c -O2 -Wall
\end{verbatim}
\section{MarkDown Spec}
Generally, you should conform to the CommonMark spec when writing posts. However, because of the additional extensions, there are some extra rules.\par
\subsection{Table}
It supports \href{https://github.com/github/docs/blob/main/content/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-tables.md}{GitHub-style tables}.\par
Note that in the generated (La)TeX manuscript, the align information of the columns are currently ignored, and default to left align. It may be supported in the future.\par
\subsection{Strikethrough}
It supports \verb!~delete~! (\del{delete}).\par
\subsection{Underline}
Underscore denotes an underline instead of an ordinary emphasis or strong emphasis. Thus, to get \textit{italics} and \textbf{bold}, use \verb!*! instead.\par
\subsection{TeX-style Equation}
TeX like inline math spans (\verb!$...$!) and display math spans (\verb!$$...$$!) ate supported. You are not required to escape ordinary dollars signs in most cases.\par
\begin{verbatim}[language=Markdown]
This is an inline math span: $a + b = c$.

This is a display math span:
$$
  a + b = c.
$$

This is a dollar sign: $, 12$; equivalent to \$, 12\$.

This is a double dollar sign: $$; equivalent to \$\$.

Common knowledge: math spans cannot be nested.
$$foo $bar$ baz$$ is equivalent to \$\$foo $bar$ baz\$\$ which only bar is rendered as equation.

Note: the opening delimiter or closing delimiter cannot be preceded or followed by an alphanumeric character.
x$a + b = c$ or $a + b = c$y will not be rendered as math (all $ rendered as \$)
\end{verbatim}
```

</details>
