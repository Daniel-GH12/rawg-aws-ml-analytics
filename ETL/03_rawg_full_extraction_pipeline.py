{
  "Comment": "RAWG Full Extraction Pipeline",
  "StartAt": "RunExtractor",
  "States": {
    "RunExtractor": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "rawg_full_extractor_lambda",
        "Payload.$": "$"
      },
      "Retry": [
        {
          "ErrorEquals": [
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException",
            "States.TaskFailed"
          ],
          "IntervalSeconds": 10,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }
      ],
      "Next": "CheckIfFinished"
    },
    "CheckIfFinished": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.Payload.processed",
          "NumericEquals": 0,
          "Next": "Finish"
        }
      ],
      "Default": "WaitBeforeNext"
    },
    "WaitBeforeNext": {
      "Type": "Wait",
      "Seconds": 120,
      "Next": "RunExtractor"
    },
    "Finish": {
      "Type": "Succeed"
    }
  }
}