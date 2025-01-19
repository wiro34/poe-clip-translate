import json
import os

from pathlib import Path

OUTPUT_DIR = (Path(__file__) / ".." / ".." / "data").resolve()

LANGUAGES = ["English", "Japanese"]


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    with open("./EXPORT/config.json", "r") as f:
        tables = json.loads(f.read())["tables"]

    for table in tables:
        name = table["name"]
        columns = table["columns"]

        data = {}
        for lang in LANGUAGES:
            with open(
                f"./EXPORT/tables/{lang}/{name}.json", "r", encoding="utf-8"
            ) as f:
                data[lang] = json.loads(f.read())

        if "Id" in data[LANGUAGES[0]][0]:
            key_field = "Id"
        else:
            key_field = "Text"

        dict = []
        for item in data[LANGUAGES[0]]:
            dict_item = {}
            dict_item[LANGUAGES[0]] = extract(item, columns)
            for lang in LANGUAGES[1:]:
                found = find(data[lang], key_field, item[key_field])
                if found:
                    dict_item[lang] = extract(found, columns)
                else:
                    print("ERROR")
            dict.append(dict_item)

        with open(OUTPUT_DIR / f"{name}.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(dict, indent=2, ensure_ascii=False))


def find(list, key, value):
    for item in list:
        if item[key] == value:
            return item
    return None


def extract(dict, columns):
    return {k: dict[k] for k in columns}


if __name__ == "__main__":
    main()
