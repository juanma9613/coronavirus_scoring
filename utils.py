import os
import pandas as pd

QUESTION_TABLE_PATH = "./json2score/questions.csv"


def transform_key_value_pair(kv_pairs, key, dictionary):
    """
    Transforms a dictionary (kv_pairs) with inside dictionaries into key value pairs
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
        self.question_table_complete = self._load_questions_table()
        self.not_score_questions = self._get_not_scoring_questions()

    def _load_questions_table(self):
        question_table = pd.read_csv(self.question_table_path, header=0,
                                     index_col='question_id', delimiter=',',
                                     dtype={'type': str, 'question': str, 
                                            'answer': str, 'score': int,
                                            'comparison': str}, engine='c', 
                                            memory_map=True, float_precision=None)
        return question_table

    def _get_not_scoring_questions(self):
        not_score_questions = self.question_table_complete[self.question_table_complete['answer'].isnull(
        )]
        return not_score_questions['question'].tolist()

    def validate(self, q_attr, answer_q):
        type_q = None
        if q_attr.iloc[0, 0] == 'bool':
            if answer_q in [True, False, 0, 1]:
                is_valid = True
                type_q = 'bool'
            else:
                is_valid = False
        elif q_attr.iloc[0, 0] == 'choice':
            if (q_attr['answer'] == answer_q).any():
                is_valid = True
                type_q = 'choice'
            else:
                is_valid = False
                print("Choice answer not found!")
        elif q_attr.iloc[0, 0] == 'text':
            if answer_q:
                is_valid = True
                type_q = 'text'
            else:
                is_valid = False
        elif q_attr.iloc[0, 0] == 'float':
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

    def comparison_apply(self, row, answer_q, type_q):
        if type_q == 'float':
            output = getattr(float(answer_q), '__' + row['comparison'] + '__')(float(row['answer']))
        return output

    def score_answer(self, q_attr, answer_q, type_q):
        if (q_attr['comparison'] == 'eq').all() and type_q == 'choice':  # For choice
            current_score = ((q_attr['answer'] == answer_q)*1.0*q_attr['score'].astype(float)).sum()
            return current_score
        elif (q_attr['comparison'] == 'eq').all() and type_q == 'bool':
            current_score = ((q_attr['answer'].astype(bool) == answer_q)
                             * 1.0*q_attr['score'].astype(float)).sum()
            return current_score
        elif type_q == 'float':
            current_score = ((q_attr.apply(lambda row: self.comparison_apply(row, answer_q, type_q), axis=1))
                             * 1.0*q_attr['score'].astype(float)).max()
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
                q_attr = self.question_table_complete.loc[self.question_table_complete['question'] == q, :]
                is_valid, type_q = self.validate(q_attr, answer_q)
                if is_valid:
                    scoring += self.score_answer(q_attr, answer_q, type_q)
                else:
                    print("Answer not valid")
                    print("Question", q)
                    print("answer_q", answer_q)
        return {'scoring': float(scoring)}
