import json
import traceback
from utils.utils import Scorer
import random
import pandas as pd

possible_answers = {'age': ['0 - 5', '6 - 11', '12 - 18', '19 - 26', '27 - 59', '>60'],
                    'bodyTemperature': ['', "36.0", "38.0", "40.0"],
                    'diagnosedWith_ASTHMA': [True, False],
                    'diagnosedWith_AUTOIMMUNEDISEASE': [True, False],
                    'diagnosedWith_KIDNEYDISEASE': [True, False],
                    'diagnosedWith_CHRONICLUNGDISEASE': [True, False],
                    'diagnosedWith_DIABETES': [True, False],
                    'diagnosedWith_HYPERTENSIONARTERIAL': [True, False],
                    'diagnosedWith_IMMUNOSUPRESSION': [True, False],
                    'diagnosedWith_CORONARYHEARTDISEASE': [True, False],
                    'hasBeenInContactWithInfected': [True, False],
                    'hasBeenTested': [True, False],
                    'isolationStatus': ['NOT_IN_ISOLATION',
                                        'ISOLATION_DUE_TO_TRAVEL',
                                        'ISOLATION_DUE_TO_GOVERNMENT_ORDERS'],
                    'name': 'Felipe Torres',
                    'nationalId': '1152448890',
                    'phone': '3215136527',
                    'postalCode': '050030',
                    'score': -1,
                    'sex': ['MALE', 'FEMALE', 'OTHER'],
                    'IsPregnant': [True, False],
                    'smokingHabit': ['CURRENTLY', 'USED_TO', 'NEVER'],
                    'submissionTimestamp': 1585725018170,
                    'symptomStart': '',
                    'symptoms_DIARRHEA': [True, False],
                    'symptoms_DRY_COUGH': [True, False],
                    'symptoms_EXHAUSTION': [True, False],
                    'symptoms_FEVER': [True, False],
                    'symptoms_HEADACHE': [True, False],
                    'symptoms_HEAVY_BREATHING': [True, False],
                    'symptoms_MUSCLE_ACHING': [True, False],
                    'symptoms_NAUSEA_OR_VOMITING': [True, False],
                    'symptoms_NO_SMELL': [True, False],
                    'symptoms_NO_TASTE': [True, False],
                    'symptoms_RUNNY_NOSE': [True, False],
                    'symptoms_SLIME_COUGH': [True, False],
                    'symptoms_SORE_THROAT': [True, False],
                    'videoUrl': ''}
total_tests = 1000
tests = {}
scorer = Scorer()
for i in range(total_tests):
    test_i = {}
    for question, answers in possible_answers.items():
        if type(answers) == list:
            answer = random.choice(answers)
            test_i[question] = answer
        else:
            test_i[question] = answers
    results = scorer.score(test_i, transform=False)
    test_i.update(results)
    tests[i] = test_i

output = pd.DataFrame.from_dict(tests, orient='index')
output.to_csv('./testing/tests.csv')
