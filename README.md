# LongTailQATask

This repository contains the code for the pilot of the task **Counting Events and Participants within Highly Ambiguous Data covering a very long tail** proposed to SemEval 2018. The pilot is described in *Section 7* of our proposal.

Following the conceptual division in the proposal text, the task implementation is divided into two parts: 

1) The folder **EventRegistries** contains the data preparation scripts and data (described in *Section 4.1* of the proposal)
2) The folder **QuestionCreation** creates questions based on the data in 1) and generates question stats (as described in *Section 5.3*)

### 1) EventRegistries

As we describe in *Section 7* of the proposal, in our pilot we only use the GVA data to create questions. However, we have also crawled and inspected the data from the FireRescue1 database.

#### 1.1) GunViolenceArchive (GVA)

The main script that crawls all frames from the GVA database, and all corresponding articles from Archive.org is `Crawler.py`. This script also normalizes the incident locations to Wikipedia URIs and detects the DCT of a document. It uses two scripts as input: `utils.py` where many functions are implemented, and `classes.py` where we define a set of object-oriented classes.

Overview of the directories in the GVA folder:

  * `frames/` contains the extracted structured data from the GVA website, stored in pandas Dataframes
  * `the_violent_corpus/` contains all documents that are used in this task, crawled from archive.org
  * `inspection_scripts_and_notebooks/` contains a set of scripts and Python notebooks that are primarily used to analyze various aspects of the data. Most importantly, `Stats.ipynb` generates stats (e.g. number of incidents per state) and `Verify_sources.ipynb` is used to verify that the incident information is found in an article.
  * `archive/` contains scripts that try to automatically archive websites in archive.org
  * `locations/` contains scripts that automatically link locations to wikipedia URIs
  * `cache_data/` contains caches that are used to improve the data, e.g. with respect to document creation times
  * `GVDB/` and `logs/` are not shown on github. The former deals with the annotations from the Gun Violence Database, while the latter contains various logs of the crawler.

#### 1.2) FireRescue1

The data is crawled with the Python Notebook file `Crawler.ipynb`, it is stored in `firerescue.pickle`, and we analyze it in `Inspect.ipynb`. 

### 2) QuestionCreation


### Contact:

Filip Ilievski (f.ilievski@vu.nl)
Marten Postma (m.c.postma@vu.nl)
