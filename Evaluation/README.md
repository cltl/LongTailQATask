### Evaluation ###

Evaluation in this task is performed on three levels: mention-level, document-level, and incident-level. All these can be run by executing the shell script `evaluate.sh` in this way:

`sh evaluate.sh <SYSTEM_OUTPUT> <GOLD_OUTPUT>`

#### Explanation of the levels of evaluation ####

The mention-level evaluation uses an external scoring script for event coreference from https://github.com/conll/reference-coreference-scorers/. This package is automatically cloned when running the evaluation script for the first time.

The document-level evaluation computes the precision, recall and F1 measure on a document level (were the documents suggested by a system really part of the answer documents for a question).

On incident-level, we implemented two metrics: exact match accuracy and RMSE. The latter differs from the former by also considering the distance from the correct answer.

For each of the three levels of evaluation, the scores per question are then averaged over all questions to compute a single score for that level.
