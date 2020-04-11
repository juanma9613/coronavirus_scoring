import json
import traceback
from utils.utils import Scorer
import os

def score(event, context):
    try:
        #questions = json.loads(event['body'])
        with open("./json2score/input.json") as fp:
            questions = json.load(fp)
        print(questions)
        scorer = Scorer()
        scoring_result = scorer.score(questions)
        response = {
            "statusCode": 200,
            "body": json.dumps(scoring_result),
            "headers": {"Access-Control-Allow-Origin": '*'}
        }

    except Exception as e:
        traceback.print_stack(e)
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
