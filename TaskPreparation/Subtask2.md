# Subtask 2: Event-based questions with any amount of (zero to N) answer incidents.

Subtask 2 consists of event-based questions with any amount of (zero to N) answer incidents). This subtask differs from Subtask 1 in that the system now also has to determine the number of answer incidents, which makes the task harder. To make the task more realistic, we also include questions with zero as an answer.

## System input

For each question, the system input will consist of:
* a question in structured format
* a CoNLL file containing the documents which should be used to determine the answer to the question.

### Question

Questions consist of *event types* and *two event properties*.

**Event types** For the trial data of this subtask, we consider two event types:
* *killing*: at least one person is killed in the event
* *injuring*: at least one person is injured and did not die as a consequence of this injury, i.e. he or she survived.

Questions can contain individual event types or their combinations, e.g. *'killing', 'injuring'* means that systems are asked to find all *killing* and all *injuring* events.

**Event properties** Each question will contain two out of the three confusability factors (location, time, and participants).

An example of a question can be found below with the confusability factors location and time.

```
"2-5109": {
    "event_types": [
        "killing",
        "injuring"
    ],
    "location": [
        "http://dbpedia.org/resource/Iowa",
        "state"
    ],
    "subtask": 2,
    "time": [
        "2017",
        "year"
    ],
    "verbose_question": "How many ['killing', 'injuring'] events happened in 2017 (year) in ('Iowa',) (state) ?"
},
```

### CoNLL

Each question has a CoNLL file containing the documents that are provided to determine what the answer is. We will use an example to explain the format:

```
#begin document (5b29c7c81d4582870a9c575f030c54c3);
5b29c7c81d4582870a9c575f030c54c3.DCT    2017-03-25      DCT     -
5b29c7c81d4582870a9c575f030c54c3.1.0    1       TITLE   -
5b29c7c81d4582870a9c575f030c54c3.1.1    dead    TITLE   -
...
5b29c7c81d4582870a9c575f030c54c3.1.0    @FresnoSheriff  BODY    -
5b29c7c81d4582870a9c575f030c54c3.1.1    says    BODY    -
5b29c7c81d4582870a9c575f030c54c3.1.2    fatal   BODY    -
....
7d8913f95949225df7ee6621bef58d44.8.180  cruelty BODY    -
7d8913f95949225df7ee6621bef58d44.8.181  .       BODY    -
#end document
#begin document (4c9f07db3763c421ed21a28a297748b2);
4c9f07db3763c421ed21a28a297748b2.DCT    2017-03-16      DCT     -
4c9f07db3763c421ed21a28a297748b2.1.0    BB      TITLE   -
```

Some observations about the file format:
* every document starts with a line starting with *#begin document (DOC_ID);*
* the line after that always provides the document creation time.
* each line consists of four columns:
    * token identifier
    * token
    * discourse type: DCT | TITLE | BODY
    * coreference chain identifier (empty in systen input file)
* every documents ends with a line *#end document*

### answer format

System are asked to provide the following output format. Again, we will use an example to explain the format:

```
"2-5109": {
    "answer_docs": [
            "47eb060049372b35627c5c79802f06f6",
            "355b7e1b77eec7b4ece96c5c553befb1"
            "accad7f54e8a49ba32d3d1c048dbc5e9",
            "9beb5743a096861bb4dd868bc42036f4",
            "17faec40b59abd39b2f21b1ea38a78dd"
        ]
    },
    "numerical_answer": 2
},
```

Observations about the format:
* the answer file is a JSON file, in which each question is an entry in the JSON.
* For each question, there are two keys:
    * *numerical_answer*: how many incidents satisfy the question criteria? In the example, two incidents satisfy the criteria.
    * *answer_docs*: which are the supporting documents for the incidents, i.e. which documents provide the system with the information needed to answer the question? In the example, the first two document identifiers provide information about one incident and other three about the other incident.
