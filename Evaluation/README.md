### Evaluation ###

#### Explanation of the levels of evaluation ####

Evaluation in this task is performed on three levels: incident-level, document-level, and mention-level. 

The incident-level evaluation compares the numeric answer provided by the system to the gold answer for each of the questions. The comparison is done twofold: by exact matching and by RMSE for difference scoring.

The document-level evaluation compares the set of answer documents between the system and the gold standard. The sets of documents for each question are compared by the customary metrics of Precision, Recall and F1-score.

The mention-level evaluation is essentially a cross-document event coreference evaluation. We use the customary metrics for event coreference: BCUB, BLANC, CEAF_E, CEAF_M, and MUC.

For each of the three levels of evaluation, the scores per question are then averaged over all questions to compute a single score for that level.

#### Answer formats ####

Users provide two different outputs:

  1) For the incident- and the document-level evaluation, systems provide a single JSON file per subtask. This JSON file contains the numeric answers to all questions in that subtask, as well as the set of documents that provide evidence for the answer. For example:
  `{'1-101':
   {
      'numerical_answer': 3,
      'answer_docs': {'8', '11', '15', '17', '87'}
   }
  }`

  2) For the mention-level evaluation, systems are asked to provide a number of CoNLL files that contain mention-level event coreference on a cross-document level. Each CoNLL file represents the documents belonging to a single question. The users should only annotate the answer documents, i.e. the ones that provide evidence for the answer to the question. Each document in the CoNLL file starts with a *#begin document* row, and it ends with *#end document*. Each row of the document in the CoNLL file represents a single token, with the following fields: `token_id`, `token`, `document_part` (whether it is the title, the content or the document creation time), and `coreference_chain`.  Example CoNLL:
  
`#begin document (748f14771b3febdc874b7827d151b6e0);
748f14771b3febdc874b7827d151b6e0.DCT	2017-01-01	DCT	-
748f14771b3febdc874b7827d151b6e0.1.0	Police	TITLE	-
748f14771b3febdc874b7827d151b6e0.1.1	:	TITLE	-
748f14771b3febdc874b7827d151b6e0.1.2	15-Year	TITLE	-
...
748f14771b3febdc874b7827d151b6e0.1.0	A	BODY	-
748f14771b3febdc874b7827d151b6e0.1.1	16-year	BODY	-
748f14771b3febdc874b7827d151b6e0.1.2	-	BODY	-
748f14771b3febdc874b7827d151b6e0.1.3	old	BODY	-
748f14771b3febdc874b7827d151b6e0.1.4	girl	BODY	-
...
#end document
#begin document (6c9fa7f335e78ca818125c626d3bc216);
6c9fa7f335e78ca818125c626d3bc216.DCT	2017-01-03	DCT	-
6c9fa7f335e78ca818125c626d3bc216.1.0	Teen	TITLE	-
6c9fa7f335e78ca818125c626d3bc216.1.1	suspect	TITLE	-
...`
  
**Note:** Both for 1) and 2), the systems can decide to answer/annotate a subset of all questions. Our scripts are flexible with respect to this, and we note also the number of questions answered.

#### Running the evaluation scripts ####

Our evaluation is based on two Bash scripts, corresponding to the answer formats defined above:

  1) The incident- and document-level answers are evaluated by executing the Bash script `evaluate_answers.sh` in this way:

`bash evaluate_answers.sh <SYSTEM_JSON> <GOLD_JSON> <OUTPUT_JSON>`

`SYSTEM_JSON` and `GOLD_JSON` are the JSON files that contain the system and gold answers, correspondingly, with their evidence documents. As mentioned above, this Bash script computes accuracy of the numeric answers, RMSE of the numeric answers, and Prec/Recall/F1 of the documents per question. We print the resulting scores in stdout, but we also store them in `OUTPUT_JSON` for convenience of our participants.

  2) The mention-level annotations in CoNLL format are evaluated by executing the Bash script `evaluate_mentions.sh` in this way:

`bash evaluate_mentions.sh <SYSTEM_DIR> <GOLD_DIR> <OUTPUT_DIR>`

This setup is analogous to the setup in 1), except that this time the script requires its input parameters to be the system and gold directories which contain the CoNLL annotations. Similarly as before, the output is printed in stdout, but one scoring file per evaluation metric (MUC, CEAF_E, CEAF_M, BLANC, BCUB) is stored in `OUTPUT_DIR`. 

The mention-level evaluation uses an external scoring script for event coreference from https://github.com/conll/reference-coreference-scorers/. This package is automatically cloned when running the evaluation script for the first time.

#### TESTS ####

Before running the `evaluate_answers.sh` and `evaluate_mentions.sh` scripts on their own files, we advice task participants to first ensure the evaluation scripts are functioning as expected, i.e. if the evaluation on all levels gives the correct scores. This can be done by executing ??? (TODO: finish this later)
