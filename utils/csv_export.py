import csv
import io

from models import Analysis


def analysis_csv(analysis: Analysis) -> io.BytesIO:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Comment", "Label", "Confidence", "Username", "Timestamp"])
    for comment in analysis.comments:
        writer.writerow(
            [
                comment.comment_text,
                comment.label,
                f"{comment.confidence:.4f}",
                comment.username or "",
                comment.timestamp or "",
            ]
        )
    return io.BytesIO(output.getvalue().encode("utf-8-sig"))
