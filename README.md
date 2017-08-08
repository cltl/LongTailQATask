# SemEval-2018 Task 5 #

Welcome!

This repository contains the code for the SemEval-2018 task 5 **Counting Events and Participants within Highly Ambiguous Data covering a very long tail**. 

For general information on this task and to join as a participant, please visit our Codalab competition site: https://competitions.codalab.org/competitions/17285.

The code distribution of this task consists of the following:
  - Installation script to get you started with the dependencies (*see https://github.com/cltl/LongTailQATask/blob/master/INSTALL.md* for an explanation of the installation)
  - The task data, consisting of questions and the documents (for the trial data, we also provide the answers)
  - Evaluation scripts and baselines (*visit https://github.com/cltl/LongTailQATask/blob/master/Evaluation/README.md* for details on the evaluation)

### Contact: ###

Filip Ilievski (f.ilievski@vu.nl)

Marten Postma (m.c.postma@vu.nl)

### CODE STRUCTURE and PILOT ###

The pilot is described in *Section 7* of our proposal.

Following the conceptual division in the proposal text, the task implementation is divided into two parts: 

1) The folder **EventRegistries** contains the data preparation scripts and data (described in *Section 4.1* of the proposal)
2) The folder **QuestionCreation** creates questions based on the data in 1. and generates question stats (as described in *Section 5.3* of our proposal)

### 1) EventRegistries

As we describe in *Section 7* of the proposal, in our pilot we only use the GVA data to create questions. However, we have also crawled and inspected the data from the FireRescue1 database.

#### 1.1) GunViolenceArchive (GVA)

The main script that crawls all frames from the GVA database, and all corresponding articles from Archive.org is `Crawler.py`. This script also normalizes the incident locations to Wikipedia URIs and detects the DCT of a document. It uses two helper scripts: `utils.py` where many functions are implemented, and `classes.py` where we define a set of object-oriented classes.

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

The main question creation notebooks are `CreateQ.ipynb` and `Stats.ipynb`, which create questions and generate per-question statistics. These rely on the classes in `classes.py` and the utility scripts: `createq_utils.py`, `display_utils.py`, and `look_up_utils.py`.

Other notable notebooks are `Participant.ipynb` and `Location check.ipynb`, which inspect the ambiguity that might occur with the participants and the locations in the data.

