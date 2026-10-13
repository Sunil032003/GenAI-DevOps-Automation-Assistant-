from Analyzer import analyze_project


def test_analyze_python_project():
    # TC001 - Analyze Python Project
    files = ["main.py", "requirements.txt"]
    expected = {"language": "Python", "project_type": "Python Project"}
    assert analyze_project(files) == expected

def test_analyze_javascript_project():
    # TC002 - Analyze JavaScript Project
    files = ["script.js", "package.json"]
    expected = {"language": "JavaScript", "project_type": "Node.js Project"}
    assert analyze_project(files) == expected

def test_analyze_java_project():
    # TC003 - Analyze Java Project
    files = ["App.java", "pom.xml"]
    expected = {"language": "Java", "project_type": "Java Maven Project"}
    assert analyze_project(files) == expected

def test_analyze_unknown_project():
    # TC004 - Analyze Unknown Project
    files = ["README.md", "LICENSE"]
    expected = {"language": "Unknown", "project_type": "Unknown"}
    assert analyze_project(files) == expected