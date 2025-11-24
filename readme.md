## A Multi-Attribute Dataset of Commercial Bottles for Computer Vision Research
This repository contains a curated dataset of high-resolution images of commercial beverage bottles. Each image represents a controlled configuration of bottle attributes, including bottle type, glass color, fill level, liquid color, label presence, and cap state. Filenames follow a deterministic naming convention encoding these attributes, and the repository includes scripts for analyzing and validating the dataset.

The dataset is published as a versioned archive on Zenodo and assigned a DOI to ensure long-term accessibility, citability, and reproducibility. This GitHub repository complements the Zenodo record by providing code, documentation, and tools for working with the dataset.

### Zenodo DOI
Dataset Digital Object Identifier (DOI) is (...).

A stable DOI ensures that the dataset can be referenced in scientific publications. Each GitHub release can be linked to a Zenodo version, enabling precise citation of the dataset used in experiments.

### Authors
* [<img src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" width="16" /> Mateusz Jackowski](https://orcid.org/0000-0001-9109-3350)
* [<img src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" width="16" /> Krzysztof Rewak](https://orcid.org/0009-0003-6847-8318)
* [<img src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" width="16" /> Karol Zygadło](https://orcid.org/0009-0004-6384-825X)

### Repository Structure
```
bottles/
 ├─ images/           # All dataset images (not tracked in GitHub)
 ├─ scripts/          # Utility scripts for analysis and preprocessing
 │    └─ stats.py     # Computes dataset statistics
 ├─ annotations/      # Annotations JSON files
 ├─ docs/             # Additional documentation or figures
 ├─ readme.md         # You are here
 └─ licence.md
```

### Naming Convention
File naming follows the pattern:
```
{type}_{color}_{fill}_{liquid}_{label}_{cap}_{index}.{extension}
```

For example:
```
vichy_brown_filled_light_labeled_crowned_001.jpg
```

Each component corresponds to one categorical attribute of the bottle.

### Available Scripts
#### Statistics
A handy script computes summary statistics for all images located in the `images/` directory. The script parses filenames according to the naming convention and prints:
- total number of images,
- distribution of each attribute,
- count of unique attribute combinations,
- any filenames that do not match the expected pattern.

Run with:
```
python -m scripts.stats
```

#### Validation
This script verifies the integrity and consistency of all images in the `images/` directory. It checks that filenames follow the expected naming convention, attributes match the allowed categories, and index numbering is correct within each attribute group.

The script reports:
- files with invalid or unparsable names,
- invalid attribute values,
- indexing issues such as missing indices or duplicates (per attribute group),
- detailed listings for all detected problems.

Run with:
```
python -m scripts.validate
```

The validator does not modify any files; it only reports inconsistencies.

#### Annotations
The annotation script creates a machine-readable JSON file describing all images in the dataset.  
It parses filenames according to the naming convention and extracts the full attribute set for each bottle.  
The resulting file provides a clean, structured representation of the dataset that can be used for further analysis, reproducibility, external tools, or downstream processing pipelines.

The generated annotation file contains, for each image:

- the filename,
- bottle type,
- glass color,
- fill level,
- liquid color,
- label presence,
- cap state,
- numerical index.

Annotations are written to `annotations/annotations.json`.

Run with:
```
python -m scripts.annotate
```

Only files that follow the expected naming scheme are included in the output. Files that cannot be parsed are skipped automatically.

### Dataset Statistics
```
Total images: 584

Attribute distributions:
- type:
  - vichy: 308
  - euro: 214
  - vichylight: 52
  - kraft: 6
  - bugel: 3
  - tulip: 1
- color:
  - brown: 584
- fill:
  - filled: 224
  - overfilled: 144
  - unfilled: 136
  - empty: 80
- liquid:
  - transparent: 458
  - light: 80
  - dark: 39
  - black: 7
- label:
  - labeled: 434
  - unlabeled: 150
- cap:
  - open: 423
  - crowned: 161

Unique combinations : 34
  - vichy_brown_filled_light_labeled_crowned: 72
  - euro_brown_overfilled_transparent_labeled_open: 57
  - euro_brown_unfilled_transparent_labeled_open: 37
  - vichy_brown_unfilled_transparent_labeled_open: 37
  - euro_brown_filled_transparent_labeled_open: 35
  - vichy_brown_overfilled_transparent_labeled_open: 34
  - vichy_brown_filled_dark_labeled_crowned: 31
  - euro_brown_unfilled_transparent_unlabeled_open: 27
  - vichy_brown_filled_transparent_labeled_open: 27
  - euro_brown_empty_transparent_labeled_open: 22
  - vichy_brown_empty_transparent_unlabeled_crowned: 19
  - vichylight_brown_unfilled_transparent_labeled_open: 16
  - vichy_brown_overfilled_transparent_unlabeled_open: 15
  - vichy_brown_filled_transparent_unlabeled_open: 14
  - vichylight_brown_overfilled_transparent_labeled_open: 14
  - vichy_brown_empty_transparent_labeled_open: 13
  - vichylight_brown_filled_transparent_labeled_open: 13
  - vichy_brown_unfilled_transparent_unlabeled_open: 12
  - euro_brown_filled_transparent_unlabeled_open: 11
  - euro_brown_overfilled_transparent_unlabeled_open: 11
  - vichylight_brown_empty_transparent_labeled_open: 9
  - vichy_brown_filled_transparent_unlabeled_crowned: 8
  - euro_brown_empty_transparent_unlabeled_open: 7
  - euro_brown_filled_black_labeled_crowned: 7
  - vichy_brown_overfilled_transparent_unlabeled_crowned: 7
  - vichy_brown_empty_transparent_unlabeled_open: 6
  - vichy_brown_unfilled_dark_unlabeled_crowned: 5
  - bugel_brown_empty_light_labeled_crowned: 3
  - kraft_brown_filled_transparent_labeled_crowned: 3
  - kraft_brown_filled_transparent_labeled_open: 3
  - vichy_brown_overfilled_dark_unlabeled_crowned: 3
  - vichy_brown_overfilled_light_unlabeled_crowned: 3
  - vichy_brown_unfilled_light_unlabeled_open: 2
  - tulip_brown_empty_transparent_labeled_open: 1
```

### Citation
If you use this dataset, please cite:

```
@dataset{...}
```

### License
For full details regarding dataset and code licensing, please refer to  the [licence.md](licence.md) file included in this repository.

### Contact
For questions, corrections, or contributions, please open an issue or contact the authors.
