import json
from shutil import copyfile

def one_to_three(all_data):
    divided_data={"1":{}, "2":{}, "3":{}}
    for k in all_data:
        subtask=k[0]
        divided_data[subtask][k]=all_data[k]
    return divided_data

def get_next_s2_id(qid_location):
    with open(qid_location, 'r') as qid_file:
        q_ids=json.load(qid_file)
        return q_ids["2"]+1

def enrich_s2(q, a, next_id, num_zeros, num_ones):
    counter=0
    for s1_qid, qdata in q["1"].items():
        if counter>=num_zeros+num_ones: # copying of questions is done
            break
        adata=a["1"][s1_qid]
        new_qid='2-%d' % next_id
        print(new_qid)
        next_id+=1
        qdata['subtask']=2
        qdata['verbose_question']=qdata['verbose_question'].replace('Which', 'How many', 1).replace('event', 'events', 1)

        src='output/system_input/%s.conll' % s1_qid
        dst='output/system_input/%s.conll' % new_qid
        if counter<num_zeros: # copy it as a question with zero answer
        # in this case, we have to modify the answer key and the conll result    
            skip_docs=set(docid for inc in adata["answer_docs"] for docid in adata["answer_docs"][inc])
            print(skip_docs)
            adata["answer_docs"]={}
            adata["numerical_answer"]=0

        else: #copy as it is
            copyfile(src, dst)          

        q["2"][new_qid]=qdata
        a["2"][new_qid]=adata
        counter+=1
    return q,a


if __name__=="__main__":
    answers_file="output/answers.json"
    questions_file="output/questions.json"
    qid_location="trial_bin/q_id.json"

    num_zeros=10 # number of questions to draw from S1 but remove the answer docs
    num_ones=10 # number of questions to copy from s1 to s2

    with open(answers_file, 'r') as afile:
        answers=json.load(afile)

    with open(questions_file, 'r') as qfile:
        questions=json.load(qfile)

    a=one_to_three(answers)
    print(len(a["1"]), len(a["2"]), len(a["3"]), len(answers))
    q=one_to_three(questions)

    next_qid=get_next_s2_id(qid_location)

    q,a=enrich_s2(q,a, next_qid, num_zeros, num_ones)

    print(len(a["1"]), len(a["2"]), len(a["3"]), len(answers))

    for x in ["1", "2", "3"]:
        basis=questions_file.rsplit('/', 1)[0]
        q_outfile='%s/%s_questions.json' % (basis, x)
        a_outfile='%s/%s_answers.json' % (basis, x)
        with open(q_outfile, 'w') as wq:
            wq.write(json.dumps(q[x], indent=4, sort_keys=True))

        with open(a_outfile, 'w') as wa:
            wa.write(json.dumps(a[x], indent=4, sort_keys=True))

