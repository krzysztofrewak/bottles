import json


def main():
    with open("annotations/annotations.json") as file:
        annotations = json.load(file)

    counts = {}
    for item in annotations["images"]:
        p = item["parameters"]
        key = (p["type"], p["color"], p["fill"], p["liquid"], p["label"], p["cap"])
        counts[key] = counts.get(key, 0) + 1

    out = [
        {"type": k[0], "color": k[1], "fill": k[2], "liquid": k[3], "label": k[4], "cap": k[5], "count": v}
        for k, v in sorted(counts.items())
    ]

    with open("docs/data.json", "w") as file:
        json.dump(out, file, indent=2)


if __name__ == "__main__":
    main()
