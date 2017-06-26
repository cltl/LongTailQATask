### Evaluation ###

Evaluation in this task is performed on three levels: mention-level, document-level, and incident-level. All these can be run by executing the shell script `evaluate.sh` in this way:

`sh evaluate.sh <DATA_DIRECTORY>`

The data directory must contain two non-empty folders: `system` (containing the system-processed files) and `gold` (containing the gold-annotated files). The `DATA_DIRECTORY` argument is optional: by default, the data is located in the folder `../Data/`. 

Before running the `evaluate.sh` script on their own files, we advice participants to first ensure the evaluation script is functioning as expected, i.e. if the evaluation on all three levels gives the correct scores. This can be done by executing `sh evaluate.sh Test`, which will evaluate the documents for 5 questions, found in the `Test` folder.

#### Explanation of the levels of evaluation ####

The mention-level evaluation uses an external scoring script for event coreference from https://github.com/conll/reference-coreference-scorers/. This package is automatically cloned when running the evaluation script for the first time.

The document-level evaluation computes the precision, recall and F1 measure on a document level (were the documents suggested by a system really part of the answer documents for a question).

On incident-level, we implemented two metrics: exact match accuracy and RMSE. The latter differs from the former by also considering the distance from the correct answer.

For each of the three levels of evaluation, the scores per question are then averaged over all questions to compute a single score for that level.
