from state.db.bootstrap import init_db


def main():
    init_db()
    print("PFIOS Step 2 database initialized.")


if __name__ == "__main__":
    main()
