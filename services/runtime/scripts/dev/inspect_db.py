from sqlalchemy import inspect
from pfios.core.db.session import engine


def main():
    inspector = inspect(engine)
    print("Tables:")
    for table_name in inspector.get_table_names():
        print(f" - {table_name}")


if __name__ == "__main__":
    main()
