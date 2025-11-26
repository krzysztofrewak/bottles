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
 │    └─ annotate.py  # Generates annotations
 │    └─ build.py     # Validates files, builds readme and annotations
 │    └─ import.py    # Imports new images into dataset 
 │    └─ stats.py     # Computes dataset statistics
 │    └─ utils.py     # Helper functions for other scripts
 │    └─ validate.py  # Validates filenames of images
 ├─ annotations/      # Annotations JSON files
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
#### Builder
The `build.py` script provides a unified pipeline for maintaining the dataset and its accompanying documentation. It performs the following steps in a controlled sequence:
- validates the entire dataset structure using `scripts.validate`,
- generates updated dataset statistics by executing `scripts.stats`,
- injects these statistics into the project’s `readme.md` based on the template in `templates/readme.md`,
- regenerates annotation files using `scripts.annotate`.

The script stops automatically if validation fails, ensuring that no inconsistent or incomplete state is written to the repository.

Run with:
```
python -m scripts.build
```


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
The annotation script creates a machine-readable JSON file describing all images in the dataset. It parses filenames according to the naming convention and extracts the full attribute set for each bottle. The resulting file provides a clean, structured representation of the dataset that can be used for further analysis, reproducibility, external tools, or downstream processing pipelines.

The generated annotation file contains, for each image:
- the filename and its extension,
- numerical index and group size,
- bottle type,
- glass color,
- fill level,
- liquid color,
- label presence,
- cap state.

Example in JSON format as follows:
```json
{
  "filename": "vichy_brown_filled_light_labeled_crowned_008.HEIC",
  "extension": "heic",
  "collection": {
    "index": 8,
    "of": 72
  },
  "parameters": {
    "type": "vichy",
    "color": "brown",
    "fill": "filled",
    "liquid": "light",
    "label": "labeled",
    "cap": "crowned"
  }
}
```

Annotations are written to `annotations/annotations.json`.

Run with:
```
python -m scripts.annotate
```

Only files that follow the expected naming scheme are included in the output. Files that cannot be parsed are skipped automatically.

### Dataset Statistics
<!-- STATS_START -->
<!-- STATS_END -->

### Citation
If you use this dataset, please cite:
```
@dataset{...}
```

### License
For full details regarding dataset and code licensing, please refer to  the [licence.md](licence.md) file included in this repository.

### Contact
For questions, corrections, or contributions, please open an issue or contact the authors.
