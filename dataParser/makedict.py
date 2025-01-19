import json
import os
import re

from pathlib import Path

OUTPUT_DIR = (Path(__file__) / ".." / ".." / "data").resolve()

LANGUAGES = ["English", "Japanese"]

STAT_DESCRIPTIONS_FILE = (
    "./EXPORT/files/Metadata@StatDescriptions@stat_descriptions.csd"
)

DQ_EXTRACT_PATTERN = r"\"([^\"]+)\""


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    make_dictionary_by_tables()
    make_stats_file()


def make_dictionary_by_tables():
    with open("./EXPORT/config.json", "r") as f:
        tables = json.loads(f.read())["tables"]

    dictionary = []
    words = []
    for table in tables:
        data = {}
        for lang in LANGUAGES:
            with open(
                f"./EXPORT/tables/{lang}/{table['name']}.json", "r", encoding="utf-8"
            ) as f:
                data[lang] = json.loads(f.read())

        for i in range(len(data[LANGUAGES[0]])):
            # discard unnessecery word
            if (
                data[LANGUAGES[0]][i][table["columns"][1]] == "{0}"
                or data[LANGUAGES[0]][i][table["columns"][1]] == ""
                or (
                    table["columns"][0] == "Id"
                    and "FilterRule" in data[LANGUAGES[0]][i][table["columns"][0]]
                )
            ):
                continue

            dict_item = {}
            for lang in LANGUAGES:
                dict_item[lang] = expand_square_brackets(
                    data[lang][i][table["columns"][1]]
                )
            if table["name"] == "Words":
                words.append(dict_item)
            else:
                dictionary.append(dict_item)

    with open(OUTPUT_DIR / f"dictionary.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(dictionary, indent=2, ensure_ascii=False))
    with open(OUTPUT_DIR / f"words.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(words, indent=2, ensure_ascii=False))


def find(list, key, value):
    for item in list:
        if item[key] == value:
            return item
    return None


def expand_square_brackets(text):
    matches = re.findall(r"\[([^\]]+)\]", text)
    if not matches:
        return text

    for md in matches:
        if "|" in md:
            text = text.replace(f"[{md}]", md.split("|", 2)[1])
        else:
            text = text.replace(f"[{md}]", md)

    return text


def make_stats_file():
    # EXPORT/tables/Stats.json is missing some text for mods, so parse .csd file
    # TODO: exclude "{0}"
    with open(STAT_DESCRIPTIONS_FILE, "r", encoding="utf-16-le") as f:
        stats = []
        buffer = None
        for line in f:
            bline = line.encode()
            if bline.startswith(b"\xef\xbb\xbf"):
                line = bline[3:].decode()
            if line.startswith("description"):
                if buffer:
                    stats.extend(parse(buffer))
                buffer = []
            if line.startswith("\t") and buffer is not None:
                buffer.append(line)

    with open(OUTPUT_DIR / f"stats.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(stats, indent=2, ensure_ascii=False))


def parse(buffer):
    len = int(buffer[1])
    en = []
    for i in range(len):
        en.append(expand_square_brackets(extract_description(buffer[2 + i])))

    ja_pos = find(buffer, 'lang "Japanese"')
    if ja_pos is None:
        return []

    ja = []
    for i in range(len):
        ja.append(expand_square_brackets(extract_description(buffer[ja_pos + 2 + i])))

    return [{"English": en, "Japanese": ja} for en, ja in zip(en, ja)]


def find(list, contains):
    for i in range(len(list)):
        if contains in list[i]:
            return i
    return None


def extract_description(line):
    md = re.search(DQ_EXTRACT_PATTERN, line)
    if not md:
        raise RuntimeError("Not found")
    return md[1]


if __name__ == "__main__":
    main()
