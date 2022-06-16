try:
    import unzip_requirements
except ImportError:
    pass

import traceback
from typing import Optional
import json
import datetime

from utils.db import db_session, UserProject, Lesson
from utils.sqs import queue, send_sqs
from utils.file import project_to_s3
from configs import TIME_LIMIT


def select_project(event: Optional[dict] = None, context: Optional[dict] = None):
    """
    Select ``UserProject` that is not accessed for more than ``TIME_LIMIT`` seconds.
    """

    time_thres = datetime.datetime.utcnow() - datetime.timedelta(seconds=TIME_LIMIT)

    # Query
    rows = (
        db_session.query(UserProject)
        .filter(UserProject.active.is_(True))
        .filter(UserProject.recent_activity_at < time_thres)
        .limit(50)
        .all()
    )

    # SQS enqueue
    for row in rows:
        print(row.id, row.recent_activity_at)
        send_sqs({"id": row.id})

    return True


def backup_project(event: Optional[dict] = None, context: Optional[dict] = None):
    """
    {
        "Records": [
            {
            "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
            "receiptHandle": "MessageReceiptHandle",
            "body": "Hello from SQS!",
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1523232000000",
                "SenderId": "123456789012",
                "ApproximateFirstReceiveTimestamp": "1523232000001"
            },
            "messageAttributes": {},
            "md5OfBody": "{{{md5_of_body}}}",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
            "awsRegion": "us-east-1"
            }
        ]
    }
    """

    time_thres = datetime.datetime.utcnow() - datetime.timedelta(seconds=TIME_LIMIT)

    lessons = {}

    records = event.get("Records", [])
    for record in records:
        try:
            body = record["body"]
            data = json.loads(body)
            project_id = data["id"]

            proj = (
                db_session.query(UserProject)
                .filter(UserProject.active.is_(True))
                .filter(UserProject.recent_activity_at < time_thres)
                .filter(UserProject.id == project_id)
                .first()
            )

            if not proj:
                print(f"Project {project_id} is already processed or re-activate.")
                continue

            print(f"ID: {proj.id} | active at: {proj.recent_activity_at}")

            if proj.lesson_id in lessons:
                lesson = lessons[proj.lesson_id]
            else:
                lesson = lessons[proj.lesson_id] = db_session.query(Lesson).get(proj.lesson_id)

            project_to_s3(lesson.course_id, lesson.id, proj)

            proj.active = False
            db_session.add(proj)
            db_session.commit()  # Commit on each loop in order to prevent overwriting zip object on S3
        except (json.JSONDecodeError, KeyError):
            traceback.print_exc()
            continue

    return True


if __name__ == "__main__":
    select_project()

    msgs = queue.receive_messages(MaxNumberOfMessages=1)
    backup_project(
        {
            "Records": [
                {
                    "body": msg.body,
                }
                for msg in msgs
            ]
        }
    )
