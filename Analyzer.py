def analyze_project(files):

    language = "Unknown"
    project_type = "Unknown"

    # Detect programming language
    if any(file.endswith(".py") for file in files):
        language = "Python"

    elif any(file.endswith(".js") for file in files):
        language = "JavaScript"

    elif any(file.endswith(".java") for file in files):
        language = "Java"

    # Detect project type
    if "requirements.txt" in files:
        project_type = "Python Project"

    elif "package.json" in files:
        project_type = "Node.js Project"

    elif "pom.xml" in files:
        project_type = "Java Maven Project"

    return {
        "language": language,
        "project_type": project_type
    }