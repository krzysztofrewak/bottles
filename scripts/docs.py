import json


def main():
    with open("annotations/annotations.json") as file:
        annotations = json.load(file)

    out = []
    for item in annotations["images"]:
        parameters = item["parameters"]
        out.append({
            "filename": item["filename"],
            "type": parameters["type"],
            "color": parameters["color"],
            "fill": parameters["fill"],
            "liquid": parameters["liquid"],
            "label": parameters["label"],
            "cap": parameters["cap"]
        })

    with open("docs/data.json", "w") as file:
        json.dump(out, file, indent=2)


if __name__ == "__main__":
    main()
