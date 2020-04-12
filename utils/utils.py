import os
import pandas as pd

QUESTION_TABLE_PATH = "./json2score/questions_final.csv"


def transform_key_value_pair(kv_pairs, key, dictionary):
    """
    Transforms a dictionary (kv_pairs) with inside dictionaries into key value pairs
    Kind of flatten dict
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
        self.epidemiological_group = ['hasBeenInContactWithInfected']
        self.clinical_group = ['symptoms_FEVER', 'symptoms_HEAVY_BREATHING', 'symptoms_DRY_COUGH']

    def _load_questions_table(self):
        question_table = pd.read_csv(self.question_table_path, header=0,
                                     index_col='question_id', delimiter=',',
                                     dtype={'type': str, 'question': str,
                                            'answer': str, 'score': float,
                                            'comparison': str, 'valid_q': int,
                                            'risk': str},
                                     engine='c', memory_map=True,
                                     float_precision=None)
        return question_table

    def _get_not_scoring_questions(self):
        not_score_questions = self.question_table_complete[self.question_table_complete['valid_q'] == 0]
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
        if (q_attr['comparison'] == 'eq').all() and type_q == 'choice':
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
            print("Couldn't score")
            print(q_attr)
            print(answer_q)
            return 0

    def score(self, questions, transform=True):
        """
        Parameters:
        -----------
        question : list(dict)

        Return:
        -------
        scoring_result : dict
            covid score and patient score
        """
        covid_score = 0
        patient_score = 0
        epidemiology_count = 0
        clinical_count = 0
        if transform:
            new_questions = dict()
            transform_key_value_pair(new_questions, None, questions)
        else:
            new_questions = questions
        for q in new_questions:
            if q in self.not_score_questions:
                pass
            else:
                answer_q = new_questions[q]
                q_attr = self.question_table_complete.loc[self.question_table_complete['question'] == q, :]
                if (len(q_attr)) == 0:
                    print("Question not in db: ", q)
                    continue
                if (q_attr['risk'] == 'patient').all():
                    is_valid, type_q = self.validate(q_attr, answer_q)
                    if is_valid:
                        patient_score += self.score_answer(q_attr, answer_q, type_q)
                    else:
                        print("Answer not valid: ", answer_q)
                        print("Question", q)
                elif (q_attr['risk'] == 'covid').all():
                    is_valid, type_q = self.validate(q_attr, answer_q)
                    if is_valid:
                        current_score = self.score_answer(q_attr, answer_q, type_q)
                        if current_score > 0:
                            if q in self.clinical_group:
                                clinical_count += 1
                            if q in self.epidemiological_group:
                                epidemiology_count += 1
                        else:
                            pass
                        covid_score += current_score
                    else:
                        print("Answer not valid: ", answer_q)
                        print("Question", q)
                else:
                    print("Risk not found, is a valid question: ", q_attr)
        if (epidemiology_count >= 1 and clinical_count >= 1) or (clinical_count >= 2):
            covid_score *= 3

        if covid_score <= 4:
            covid_risk = 'low'
        elif covid_score > 4 and covid_score < 10:
            covid_risk = 'medium'
        else:
            covid_risk = 'high'

        if patient_score == 0:
            patient_risk = 'low'
        elif patient_score == 1:
            patient_risk = 'medium'
        else:
            patient_risk = 'high'

        return {'covid_score': float(covid_score),
                'covid_risk': covid_risk,
                'patient_score': float(patient_score),
                'patient_risk': patient_risk}
