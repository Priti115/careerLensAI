"""Canonical role profiles used for prediction reranking and skill gaps."""

from __future__ import annotations


ROLE_PROFILES: dict[str, dict[str, object]] = {
    "Automation Testing": {
        "aliases": {"AUTOMATION TESTING", "Automation Testing", "Testing", "QA Automation"},
        "skills": {
            "selenium",
            "java",
            "python",
            "sql",
            "api testing",
            "test automation",
            "manual testing",
            "jira",
            "testng",
            "pytest",
            "postman",
            "jenkins",
            "git",
            "bug tracking",
            "linux",
        },
        "description": "quality assurance automation testing selenium api testing test cases regression testing defect tracking ci cd",
    },
    "Python Developer": {
        "aliases": {"Python Developer", "PYTHON DEVELOPER"},
        "skills": {
            "python",
            "flask",
            "fastapi",
            "django",
            "sql",
            "git",
            "api",
            "oop",
            "pytest",
            "pandas",
            "numpy",
            "docker",
        },
        "description": "python backend api development flask fastapi django databases testing deployment software engineering",
    },
    "Data Science": {
        "aliases": {"Data Science", "DATA SCIENCE", "Data Scientist"},
        "skills": {
            "python",
            "sql",
            "machine learning",
            "statistics",
            "pandas",
            "numpy",
            "scikit-learn",
            "data visualization",
            "tableau",
            "power bi",
            "nlp",
        },
        "description": "machine learning statistics data analysis predictive modeling python sql visualization experiments",
    },
    "Data Analyst": {
        "aliases": {"Data Analyst", "Business Analyst", "BUSINESS-DEVELOPMENT"},
        "skills": {"sql", "excel", "power bi", "tableau", "python", "statistics", "dashboarding", "data analysis"},
        "description": "data analysis dashboards reporting sql excel business metrics visualization stakeholder insights",
    },
    "Java Developer": {
        "aliases": {"Java Developer", "JAVA DEVELOPER"},
        "skills": {"java", "spring", "spring boot", "sql", "git", "api", "oop", "microservices", "maven", "junit"},
        "description": "java backend spring boot microservices api development databases unit testing enterprise software",
    },
    "Web Designing": {
        "aliases": {"Web Designing", "Web Developer"},
        "skills": {"html", "css", "javascript", "react", "bootstrap", "figma", "responsive design", "git"},
        "description": "web design frontend html css javascript responsive ui ux layout accessibility",
    },
    "DevOps Engineer": {
        "aliases": {"DevOps Engineer", "DEVOPS ENGINEER"},
        "skills": {"linux", "docker", "kubernetes", "aws", "ci/cd", "terraform", "jenkins", "monitoring", "git"},
        "description": "devops cloud automation deployment ci cd containers infrastructure monitoring reliability",
    },
    "Database": {
        "aliases": {"Database", "Database Administrator"},
        "skills": {"sql", "mysql", "postgresql", "oracle", "mongodb", "database", "query optimization", "backup"},
        "description": "database administration sql queries performance tuning backup recovery schema design",
    },
    "Network Security Engineer": {
        "aliases": {"Network Security Engineer", "Cyber Security"},
        "skills": {"network security", "linux", "firewall", "vulnerability assessment", "siem", "tcp/ip", "security"},
        "description": "network security cyber security firewalls vulnerability monitoring incident response linux",
    },
    "ETL Developer": {
        "aliases": {"ETL Developer"},
        "skills": {"sql", "etl", "python", "data warehouse", "spark", "hadoop", "airflow", "data pipeline"},
        "description": "etl data pipelines data warehouse sql transformation orchestration big data",
    },
    "Hadoop": {
        "aliases": {"Hadoop", "Big Data Engineer"},
        "skills": {"hadoop", "spark", "hive", "sql", "python", "scala", "big data", "linux"},
        "description": "big data hadoop spark hive distributed processing data engineering",
    },
    "Blockchain": {
        "aliases": {"Blockchain"},
        "skills": {"blockchain", "solidity", "smart contracts", "javascript", "web3", "ethereum", "git"},
        "description": "blockchain smart contracts solidity web3 decentralized applications ethereum",
    },
    "INFORMATION-TECHNOLOGY": {
        "aliases": {"INFORMATION-TECHNOLOGY", "Information Technology", "IT"},
        "skills": {"linux", "networking", "sql", "support", "windows", "security", "troubleshooting", "cloud"},
        "description": "information technology systems support networking troubleshooting security cloud operations",
    },
    "AGRICULTURE": {
        "aliases": {"AGRICULTURE", "Agriculture"},
        "skills": {"agriculture", "farming", "crop", "soil", "irrigation", "agronomy", "livestock"},
        "description": "agriculture farming crop soil irrigation agronomy farm management livestock",
    },
}


def canonical_role(role: str) -> str:
    """Map inconsistent dataset labels to a canonical role when known."""

    role_clean = role.strip()
    for canonical, profile in ROLE_PROFILES.items():
        aliases = {str(alias).lower() for alias in profile.get("aliases", set())}
        if role_clean.lower() == canonical.lower() or role_clean.lower() in aliases:
            return canonical
    return role_clean


def skills_for_role(role: str) -> set[str]:
    """Return required skills for a role."""

    profile = ROLE_PROFILES.get(canonical_role(role))
    if not profile:
        return {"communication", "problem solving", "project work", "technical documentation", "git"}
    return {str(skill).lower() for skill in profile["skills"]}


def description_for_role(role: str) -> str:
    """Return compact role description text for matching."""

    profile = ROLE_PROFILES.get(canonical_role(role))
    return str(profile.get("description", role)) if profile else role
