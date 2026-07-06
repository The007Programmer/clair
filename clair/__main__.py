"""clair entrypoint: `python3 -m clair`. Dispatches to cli.main()."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
