import json
import os
import pandas as pd
import numpy as np
import traceback

QUESTION_TABLE_PATH = "./json2score/questions.csv"
QUESTION_TYPE_TABLE_PATH = "./json2score/questions_type.csv"

def transform_key_value_pair(kv_pairs, key, dictionary):
    """
    Transforms a dictionary with inside dictionaries into key value pairs
    """
    if type(dictionary) is dict:
        for new_key, new_value in dictionary.items():
            if key is not None:
                transform_key_value_pair(kv_pairs, key + '_' + str(new_key), new_value)
            else:
                transform_key_value_pair(kv_pairs, new_key, new_value)
    else:
        kv_pairs[key] = dictionary

class Scorer():
    def __init__(self):
        self.question_table_path = QUESTION_TABLE_PATH
        self.question_type_table_path = QUESTION_TYPE_TABLE_PATH
        self.question_table = self._load_questions_table()
        self.question_type_table = self._load_questions_type_table()
        self.question_table_complete = self._join_tables()
        self.not_score_questions = self._get_not_scoring_questions()

    def _load_questions_table(self):
        question_table = pd.read_csv(self.question_table_path, header=0, index_col='question_id')
        return question_table

    def _load_questions_type_table(self):
        question_type_table = pd.read_csv(self.question_type_table_path, header=0)
        return question_type_table

    def _join_tables(self):
        question_complete = pd.merge(self.question_table,
                                     self.question_type_table, how='left',
                                     left_on='type_id', right_on='type_id')
        return question_complete

    def _get_not_scoring_questions(self):
        not_score_questions = self.question_table_complete[self.question_table_complete['answer'].isnull()]
        return not_score_questions['question'].tolist()

    def validate(self, q_attr, answer_q):
        type_q = None
        if q_attr['type'].unique() == 'bool':
            if answer_q in [True, False, 0, 1]:
                is_valid = True
                type_q = 'bool'
            else:
                is_valid = False
        elif q_attr['type'].unique() == 'choice':
            if (q_attr['answer']==answer_q).any():
                is_valid = True
                type_q = 'choice'
            else:
                print("Choice answer not found!")
        elif q_attr['type'].unique() == 'text':
            if answer_q :
                is_valid = True
                type_q = 'text'
            else:
                is_valid = False
        elif q_attr['type'].unique() == 'float':
            try: 
                answer_q = float(answer_q)
                type_q = 'float'
                is_valid = True
            except:
                is_valid = False
        else:
            print("TYPE NOT AVAILABLE")
            raise NotImplementedError
        return is_valid, type_q

    def comparison_apply(self, row, answer_q):
        output = getattr(row['answer'], row['comparison'])(answer_q)
        return output

    def score_answer(self, q_attr, answer_q, type_q):
        if (q_attr['comparison']=='eq').all() and type_q != 'bool':#For choice
            current_score = ((q_attr['answer']==answer_q)*1.0*q_attr['score'].astype(float)).sum()
            return current_score
        elif (q_attr['comparison']=='eq').all() and type_q == 'bool':
            current_score = ((q_attr['answer'].astype(bool)==answer_q)*1.0*q_attr['score'].astype(float)).sum()
            return current_score
        else:
            return 0

    def score(self, questions):
        """
        Parameters:
        -----------
        question : list(dict)

        Return:
        -------
        scoring : float
        """
        scoring = 0.
        new_questions = dict()
        transform_key_value_pair(new_questions, None, questions)
        for q in new_questions:
            if q in self.not_score_questions:
                pass
            else:
                answer_q = new_questions[q]
                q_attr = self.question_table_complete.loc[self.question_table_complete['question']==q, :]
                is_valid, type_q = self.validate(q_attr, answer_q)
                if is_valid:
                    scoring += self.score_answer(q_attr, answer_q, type_q)
                else:
                    print("Answer not valid")
                    print("Question", q)
                    print("answer_q", answer_q)
        return {'scoring': float(scoring)}


def score(event, context):
    try:
        questions = json.loads(event['body'])
        scorer = Scorer()
        scoring_result = scorer.score(questions)
        response = {
            "statusCode": 200,
            "body": json.dumps(scoring_result),
            "headers": {"Access-Control-Allow-Origin": '*'}
        }

    except Exception as e:
        #traceback.print_exc()
        response = {
            "statusCode": 500,
            "body": "Failed to score",
            "headers": {"Access-Control-Allow-Origin": '*'}
        }

    return response


if __name__ == "__main__":
    context = None
    event = None
    print(score(event, context))
