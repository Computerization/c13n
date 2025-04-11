# c13n

Welcome to `c13n`, the newsletter of [Computerization](https://computerization.io).

We create and share tutorials and insights on computer science and technology. We are a passionate high school student club dedicated to advancing informatization systems at the Shanghai World Foreign Language Academy.

## Architecture

The architecture of this project consists of two parts:
- **Web:** The website of [c13n.club](https://c13n.club) is built with Astro, with the site generated from static markdown files under `/src`.
- **TeX:** The TeX version (namely PDF compilations) are generated from the Markdown files mainly using utilities under `/typeset`. The compilation can be automated using `make.py` and is now ready on GitHub actions.

## Web

We use `pnpm` as `c13n`'s package manager. Please avoid the usage of `npm` command.

| Command                    | Action                                           |
|:---------------------------| :----------------------------------------------- |
| `pnpm install`             | Installs dependencies                            |
| `pnpm run dev`             | Starts local dev server at `localhost:4321`      |
| `pnpm run dev:network`     | Starts local dev server on local network         |
| `pnpm run sync`            | Generates TypeScript types for all Astro modules.|
| `pnpm run build`           | Build your production site to `./dist/`          |
| `pnpm run preview`         | Preview your build locally, before deploying     |
| `pnpm run preview:network` | Preview build on local network                   |
| `pnpm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `pnpm run astro -- --help` | Get help using the Astro CLI                     |
| `pnpm run lint`            | Run ESLint                                       |
| `pnpm run lint:fix`        | Auto-fix ESLint issues                           |

## TeX

The Python script `make.py` reads Markdown files under `/src` and compiles them to TeX, and then PDF, placed under `/public`. During the process a `/.tmp` directory will be created and utilities under `/typeset` will be called.

Currently, two make modes are implemented:

- `make.py post`: this compiles each post individually and generates TeX and PDF versions for viewers to download.
- `make.py batch`: separate posts are compiled to batches of 5 that will serve as the final product of our newsletters.

The two commands will be automatically executed on commit by the GitHub Action bot. For more details of the limited support on Markdown syntax and file formats, see [this documentation](./typeset/README.md).

## License

MIT for source code, CC BY 4.0 for texts.
