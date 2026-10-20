from sc2analyzer.embedded_pg import ensure_database

ensure_database()

from sc2analyzer.api import main

if __name__ == "__main__":
    main()
