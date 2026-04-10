from fastapi import FastAPI
from pydantic import BaseModel
import re

app = FastAPI(title="LN Code Review API")

class CodeRequest(BaseModel):
    program: str
    code: str


def analyze_code(code):
    issues = []
    lines = code.split("\n")

    for i, line in enumerate(lines, start=1):
        l = line.lower()

        # RULE 1: select *
        if re.search(r"select\s+\*", l):
            if "for update" not in code.lower():
                issues.append({
                    "rule": "Avoid SELECT *",
                    "severity": "BLOCKER",
                    "message": "Use explicit fields unless using for update",
                    "line": i
                })

        # RULE 2: string empty check
        if re.search(r'<> ""|= ""', line):
            if "where" not in l:
                issues.append({
                    "rule": "String Empty Check",
                    "severity": "BLOCKER",
                    "message": "Use isspace() instead of \"\"",
                    "line": i
                })

        # RULE 3: division safety
        if "/" in line:
            if i == 1 or "if" not in lines[i-2].lower():
                issues.append({
                    "rule": "Division Safety",
                    "severity": "BLOCKER",
                    "message": "Check denominator before division",
                    "line": i
                })

    return issues


@app.post("/ln-code-review")
def review_code(req: CodeRequest):

    issues = analyze_code(req.code)

    blocker = len([i for i in issues if i["severity"] == "BLOCKER"])
    major = len([i for i in issues if i["severity"] == "MAJOR"])
    warning = len([i for i in issues if i["severity"] == "WARNING"])

    return {
        "program": req.program,
        "status": "FAIL" if blocker > 0 else "PASS",
        "summary": {
            "blocker": blocker,
            "major": major,
            "warning": warning
        },
        "issues": issues
    }