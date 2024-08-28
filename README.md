# c13n
The newsletter of Computerization.

## Commands

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

## License

MIT for source code, CC BY 4.0 for texts.