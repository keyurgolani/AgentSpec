"""
Context Detection System

This module provides the ContextDetector class for analyzing projects and detecting
technology stacks, frameworks, and project characteristics to suggest relevant
instructions and templates.
"""

import json
import logging
import os
import re
import subprocess  # nosec B404 # Used safely for git commands
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ProjectType(Enum):
    """Enumeration of supported project types"""

    WEB_FRONTEND = "web_frontend"
    WEB_BACKEND = "web_backend"
    FULLSTACK_WEB = "fullstack_web"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    MICROSERVICE = "microservice"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"
    GAME = "game"
    UNKNOWN = "unknown"


class Language(Enum):
    """Enumeration of programming languages"""

    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    PYTHON = "python"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    DART = "dart"
    HTML = "html"
    CSS = "css"
    UNKNOWN = "unknown"


@dataclass
class Dependency:
    """Represents a project dependency"""

    name: str
    version: Optional[str] = None
    type: str = "runtime"  # runtime, dev, peer, optional
    source: str = ""  # package.json, requirements.txt, etc.


@dataclass
class Framework:
    """Represents a detected framework"""

    name: str
    version: Optional[str] = None
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)


@dataclass
class TechnologyStack:
    """Represents the detected technology stack"""

    languages: List[Language] = field(default_factory=list)
    frameworks: List[Framework] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)


@dataclass
class FileStructure:
    """Represents project file structure analysis"""

    total_files: int = 0
    directories: List[str] = field(default_factory=list)
    file_types: Dict[str, int] = field(default_factory=dict)
    config_files: List[str] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    documentation_files: List[str] = field(default_factory=list)


@dataclass
class GitInfo:
    """Represents Git repository information"""

    is_git_repo: bool = False
    branch: Optional[str] = None
    remote_url: Optional[str] = None
    commit_count: int = 0
    contributors: int = 0
    last_commit_date: Optional[str] = None


@dataclass
class ProjectContext:
    """Comprehensive project context information"""

    project_path: str
    project_type: ProjectType
    technology_stack: TechnologyStack
    dependencies: List[Dependency] = field(default_factory=list)
    file_structure: FileStructure = field(default_factory=FileStructure)
    git_info: Optional[GitInfo] = None
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstructionSuggestion:
    """Represents a suggested instruction with confidence scoring"""

    instruction_id: str
    tags: List[str]
    confidence: float
    reasons: List[str] = field(default_factory=list)
    category: str = ""


class ContextDetector:
    """
    Detects project context and suggests relevant instructions based on
    technology stack, project structure, and other characteristics.
    """

    def __init__(self) -> None:
        """Initialize the context detector"""
        self._language_extensions = {
            Language.JAVASCRIPT: [".js", ".mjs", ".jsx", ".cjs"],
            Language.TYPESCRIPT: [".ts", ".tsx", ".d.ts"],
            Language.PYTHON: [".py", ".pyw", ".pyi", ".py3"],
            Language.JAVA: [".java", ".class", ".jar"],
            Language.CSHARP: [".cs", ".csx", ".vb"],
            Language.CPP: [
                ".cpp",
                ".cxx",
                ".cc",
                ".c++",
                ".hpp",
                ".hxx",
                ".h++",
            ],
            Language.C: [".c", ".h"],
            Language.GO: [".go", ".mod", ".sum"],
            Language.RUST: [".rs", ".toml"],
            Language.PHP: [".php", ".phtml", ".php3", ".php4", ".php5"],
            Language.RUBY: [".rb", ".rbw", ".rake", ".gemspec"],
            Language.SWIFT: [".swift"],
            Language.KOTLIN: [".kt", ".kts"],
            Language.DART: [".dart"],
            Language.HTML: [".html", ".htm", ".xhtml"],
            Language.CSS: [".css", ".scss", ".sass", ".less", ".styl"],
        }

        # Content patterns for language detection when extensions are ambiguous
        self._language_content_patterns = {
            Language.JAVASCRIPT: [
                r"console\.log",
                r"function\s+\w+",
                r"var\s+\w+",
                r"let\s+\w+",
                r"const\s+\w+",
            ],
            Language.TYPESCRIPT: [
                r"interface\s+\w+",
                r"type\s+\w+\s*=",
                r":\s*string",
                r":\s*number",
                r"export\s+type",
            ],
            Language.PYTHON: [
                r"def\s+\w+",
                r"import\s+\w+",
                r"from\s+\w+\s+import",
                r'if\s+__name__\s*==\s*[\'"]__main__[\'"]',
            ],
            Language.JAVA: [
                r"public\s+class",
                r"public\s+static\s+void\s+main",
                r"import\s+java\.",
            ],
            Language.CSHARP: [
                r"using\s+System",
                r"namespace\s+\w+",
                r"public\s+class",
                r"\[.*\]",
            ],
            Language.GO: [
                r"package\s+\w+",
                r"func\s+\w+",
                r'import\s+[\'"]',
                r"go\s+\w+",
            ],
            Language.RUST: [
                r"fn\s+\w+",
                r"use\s+\w+",
                r"struct\s+\w+",
                r"impl\s+\w+",
            ],
            Language.PHP: [r"<\?php", r"function\s+\w+", r"\$\w+", r"echo\s+"],
            Language.RUBY: [
                r"def\s+\w+",
                r"class\s+\w+",
                r'require\s+[\'"]',
                r"puts\s+",
            ],
        }

        self._framework_indicators = {
            "react": {
                "files": ["package.json"],
                "dependencies": ["react", "react-dom", "react-scripts"],
                "files_patterns": [r".*\.jsx?$", r".*\.tsx?$"],
                "content_patterns": [
                    r"import.*react",
                    r'from [\'"]react[\'"]',
                    r"React\.",
                    r"useState",
                    r"useEffect",
                ],
            },
            "vue": {
                "files": ["package.json", "vue.config.js"],
                "dependencies": ["vue", "@vue/cli"],
                "files_patterns": [r".*\.vue$"],
                "content_patterns": [
                    r"<template>",
                    r"Vue\.",
                    r"createApp",
                    r"defineComponent",
                ],
            },
            "angular": {
                "files": ["package.json", "angular.json", "tsconfig.json"],
                "dependencies": ["@angular/core", "@angular/cli"],
                "files_patterns": [
                    r".*\.component\.ts$",
                    r".*\.service\.ts$",
                    r".*\.module\.ts$",
                ],
                "content_patterns": [
                    r"@Component",
                    r"@Injectable",
                    r"@NgModule",
                    r"import.*@angular",
                ],
            },
            "svelte": {
                "files": ["package.json", "svelte.config.js"],
                "dependencies": ["svelte", "@sveltejs/kit"],
                "files_patterns": [r".*\.svelte$"],
                "content_patterns": [r"<script>", r"export let", r"\$:"],
            },
            "django": {
                "files": [
                    "requirements.txt",
                    "setup.py",
                    "manage.py",
                    "pyproject.toml",
                ],
                "dependencies": ["django", "Django"],
                "files_patterns": [
                    r".*settings\.py$",
                    r".*urls\.py$",
                    r".*models\.py$",
                    r".*views\.py$",
                ],
                "content_patterns": [
                    r"from django",
                    r"DJANGO_SETTINGS_MODULE",
                    r"django\.",
                    r"models\.Model",
                ],
            },
            "flask": {
                "files": [
                    "requirements.txt",
                    "setup.py",
                    "app.py",
                    "pyproject.toml",
                ],
                "dependencies": ["flask", "Flask"],
                "content_patterns": [
                    r"from flask",
                    r"Flask\(__name__\)",
                    r"@app\.route",
                    r"flask\.",
                ],
            },
            "fastapi": {
                "files": [
                    "requirements.txt",
                    "setup.py",
                    "main.py",
                    "pyproject.toml",
                ],
                "dependencies": ["fastapi", "uvicorn"],
                "content_patterns": [
                    r"from fastapi",
                    r"FastAPI\(",
                    r"@app\.get",
                    r"@app\.post",
                ],
            },
            "express": {
                "files": ["package.json", "server.js", "app.js"],
                "dependencies": ["express"],
                "content_patterns": [
                    r'require\([\'"]express[\'"]',
                    r'from [\'"]express[\'"]',
                    r"express\(\)",
                    r"app\.get",
                    r"app\.post",
                ],
            },
            "nestjs": {
                "files": ["package.json", "nest-cli.json"],
                "dependencies": ["@nestjs/core", "@nestjs/common"],
                "files_patterns": [
                    r".*\.controller\.ts$",
                    r".*\.service\.ts$",
                    r".*\.module\.ts$",
                ],
                "content_patterns": [
                    r"@Controller",
                    r"@Injectable",
                    r"@Module",
                    r'from [\'"]@nestjs',
                ],
            },
            "nextjs": {
                "files": ["package.json", "next.config.js", "next.config.mjs"],
                "dependencies": ["next", "react"],
                "files_patterns": [
                    r"pages/.*\.js$",
                    r"pages/.*\.tsx?$",
                    r"app/.*\.tsx?$",
                ],
                "content_patterns": [
                    r'from [\'"]next/',
                    r"import.*next/",
                    r"getStaticProps",
                    r"getServerSideProps",
                ],
            },
            "nuxt": {
                "files": ["package.json", "nuxt.config.js", "nuxt.config.ts"],
                "dependencies": ["nuxt", "@nuxt/"],
                "content_patterns": [
                    r'from [\'"]nuxt',
                    r"export.*nuxtConfig",
                    r"defineNuxtConfig",
                ],
            },
            "gatsby": {
                "files": ["package.json", "gatsby-config.js"],
                "dependencies": ["gatsby"],
                "content_patterns": [r"gatsby-", r"graphql`", r"StaticQuery"],
            },
            "spring": {
                "files": ["pom.xml", "build.gradle", "application.properties"],
                "dependencies": ["spring-boot", "spring-core"],
                "files_patterns": [
                    r".*Application\.java$",
                    r".*Controller\.java$",
                ],
                "content_patterns": [
                    r"@SpringBootApplication",
                    r"@RestController",
                    r"@Service",
                    r"import.*springframework",
                ],
            },
            "laravel": {
                "files": ["composer.json", "artisan"],
                "dependencies": ["laravel/framework"],
                "files_patterns": [r"app/.*\.php$", r"routes/.*\.php$"],
                "content_patterns": [
                    r"use Illuminate",
                    r"Artisan::",
                    r"Route::",
                ],
            },
            "rails": {
                "files": ["Gemfile", "config/application.rb"],
                "dependencies": ["rails"],
                "files_patterns": [r"app/.*\.rb$", r"config/.*\.rb$"],
                "content_patterns": [
                    r"Rails\.",
                    r"ActiveRecord::",
                    r"class.*Controller",
                ],
            },
            "dotnet": {
                "files": ["*.csproj", "*.sln", "Program.cs"],
                "dependencies": ["Microsoft.AspNetCore"],
                "files_patterns": [r".*\.cs$"],
                "content_patterns": [
                    r"using Microsoft",
                    r"namespace",
                    r"\[ApiController\]",
                ],
            },
        }

        self._project_type_indicators = {
            ProjectType.WEB_FRONTEND: {
                "frameworks": ["react", "vue", "angular"],
                "files": ["index.html", "public/index.html", "src/index.html"],
                "dependencies": ["webpack", "vite", "parcel", "rollup"],
            },
            ProjectType.WEB_BACKEND: {
                "frameworks": ["django", "flask", "express", "fastapi"],
                "files": ["server.js", "app.py", "main.py", "manage.py"],
                "dependencies": ["express", "django", "flask", "fastapi"],
            },
            ProjectType.FULLSTACK_WEB: {
                "frameworks": ["nextjs", "nuxt"],
                "files": ["next.config.js", "nuxt.config.js"],
                "dependencies": ["next", "nuxt"],
            },
            ProjectType.MOBILE_APP: {
                "files": ["android/", "ios/", "App.js", "App.tsx"],
                "dependencies": ["react-native", "flutter", "ionic"],
            },
            ProjectType.CLI_TOOL: {
                "files": ["bin/", "cli.py", "main.py", "index.js"],
                "dependencies": ["click", "argparse", "commander", "yargs"],
            },
            ProjectType.LIBRARY: {
                "files": [
                    "setup.py",
                    "pyproject.toml",
                    "package.json",
                    "lib/",
                ],
                "dependencies": ["setuptools", "poetry"],
            },
        }

    def analyze_project(self, project_path: str) -> ProjectContext:
        """
        Perform comprehensive project analysis.

        Args:
            project_path: Path to the project directory

        Returns:
            ProjectContext with analysis results
        """
        project_dir = Path(project_path).resolve()

        if not project_dir.exists() or not project_dir.is_dir():
            raise ValueError(f"Invalid project path: {project_dir}")

        logger.info(f"Analyzing project at: {project_dir}")

        # Initialize context
        context = ProjectContext(
            project_path=str(project_dir),
            project_type=ProjectType.UNKNOWN,
            technology_stack=TechnologyStack(),
        )

        # Analyze file structure
        context.file_structure = self._analyze_file_structure(project_dir)

        # Detect technology stack
        context.technology_stack = self.detect_technology_stack(str(project_dir))

        # Detect dependencies
        context.dependencies = self._detect_dependencies(project_dir)

        # Detect project type
        context.project_type = self._detect_project_type(context)

        # Analyze Git repository
        context.git_info = self._analyze_git_repository(project_dir)

        # Calculate confidence score
        context.confidence_score = self._calculate_context_confidence(context)

        # Add metadata
        context.metadata = self._collect_metadata(project_dir, context)

        logger.info(
            f"Project analysis complete. Type: {context.project_type.value}, "
            f"Confidence: {context.confidence_score:.2f}"
        )

        return context

    def detect_technology_stack(self, project_path: str) -> TechnologyStack:
        """
        Detect technology stack from project files.

        Args:
            project_path: Path to the project directory

        Returns:
            TechnologyStack with detected technologies
        """
        project_dir = Path(project_path)
        stack = TechnologyStack()

        # Detect languages
        stack.languages = self._detect_languages(project_dir)

        # Detect frameworks
        stack.frameworks = self._detect_frameworks(project_dir)

        # Detect databases
        stack.databases = self._detect_databases(project_dir)

        # Detect tools
        stack.tools = self._detect_tools(project_dir)

        # Detect platforms
        stack.platforms = self._detect_platforms(project_dir)

        return stack

    def suggest_instructions(
        self, context: ProjectContext
    ) -> List[InstructionSuggestion]:
        """
        Suggest relevant instructions based on project context.

        Args:
            context: Project context information

        Returns:
            List of instruction suggestions with confidence scores
        """
        suggestions = []

        # Base suggestions for all projects
        suggestions.extend(self._get_base_suggestions())

        # Language-specific suggestions
        for language in context.technology_stack.languages:
            suggestions.extend(self._get_language_suggestions(language))

        # Framework-specific suggestions
        for framework in context.technology_stack.frameworks:
            suggestions.extend(self._get_framework_suggestions(framework))

        # Project type suggestions
        suggestions.extend(self._get_project_type_suggestions(context.project_type))

        # Dependency-based suggestions
        suggestions.extend(self._get_dependency_suggestions(context.dependencies))

        # File structure suggestions
        suggestions.extend(self._get_structure_suggestions(context.file_structure))

        # Calculate final confidence scores
        for suggestion in suggestions:
            suggestion.confidence = self.calculate_confidence(suggestion, context)

        # Sort by confidence and remove duplicates
        unique_suggestions: dict[str, InstructionSuggestion] = {}
        for suggestion in suggestions:
            key = suggestion.instruction_id
            if (
                key not in unique_suggestions
                or suggestion.confidence > unique_suggestions[key].confidence
            ):
                unique_suggestions[key] = suggestion

        final_suggestions = list(unique_suggestions.values())
        final_suggestions.sort(key=lambda s: s.confidence, reverse=True)

        return final_suggestions

    def calculate_confidence(
        self, suggestion: InstructionSuggestion, context: ProjectContext
    ) -> float:
        """
        Calculate confidence score for an instruction suggestion.

        Args:
            suggestion: Instruction suggestion
            context: Project context

        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = suggestion.confidence

        # Boost confidence based on multiple evidence sources
        evidence_boost = min(len(suggestion.reasons) * 0.1, 0.3)

        # Boost confidence for popular frameworks/languages
        popularity_boost = 0.0
        for framework in context.technology_stack.frameworks:
            if framework.name in [
                "react",
                "vue",
                "angular",
                "django",
                "flask",
            ]:
                popularity_boost += 0.1

        # Boost confidence based on project maturity (file count, git history)
        maturity_boost = 0.0
        if context.file_structure.total_files > 50:
            maturity_boost += 0.1
        if context.git_info and context.git_info.commit_count > 10:
            maturity_boost += 0.1

        # Calculate final confidence
        final_confidence = min(
            base_confidence + evidence_boost + popularity_boost + maturity_boost,
            1.0,
        )

        return final_confidence

    def _analyze_file_structure(self, project_path: Path) -> FileStructure:
        """Analyze project file structure"""
        structure = FileStructure()

        try:
            # Walk through all files
            for root, dirs, files in os.walk(project_path):
                # Skip hidden directories and common ignore patterns
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["node_modules", "__pycache__", "venv", "env"]
                ]

                rel_root = os.path.relpath(root, project_path)
                if rel_root != ".":
                    structure.directories.append(rel_root)

                for file in files:
                    if file.startswith("."):
                        continue

                    structure.total_files += 1
                    file_path = os.path.join(root, file)
                    rel_file_path = os.path.relpath(file_path, project_path)

                    # Categorize files
                    ext = Path(file).suffix.lower()
                    structure.file_types[ext] = structure.file_types.get(ext, 0) + 1

                    # Identify special file types
                    if self._is_config_file(file):
                        structure.config_files.append(rel_file_path)
                    elif self._is_source_file(file):
                        structure.source_files.append(rel_file_path)
                    elif self._is_test_file(file):
                        structure.test_files.append(rel_file_path)
                    elif self._is_documentation_file(file):
                        structure.documentation_files.append(rel_file_path)

        except Exception as e:
            logger.error(f"Error analyzing file structure: {e}")

        return structure

    def _detect_languages(self, project_path: Path) -> List[Language]:
        """Detect programming languages from file extensions and content analysis"""
        languages = set()
        language_file_counts: dict[str, int] = {}

        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d
                not in [
                    "node_modules",
                    "__pycache__",
                    "venv",
                    "env",
                    "build",
                    "dist",
                ]
            ]

            for file in files:
                if file.startswith("."):
                    continue

                file_path = Path(root) / file
                ext = file_path.suffix.lower()

                # Detect by file extension
                detected_by_extension = []
                for language, extensions in self._language_extensions.items():
                    if ext in extensions:
                        detected_by_extension.append(language)
                        language_file_counts[language.value] = (
                            language_file_counts.get(language.value, 0) + 1
                        )

                # For ambiguous cases or extensionless files, use content analysis
                if not detected_by_extension or len(detected_by_extension) > 1:
                    content_language = self._detect_language_from_content(file_path)
                    if content_language:
                        detected_by_extension = [content_language]
                        language_file_counts[content_language.value] = (
                            language_file_counts.get(content_language.value, 0) + 1
                        )

                languages.update(detected_by_extension)

        # Filter out languages with very few files (likely false positives)
        filtered_languages = []
        total_files = sum(language_file_counts.values())

        for language in languages:
            file_count = language_file_counts.get(language.value, 0)
            # Include language if it has at least 2 files or represents >5% of total files
            if file_count >= 2 or (total_files > 0 and file_count / total_files > 0.05):
                filtered_languages.append(language)

        return filtered_languages

    def _detect_language_from_content(self, file_path: Path) -> Optional[Language]:
        """Detect language from file content using pattern matching"""
        try:
            # Only analyze reasonably sized text files
            if file_path.stat().st_size > 1024 * 1024:  # Skip files larger than 1MB
                return None

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(4096)  # Read first 4KB for analysis

            # Score each language based on pattern matches
            language_scores = {}

            for language, patterns in self._language_content_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, content, re.IGNORECASE))
                    score += matches

                if score > 0:
                    language_scores[language] = score

            # Return the language with the highest score
            if language_scores:
                return max(language_scores.items(), key=lambda x: x[1])[0]

        except Exception:
            pass  # nosec B110 # Intentionally ignore parsing errors

        return None

    def _detect_frameworks(self, project_path: Path) -> List[Framework]:
        """Detect frameworks from various indicators"""
        frameworks = []

        for framework_name, indicators in self._framework_indicators.items():
            confidence = 0.0
            evidence = []

            # Check for required files
            if "files" in indicators:
                for file_name in indicators["files"]:
                    if (project_path / file_name).exists():
                        confidence += 0.3
                        evidence.append(f"Found {file_name}")

            # Check dependencies
            if "dependencies" in indicators:
                deps = self._get_package_dependencies(project_path)
                for dep in indicators["dependencies"]:
                    if any(dep in d.name for d in deps):
                        confidence += 0.4
                        evidence.append(f"Found dependency: {dep}")

            # Check file patterns
            if "files_patterns" in indicators:
                for pattern in indicators["files_patterns"]:
                    if self._find_files_matching_pattern(project_path, pattern):
                        confidence += 0.2
                        evidence.append(f"Found files matching: {pattern}")

            # Check content patterns
            if "content_patterns" in indicators:
                for pattern in indicators["content_patterns"]:
                    if self._find_content_matching_pattern(project_path, pattern):
                        confidence += 0.3
                        evidence.append(f"Found content matching: {pattern}")

            if confidence > 0.3:  # Minimum threshold
                frameworks.append(
                    Framework(
                        name=framework_name,
                        confidence=min(confidence, 1.0),
                        evidence=evidence,
                    )
                )

        return frameworks

    def _detect_databases(self, project_path: Path) -> List[str]:
        """Detect database usage from dependencies and config files"""
        databases = set()

        # Check dependencies
        deps = self._get_package_dependencies(project_path)
        db_indicators = {
            "postgresql": ["psycopg2", "pg", "postgres"],
            "mysql": ["mysql", "pymysql", "mysql2"],
            "sqlite": ["sqlite3", "sqlite"],
            "mongodb": ["pymongo", "mongoose", "mongodb"],
            "redis": ["redis", "redis-py"],
            "elasticsearch": ["elasticsearch", "elastic"],
        }

        for db_name, indicators in db_indicators.items():
            for indicator in indicators:
                if any(indicator in dep.name.lower() for dep in deps):
                    databases.add(db_name)

        # Check config files for database URLs
        config_patterns = {
            "postgresql": [r"postgres://", r"postgresql://"],
            "mysql": [r"mysql://", r"mysql2://"],
            "mongodb": [r"mongodb://", r"mongo://"],
            "redis": [r"redis://"],
        }

        for db_name, patterns in config_patterns.items():
            for pattern in patterns:
                if self._find_content_matching_pattern(project_path, pattern):
                    databases.add(db_name)

        return list(databases)

    def _detect_tools(self, project_path: Path) -> List[str]:
        """Detect development tools and build systems"""
        tools = set()

        # Check for tool-specific files
        tool_files = {
            "webpack": ["webpack.config.js", "webpack.config.ts"],
            "vite": ["vite.config.js", "vite.config.ts"],
            "rollup": ["rollup.config.js"],
            "parcel": [".parcelrc"],
            "docker": ["Dockerfile", "docker-compose.yml"],
            "kubernetes": ["k8s/", "kubernetes/"],
            "terraform": ["*.t"],
            "ansible": ["playbook.yml", "ansible.cfg"],
            "makefile": ["Makefile", "makefile"],
            "cmake": ["CMakeLists.txt"],
            "gradle": ["build.gradle", "gradlew"],
            "maven": ["pom.xml"],
        }

        for tool, files in tool_files.items():
            for file_pattern in files:
                if "*" in file_pattern:
                    if self._find_files_matching_pattern(project_path, file_pattern):
                        tools.add(tool)
                else:
                    if (project_path / file_pattern).exists():
                        tools.add(tool)

        return list(tools)

    def _detect_platforms(self, project_path: Path) -> List[str]:
        """Detect target platforms"""
        platforms = set()

        # Check for platform-specific indicators
        platform_indicators = {
            "web": ["index.html", "public/", "static/", "assets/"],
            "mobile": ["android/", "ios/", "App.js", "App.tsx"],
            "desktop": ["electron", "tauri", ".desktop"],
            "server": ["server.js", "app.py", "main.py"],
            "cloud": ["serverless.yml", "sam.yml", "cloudformation/"],
        }

        for platform, indicators in platform_indicators.items():
            for indicator in indicators:
                if (project_path / indicator).exists():
                    platforms.add(platform)

        return list(platforms)

    def _detect_dependencies(self, project_path: Path) -> List[Dependency]:
        """Detect project dependencies from various package files"""
        dependencies = []

        # Node.js dependencies
        package_json = project_path / "package.json"
        if package_json.exists():
            dependencies.extend(self._parse_package_json(package_json))

        # Yarn dependencies
        yarn_lock = project_path / "yarn.lock"
        if yarn_lock.exists():
            dependencies.extend(self._parse_yarn_lock(yarn_lock))

        # Python dependencies
        requirements_txt = project_path / "requirements.txt"
        if requirements_txt.exists():
            dependencies.extend(self._parse_requirements_txt(requirements_txt))

        pyproject_toml = project_path / "pyproject.toml"
        if pyproject_toml.exists():
            dependencies.extend(self._parse_pyproject_toml(pyproject_toml))

        setup_py = project_path / "setup.py"
        if setup_py.exists():
            dependencies.extend(self._parse_setup_py(setup_py))

        pipfile = project_path / "Pipfile"
        if pipfile.exists():
            dependencies.extend(self._parse_pipfile(pipfile))

        # Ruby dependencies
        gemfile = project_path / "Gemfile"
        if gemfile.exists():
            dependencies.extend(self._parse_gemfile(gemfile))

        # Java dependencies
        pom_xml = project_path / "pom.xml"
        if pom_xml.exists():
            dependencies.extend(self._parse_pom_xml(pom_xml))

        build_gradle = project_path / "build.gradle"
        if build_gradle.exists():
            dependencies.extend(self._parse_build_gradle(build_gradle))

        # Go dependencies
        go_mod = project_path / "go.mod"
        if go_mod.exists():
            dependencies.extend(self._parse_go_mod(go_mod))

        # Rust dependencies
        cargo_toml = project_path / "Cargo.toml"
        if cargo_toml.exists():
            dependencies.extend(self._parse_cargo_toml(cargo_toml))

        # PHP dependencies
        composer_json = project_path / "composer.json"
        if composer_json.exists():
            dependencies.extend(self._parse_composer_json(composer_json))

        # .NET dependencies
        for csproj_file in project_path.glob("*.csproj"):
            dependencies.extend(self._parse_csproj(csproj_file))

        return dependencies

    def _detect_project_type(self, context: ProjectContext) -> ProjectType:
        """Detect project type based on context"""
        scores = {project_type: 0.0 for project_type in ProjectType}

        # Score based on frameworks
        framework_names = [f.name for f in context.technology_stack.frameworks]
        for project_type, indicators in self._project_type_indicators.items():
            if "frameworks" in indicators:
                for framework in indicators["frameworks"]:
                    if framework in framework_names:
                        scores[project_type] += 0.4

        # Score based on files
        for project_type, indicators in self._project_type_indicators.items():
            if "files" in indicators:
                for file_pattern in indicators["files"]:
                    if any(
                        file_pattern in f
                        for f in context.file_structure.config_files
                        + context.file_structure.source_files
                    ):
                        scores[project_type] += 0.2

        # Score based on dependencies
        dep_names = [d.name for d in context.dependencies]
        for project_type, indicators in self._project_type_indicators.items():
            if "dependencies" in indicators:
                for dep in indicators["dependencies"]:
                    if any(dep in name for name in dep_names):
                        scores[project_type] += 0.3

        # Return the highest scoring type
        best_type = max(scores.items(), key=lambda x: x[1])
        return best_type[0] if best_type[1] > 0.3 else ProjectType.UNKNOWN

    def _analyze_git_repository(self, project_path: Path) -> Optional[GitInfo]:
        """Analyze Git repository information"""
        git_dir = project_path / ".git"
        if not git_dir.exists():
            return None

        git_info = GitInfo(is_git_repo=True)

        try:
            # Get current branch
            result = subprocess.run(  # nosec B603 B607 # Safe git command
                ["git", "branch", "--show-current"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                git_info.branch = result.stdout.strip()

            # Get remote URL
            result = subprocess.run(  # nosec B603 B607 # Safe git command
                ["git", "remote", "get-url", "origin"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                git_info.remote_url = result.stdout.strip()

            # Get commit count
            result = subprocess.run(  # nosec B603 B607 # Safe git command
                ["git", "rev-list", "--count", "HEAD"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                git_info.commit_count = int(result.stdout.strip())

            # Get contributor count
            result = subprocess.run(  # nosec B603 B607 # Safe git command
                ["git", "shortlog", "-sn"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                git_info.contributors = len(result.stdout.strip().split("\n"))

            # Get last commit date
            result = subprocess.run(  # nosec B603 B607 # Safe git command
                ["git", "log", "-1", "--format=%ci"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                git_info.last_commit_date = result.stdout.strip()

        except Exception as e:
            logger.warning(f"Error analyzing Git repository: {e}")

        return git_info

    def _calculate_context_confidence(self, context: ProjectContext) -> float:
        """Calculate overall confidence score for the context"""
        confidence = 0.0

        # Base confidence from detected languages
        if context.technology_stack.languages:
            confidence += 0.2

        # Confidence from frameworks
        if context.technology_stack.frameworks:
            avg_framework_confidence = sum(
                f.confidence for f in context.technology_stack.frameworks
            ) / len(context.technology_stack.frameworks)
            confidence += avg_framework_confidence * 0.4

        # Confidence from project type detection
        if context.project_type != ProjectType.UNKNOWN:
            confidence += 0.2

        # Confidence from file structure
        if context.file_structure.total_files > 5:
            confidence += 0.1

        # Confidence from dependencies
        if context.dependencies:
            confidence += 0.1

        return min(confidence, 1.0)

    def _collect_metadata(
        self, project_path: Path, context: ProjectContext
    ) -> Dict[str, Any]:
        """Collect additional project metadata"""
        metadata: Dict[str, Any] = {}

        # Project size metrics
        metadata["project_size"] = {
            "total_files": context.file_structure.total_files,
            "source_files": len(context.file_structure.source_files),
            "test_files": len(context.file_structure.test_files),
            "config_files": len(context.file_structure.config_files),
        }

        # Language distribution
        if context.file_structure.file_types:
            metadata["file_type_distribution"] = context.file_structure.file_types

        # Framework versions
        if context.technology_stack.frameworks:
            metadata["framework_versions"] = {
                f.name: f.version
                for f in context.technology_stack.frameworks
                if f.version
            }

        # Architectural patterns
        metadata["architectural_patterns"] = self._detect_architectural_patterns(
            project_path, context
        )

        # Project complexity assessment
        metadata["complexity_assessment"] = self._assess_project_complexity(context)

        # Dependency analysis
        metadata["dependency_analysis"] = self._analyze_dependencies(
            context.dependencies
        )

        # Code quality indicators
        metadata["quality_indicators"] = self._analyze_code_quality_indicators(
            project_path, context
        )

        return metadata

    def _detect_architectural_patterns(
        self, project_path: Path, context: ProjectContext
    ) -> Dict[str, Any]:
        """Detect architectural patterns from project structure"""
        detected_patterns: List[str] = []
        confidence_scores: Dict[str, float] = {}
        evidence: Dict[str, List[str]] = {}

        patterns: Dict[str, Any] = {
            "detected_patterns": detected_patterns,
            "confidence_scores": confidence_scores,
            "evidence": evidence,
        }

        directories = set(context.file_structure.directories)
        source_files = context.file_structure.source_files

        # MVC Pattern Detection
        mvc_indicators = [
            "models",
            "views",
            "controllers",
            "model",
            "view",
            "controller",
        ]
        mvc_score = sum(
            1
            for indicator in mvc_indicators
            if any(indicator in d.lower() for d in directories)
        )
        if mvc_score >= 2:
            detected_patterns.append("MVC")
            confidence_scores["MVC"] = min(mvc_score / 3, 1.0)
            evidence["MVC"] = [
                d
                for d in directories
                if any(ind in d.lower() for ind in mvc_indicators)
            ]

        # Microservices Pattern Detection
        microservice_indicators = [
            "services",
            "service",
            "api",
            "gateway",
            "auth",
            "user",
            "payment",
        ]
        microservice_score = sum(
            1
            for indicator in microservice_indicators
            if any(indicator in d.lower() for d in directories)
        )
        if microservice_score >= 3 or any(
            "docker" in f.lower() for f in context.file_structure.config_files
        ):
            detected_patterns.append("Microservices")
            confidence_scores["Microservices"] = min(microservice_score / 5, 1.0)
            evidence["Microservices"] = [
                d
                for d in directories
                if any(ind in d.lower() for ind in microservice_indicators)
            ]

        # Layered Architecture Detection
        layer_indicators = [
            "presentation",
            "business",
            "data",
            "domain",
            "infrastructure",
            "application",
        ]
        layer_score = sum(
            1
            for indicator in layer_indicators
            if any(indicator in d.lower() for d in directories)
        )
        if layer_score >= 2:
            detected_patterns.append("Layered")
            confidence_scores["Layered"] = min(layer_score / 4, 1.0)
            evidence["Layered"] = [
                d
                for d in directories
                if any(ind in d.lower() for ind in layer_indicators)
            ]

        # Component-Based Architecture (React/Vue/Angular)
        component_indicators = [
            "components",
            "component",
            "widgets",
            "pages",
            "screens",
        ]
        component_files = [
            f
            for f in source_files
            if any(ind in f.lower() for ind in component_indicators)
        ]
        if len(component_files) > 5 or any(
            f.name in ["react", "vue", "angular"]
            for f in context.technology_stack.frameworks
        ):
            detected_patterns.append("Component-Based")
            confidence_scores["Component-Based"] = min(len(component_files) / 10, 1.0)
            evidence["Component-Based"] = component_files[:10]  # Limit evidence

        # Hexagonal/Clean Architecture Detection
        clean_indicators = [
            "adapters",
            "ports",
            "domain",
            "infrastructure",
            "usecases",
            "entities",
        ]
        clean_score = sum(
            1
            for indicator in clean_indicators
            if any(indicator in d.lower() for d in directories)
        )
        if clean_score >= 3:
            detected_patterns.append("Hexagonal/Clean")
            confidence_scores["Hexagonal/Clean"] = min(clean_score / 5, 1.0)
            evidence["Hexagonal/Clean"] = [
                d
                for d in directories
                if any(ind in d.lower() for ind in clean_indicators)
            ]

        # Monolithic Detection
        if len(directories) < 5 and context.file_structure.total_files > 20:
            detected_patterns.append("Monolithic")
            confidence_scores["Monolithic"] = 0.7
            evidence["Monolithic"] = [
                "Few directories with many files suggests monolithic structure"
            ]

        return patterns

    def _assess_project_complexity(self, context: ProjectContext) -> Dict[str, Any]:
        """Assess project complexity based on various metrics"""
        complexity: Dict[str, Any] = {
            "overall_score": 0,
            "factors": {},
            "recommendations": [],
        }

        # File count complexity
        file_count = context.file_structure.total_files
        if file_count < 10:
            complexity["factors"]["file_count"] = {
                "score": 1,
                "level": "Simple",
            }
        elif file_count < 50:
            complexity["factors"]["file_count"] = {
                "score": 2,
                "level": "Small",
            }
        elif file_count < 200:
            complexity["factors"]["file_count"] = {
                "score": 3,
                "level": "Medium",
            }
        elif file_count < 500:
            complexity["factors"]["file_count"] = {
                "score": 4,
                "level": "Large",
            }
        else:
            complexity["factors"]["file_count"] = {
                "score": 5,
                "level": "Very Large",
            }

        # Language diversity complexity
        lang_count = len(context.technology_stack.languages)
        if lang_count <= 1:
            complexity["factors"]["language_diversity"] = {
                "score": 1,
                "level": "Single Language",
            }
        elif lang_count <= 3:
            complexity["factors"]["language_diversity"] = {
                "score": 2,
                "level": "Multi-Language",
            }
        else:
            complexity["factors"]["language_diversity"] = {
                "score": 3,
                "level": "Polyglot",
            }

        # Framework complexity
        framework_count = len(context.technology_stack.frameworks)
        if framework_count == 0:
            complexity["factors"]["framework_complexity"] = {
                "score": 1,
                "level": "No Frameworks",
            }
        elif framework_count <= 2:
            complexity["factors"]["framework_complexity"] = {
                "score": 2,
                "level": "Simple Stack",
            }
        elif framework_count <= 4:
            complexity["factors"]["framework_complexity"] = {
                "score": 3,
                "level": "Complex Stack",
            }
        else:
            complexity["factors"]["framework_complexity"] = {
                "score": 4,
                "level": "Very Complex Stack",
            }

        # Dependency complexity
        dep_count = len(context.dependencies)
        if dep_count < 5:
            complexity["factors"]["dependency_complexity"] = {
                "score": 1,
                "level": "Few Dependencies",
            }
        elif dep_count < 20:
            complexity["factors"]["dependency_complexity"] = {
                "score": 2,
                "level": "Moderate Dependencies",
            }
        elif dep_count < 50:
            complexity["factors"]["dependency_complexity"] = {
                "score": 3,
                "level": "Many Dependencies",
            }
        else:
            complexity["factors"]["dependency_complexity"] = {
                "score": 4,
                "level": "Dependency Heavy",
            }

        # Directory structure complexity
        dir_count = len(context.file_structure.directories)
        if dir_count < 5:
            complexity["factors"]["structure_complexity"] = {
                "score": 1,
                "level": "Flat Structure",
            }
        elif dir_count < 15:
            complexity["factors"]["structure_complexity"] = {
                "score": 2,
                "level": "Organized Structure",
            }
        elif dir_count < 30:
            complexity["factors"]["structure_complexity"] = {
                "score": 3,
                "level": "Complex Structure",
            }
        else:
            complexity["factors"]["structure_complexity"] = {
                "score": 4,
                "level": "Very Complex Structure",
            }

        # Calculate overall score
        total_score = sum(factor["score"] for factor in complexity["factors"].values())
        max_score = len(complexity["factors"]) * 5
        complexity["overall_score"] = total_score / max_score

        # Generate recommendations based on complexity
        if complexity["overall_score"] > 0.7:
            complexity["recommendations"].extend(
                [
                    "Consider breaking down into smaller modules",
                    "Implement comprehensive documentation",
                    "Set up automated testing and CI/CD",
                    "Consider architectural refactoring",
                ]
            )
        elif complexity["overall_score"] > 0.5:
            complexity["recommendations"].extend(
                [
                    "Maintain good documentation",
                    "Implement testing strategy",
                    "Monitor technical debt",
                ]
            )
        else:
            complexity["recommendations"].extend(
                [
                    "Good foundation for growth",
                    "Consider adding tests as project grows",
                ]
            )

        return complexity

    def _analyze_dependencies(self, dependencies: List[Dependency]) -> Dict[str, Any]:
        """Analyze project dependencies for insights"""
        analysis: Dict[str, Any] = {
            "total_count": len(dependencies),
            "by_type": {},
            "by_source": {},
            "security_concerns": [],
            "outdated_patterns": [],
            "recommendations": [],
        }

        # Group by type
        for dep in dependencies:
            dep_type = dep.type
            if dep_type not in analysis["by_type"]:
                analysis["by_type"][dep_type] = []
            analysis["by_type"][dep_type].append(dep.name)

        # Group by source
        for dep in dependencies:
            source = dep.source
            if source not in analysis["by_source"]:
                analysis["by_source"][source] = 0
            analysis["by_source"][source] += 1

        # Identify potential security concerns
        security_sensitive = [
            "express",
            "django",
            "flask",
            "react",
            "vue",
            "angular",
            "spring",
        ]
        for dep in dependencies:
            if any(sensitive in dep.name.lower() for sensitive in security_sensitive):
                analysis["security_concerns"].append(
                    {
                        "dependency": dep.name,
                        "reason": "Security-sensitive framework requiring careful configuration",
                    }
                )

        # Identify outdated patterns (simplified)
        outdated_patterns = ["jquery", "bower", "grunt", "gulp"]
        for dep in dependencies:
            if any(pattern in dep.name.lower() for pattern in outdated_patterns):
                analysis["outdated_patterns"].append(
                    {
                        "dependency": dep.name,
                        "reason": "Consider modern alternatives",
                    }
                )

        # Generate recommendations
        if len(dependencies) > 50:
            analysis["recommendations"].append("Consider dependency audit and cleanup")

        if len(analysis["security_concerns"]) > 0:
            analysis["recommendations"].append(
                "Implement security scanning for dependencies"
            )

        if len(analysis["outdated_patterns"]) > 0:
            analysis["recommendations"].append(
                "Consider modernizing outdated dependencies"
            )

        return analysis

    def _analyze_code_quality_indicators(
        self, project_path: Path, context: ProjectContext
    ) -> Dict[str, Any]:
        """Analyze code quality indicators from project structure"""
        indicators: Dict[str, Any] = {
            "test_coverage_estimate": 0.0,
            "documentation_coverage": 0.0,
            "configuration_organization": "unknown",
            "code_organization": "unknown",
            "quality_score": 0.0,
            "recommendations": [],
        }

        # Estimate test coverage based on file ratios
        source_count = len(context.file_structure.source_files)
        test_count = len(context.file_structure.test_files)

        if source_count > 0:
            indicators["test_coverage_estimate"] = min(test_count / source_count, 1.0)

        # Documentation coverage
        doc_count = len(context.file_structure.documentation_files)
        total_files = context.file_structure.total_files

        if total_files > 0:
            indicators["documentation_coverage"] = min(
                doc_count / max(total_files * 0.1, 1), 1.0
            )

        # Configuration organization
        config_count = len(context.file_structure.config_files)
        if config_count <= 3:
            indicators["configuration_organization"] = "simple"
        elif config_count <= 8:
            indicators["configuration_organization"] = "organized"
        else:
            indicators["configuration_organization"] = "complex"

        # Code organization based on directory structure
        dir_count = len(context.file_structure.directories)
        if dir_count < 3:
            indicators["code_organization"] = "flat"
        elif dir_count < 10:
            indicators["code_organization"] = "organized"
        elif dir_count < 20:
            indicators["code_organization"] = "well-structured"
        else:
            indicators["code_organization"] = "complex"

        # Calculate overall quality score
        quality_factors = [
            indicators["test_coverage_estimate"],
            indicators["documentation_coverage"],
            (
                0.8
                if indicators["configuration_organization"] in ["simple", "organized"]
                else 0.4
            ),
            (
                0.8
                if indicators["code_organization"] in ["organized", "well-structured"]
                else 0.4
            ),
        ]

        indicators["quality_score"] = sum(quality_factors) / len(quality_factors)

        # Generate recommendations
        if indicators["test_coverage_estimate"] < 0.3:
            indicators["recommendations"].append("Increase test coverage")

        if indicators["documentation_coverage"] < 0.1:
            indicators["recommendations"].append("Add project documentation")

        if indicators["configuration_organization"] == "complex":
            indicators["recommendations"].append("Simplify configuration management")

        if indicators["code_organization"] == "flat":
            indicators["recommendations"].append(
                "Improve code organization with better directory structure"
            )

        return indicators

    # Helper methods for file and content analysis

    def _is_config_file(self, filename: str) -> bool:
        """Check if file is a configuration file"""
        config_patterns = [
            r".*\.config\.(js|ts|json|yaml|yml)$",
            r".*\.json$",
            r".*\.yaml$",
            r".*\.yml$",
            r".*\.toml$",
            r".*\.ini$",
            r".*\.env$",
            r"Dockerfile",
            r"docker-compose\.yml",
            r"Makefile",
            r"package\.json",
            r"requirements\.txt",
            r"setup\.py",
            r"pyproject\.toml",
        ]

        return any(
            re.match(pattern, filename, re.IGNORECASE) for pattern in config_patterns
        )

    def _is_source_file(self, filename: str) -> bool:
        """Check if file is a source code file"""
        source_extensions = [
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cs",
            ".cpp",
            ".c",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".swift",
            ".kt",
        ]
        return any(filename.lower().endswith(ext) for ext in source_extensions)

    def _is_test_file(self, filename: str) -> bool:
        """Check if file is a test file"""
        test_patterns = [
            r".*test.*\.(py|js|ts|jsx|tsx)$",
            r".*spec.*\.(py|js|ts|jsx|tsx)$",
            r"test_.*\.py$",
            r".*_test\.py$",
        ]

        return any(
            re.match(pattern, filename, re.IGNORECASE) for pattern in test_patterns
        )

    def _is_documentation_file(self, filename: str) -> bool:
        """Check if file is documentation"""
        doc_patterns = [
            r"README.*",
            r".*\.md$",
            r".*\.rst$",
            r".*\.txt$",
            r"CHANGELOG.*",
            r"LICENSE.*",
            r"CONTRIBUTING.*",
        ]

        return any(
            re.match(pattern, filename, re.IGNORECASE) for pattern in doc_patterns
        )

    def _get_package_dependencies(self, project_path: Path) -> List[Dependency]:
        """Get all package dependencies from various sources"""
        dependencies = []

        # This is a simplified version - the full implementation would parse all package files
        package_json = project_path / "package.json"
        if package_json.exists():
            dependencies.extend(self._parse_package_json(package_json))

        requirements_txt = project_path / "requirements.txt"
        if requirements_txt.exists():
            dependencies.extend(self._parse_requirements_txt(requirements_txt))

        return dependencies

    def _parse_package_json(self, package_json_path: Path) -> List[Dependency]:
        """Parse package.json for dependencies"""
        dependencies = []

        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Parse different dependency types
            for dep_type in [
                "dependencies",
                "devDependencies",
                "peerDependencies",
            ]:
                if dep_type in data:
                    for name, version in data[dep_type].items():
                        dependencies.append(
                            Dependency(
                                name=name,
                                version=version,
                                type=dep_type,
                                source="package.json",
                            )
                        )

        except Exception as e:
            logger.error(f"Error parsing package.json: {e}")

        return dependencies

    def _parse_requirements_txt(self, requirements_path: Path) -> List[Dependency]:
        """Parse requirements.txt for dependencies"""
        dependencies = []

        try:
            with open(requirements_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Simple parsing - could be enhanced for complex version specs
                        if "==" in line:
                            name, version = line.split("==", 1)
                        elif ">=" in line:
                            name, version = line.split(">=", 1)
                        else:
                            name, version = line, None

                        dependencies.append(
                            Dependency(
                                name=name.strip(),
                                version=version.strip() if version else None,
                                type="runtime",
                                source="requirements.txt",
                            )
                        )

        except Exception as e:
            logger.error(f"Error parsing requirements.txt: {e}")

        return dependencies

    def _parse_pyproject_toml(self, pyproject_path: Path) -> List[Dependency]:
        """Parse pyproject.toml for dependencies"""
        dependencies = []

        try:
            # Simple TOML parsing for dependencies section
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for [tool.poetry.dependencies] or [project.dependencies] sections
            in_deps_section = False
            for line in content.split("\n"):
                line = line.strip()

                if line.startswith("[tool.poetry.dependencies]") or line.startswith(
                    "[project.dependencies]"
                ):
                    in_deps_section = True
                    continue
                elif line.startswith("[") and in_deps_section:
                    in_deps_section = False
                    continue

                if in_deps_section and "=" in line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        name = parts[0].strip().strip("\"'")
                        version = parts[1].strip().strip("\"'")
                        if name != "python":  # Skip python version requirement
                            dependencies.append(
                                Dependency(
                                    name=name,
                                    version=version,
                                    type="runtime",
                                    source="pyproject.toml",
                                )
                            )

        except Exception as e:
            logger.error(f"Error parsing pyproject.toml: {e}")

        return dependencies

    def _parse_gemfile(self, gemfile_path: Path) -> List[Dependency]:
        """Parse Gemfile for dependencies"""
        dependencies = []

        try:
            with open(gemfile_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("gem ") and not line.startswith("#"):
                        # Parse gem "name", "version" format
                        parts = line.split(",")
                        if len(parts) >= 1:
                            gem_part = parts[0].replace("gem ", "").strip().strip("\"'")
                            version = None
                            if len(parts) > 1:
                                version = parts[1].strip().strip("\"'")

                            dependencies.append(
                                Dependency(
                                    name=gem_part,
                                    version=version,
                                    type="runtime",
                                    source="Gemfile",
                                )
                            )

        except Exception as e:
            logger.error(f"Error parsing Gemfile: {e}")

        return dependencies

    def _parse_yarn_lock(self, yarn_lock_path: Path) -> List[Dependency]:
        """Parse yarn.lock for dependencies (simplified)"""
        # Yarn.lock is complex, this is a basic implementation
        return []

    def _parse_setup_py(self, setup_py_path: Path) -> List[Dependency]:
        """Parse setup.py for dependencies"""
        dependencies = []

        try:
            with open(setup_py_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for install_requires or requires patterns
            install_requires_match = re.search(
                r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL
            )
            if install_requires_match:
                deps_str = install_requires_match.group(1)
                for line in deps_str.split(","):
                    line = line.strip().strip("\"'")
                    if line and not line.startswith("#"):
                        # Parse package>=version format
                        if ">=" in line:
                            name, version = line.split(">=", 1)
                        elif "==" in line:
                            name, version = line.split("==", 1)
                        else:
                            name, version = line, None

                        dependencies.append(
                            Dependency(
                                name=name.strip(),
                                version=version.strip() if version else None,
                                type="runtime",
                                source="setup.py",
                            )
                        )

        except Exception as e:
            logger.error(f"Error parsing setup.py: {e}")

        return dependencies

    def _parse_pipfile(self, pipfile_path: Path) -> List[Dependency]:
        """Parse Pipfile for dependencies"""
        dependencies = []

        try:
            with open(pipfile_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for [packages] and [dev-packages] sections
            in_packages = False
            in_dev_packages = False

            for line in content.split("\n"):
                line = line.strip()

                if line == "[packages]":
                    in_packages = True
                    in_dev_packages = False
                    continue
                elif line == "[dev-packages]":
                    in_packages = False
                    in_dev_packages = True
                    continue
                elif line.startswith("["):
                    in_packages = False
                    in_dev_packages = False
                    continue

                if (
                    (in_packages or in_dev_packages)
                    and "=" in line
                    and not line.startswith("#")
                ):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        version = parts[1].strip().strip("\"'")
                        dep_type = "dev" if in_dev_packages else "runtime"

                        dependencies.append(
                            Dependency(
                                name=name,
                                version=version,
                                type=dep_type,
                                source="Pipfile",
                            )
                        )

        except Exception as e:
            logger.error(f"Error parsing Pipfile: {e}")

        return dependencies

    def _parse_pom_xml(self, pom_xml_path: Path) -> List[Dependency]:
        """Parse pom.xml for Maven dependencies (simplified)"""
        dependencies = []

        try:
            with open(pom_xml_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple regex to find dependencies
            dep_pattern = r"<dependency>.*?<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>.*?(?:<version>(.*?)</version>)?.*?</dependency>"
            matches = re.findall(dep_pattern, content, re.DOTALL)

            for match in matches:
                group_id, artifact_id, version = match
                name = f"{group_id}:{artifact_id}"
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version if version else None,
                        type="runtime",
                        source="pom.xml",
                    )
                )

        except Exception as e:
            logger.error(f"Error parsing pom.xml: {e}")

        return dependencies

    def _parse_build_gradle(self, build_gradle_path: Path) -> List[Dependency]:
        """Parse build.gradle for Gradle dependencies (simplified)"""
        dependencies = []

        try:
            with open(build_gradle_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for implementation, compile, testImplementation etc.
            dep_pattern = (
                r'(implementation|compile|testImplementation|api)\s+[\'"]([^\'"]+)[\'"]'
            )
            matches = re.findall(dep_pattern, content)

            for dep_type, dep_name in matches:
                # Parse group:name:version format
                parts = dep_name.split(":")
                if len(parts) >= 2:
                    name = f"{parts[0]}:{parts[1]}"
                    version = parts[2] if len(parts) > 2 else None

                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=("dev" if "test" in dep_type.lower() else "runtime"),
                            source="build.gradle",
                        )
                    )

        except Exception as e:
            logger.error(f"Error parsing build.gradle: {e}")

        return dependencies

    def _parse_go_mod(self, go_mod_path: Path) -> List[Dependency]:
        """Parse go.mod for Go dependencies"""
        dependencies = []

        try:
            with open(go_mod_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for require section
            in_require = False
            for line in content.split("\n"):
                line = line.strip()

                if line.startswith("require ("):
                    in_require = True
                    continue
                elif line == ")" and in_require:
                    in_require = False
                    continue
                elif line.startswith("require ") and not in_require:
                    # Single line require
                    parts = line.replace("require ", "").split()
                    if len(parts) >= 2:
                        dependencies.append(
                            Dependency(
                                name=parts[0],
                                version=parts[1],
                                type="runtime",
                                source="go.mod",
                            )
                        )
                elif in_require and line and not line.startswith("//"):
                    parts = line.split()
                    if len(parts) >= 2:
                        dependencies.append(
                            Dependency(
                                name=parts[0],
                                version=parts[1],
                                type="runtime",
                                source="go.mod",
                            )
                        )

        except Exception as e:
            logger.error(f"Error parsing go.mod: {e}")

        return dependencies

    def _parse_cargo_toml(self, cargo_toml_path: Path) -> List[Dependency]:
        """Parse Cargo.toml for Rust dependencies"""
        dependencies = []

        try:
            with open(cargo_toml_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for [dependencies] section
            in_deps = False
            for line in content.split("\n"):
                line = line.strip()

                if line == "[dependencies]":
                    in_deps = True
                    continue
                elif line.startswith("[") and in_deps:
                    in_deps = False
                    continue

                if in_deps and "=" in line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        version = parts[1].strip().strip("\"'")

                        dependencies.append(
                            Dependency(
                                name=name,
                                version=version,
                                type="runtime",
                                source="Cargo.toml",
                            )
                        )

        except Exception as e:
            logger.error(f"Error parsing Cargo.toml: {e}")

        return dependencies

    def _parse_composer_json(self, composer_json_path: Path) -> List[Dependency]:
        """Parse composer.json for PHP dependencies"""
        dependencies = []

        try:
            with open(composer_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Parse require and require-dev sections
            for section, dep_type in [
                ("require", "runtime"),
                ("require-dev", "dev"),
            ]:
                if section in data:
                    for name, version in data[section].items():
                        if name != "php":  # Skip PHP version requirement
                            dependencies.append(
                                Dependency(
                                    name=name,
                                    version=version,
                                    type=dep_type,
                                    source="composer.json",
                                )
                            )

        except Exception as e:
            logger.error(f"Error parsing composer.json: {e}")

        return dependencies

    def _parse_csproj(self, csproj_path: Path) -> List[Dependency]:
        """Parse .csproj for .NET dependencies"""
        dependencies = []

        try:
            with open(csproj_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for PackageReference elements
            package_pattern = (
                r'<PackageReference\s+Include="([^"]+)"\s+Version="([^"]+)"'
            )
            matches = re.findall(package_pattern, content)

            for name, version in matches:
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        type="runtime",
                        source=csproj_path.name,
                    )
                )

        except Exception as e:
            logger.error(f"Error parsing {csproj_path.name}: {e}")

        return dependencies

    def _find_files_matching_pattern(self, project_path: Path, pattern: str) -> bool:
        """Find files matching a regex pattern"""
        try:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["node_modules", "__pycache__"]
                ]
                for file in files:
                    if re.match(pattern, file):
                        return True
        except Exception:
            pass  # nosec B110 # Intentionally ignore file access errors
        return False

    def _find_content_matching_pattern(self, project_path: Path, pattern: str) -> bool:
        """Find content matching a regex pattern in source files"""
        try:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["node_modules", "__pycache__"]
                ]
                for file in files:
                    if self._is_source_file(file) or self._is_config_file(file):
                        file_path = Path(root) / file
                        try:
                            with open(
                                file_path,
                                "r",
                                encoding="utf-8",
                                errors="ignore",
                            ) as f:
                                content = f.read()
                                if re.search(pattern, content, re.IGNORECASE):
                                    return True
                        except Exception:
                            continue  # nosec B112 # Intentionally skip unreadable files
        except Exception:
            pass  # nosec B110 # Intentionally ignore file access errors
        return False

    # Comprehensive instruction suggestion methods

    def _get_base_suggestions(self) -> List[InstructionSuggestion]:
        """Get base suggestions for all projects"""
        return [
            InstructionSuggestion(
                instruction_id="context_management",
                tags=["general", "persistence", "resume", "tracking"],
                confidence=0.9,
                reasons=["Essential for maintaining task context across sessions"],
                category="general",
            ),
            InstructionSuggestion(
                instruction_id="project_context",
                tags=["general", "persistence", "commands", "debugging"],
                confidence=0.8,
                reasons=["Helps avoid repeating mistakes and track project state"],
                category="general",
            ),
            InstructionSuggestion(
                instruction_id="thorough_analysis",
                tags=["general", "analysis", "debugging", "investigation"],
                confidence=0.9,
                reasons=["Critical for understanding codebase before making changes"],
                category="general",
            ),
            InstructionSuggestion(
                instruction_id="no_error_policy",
                tags=["general", "quality", "testing", "integration"],
                confidence=1.0,
                reasons=["Ensures code quality and prevents broken deployments"],
                category="general",
            ),
        ]

    def _get_language_suggestions(
        self, language: Language
    ) -> List[InstructionSuggestion]:
        """Get suggestions based on programming language"""
        suggestions = []

        language_mapping = {
            Language.PYTHON: [
                (
                    "python_best_practices",
                    ["python", "best-practices", "pep8"],
                    0.9,
                    "Python project detected",
                ),
                (
                    "python_testing",
                    ["python", "testing", "pytest"],
                    0.8,
                    "Python projects benefit from comprehensive testing",
                ),
                (
                    "python_packaging",
                    ["python", "packaging", "setup"],
                    0.7,
                    "Python projects need proper packaging",
                ),
            ],
            Language.JAVASCRIPT: [
                (
                    "javascript_best_practices",
                    ["javascript", "best-practices", "es6"],
                    0.9,
                    "JavaScript project detected",
                ),
                (
                    "javascript_testing",
                    ["javascript", "testing", "jest"],
                    0.8,
                    "JavaScript projects need testing framework",
                ),
                (
                    "npm_security",
                    ["javascript", "security", "npm"],
                    0.8,
                    "JavaScript projects have npm security considerations",
                ),
            ],
            Language.TYPESCRIPT: [
                (
                    "typescript_configuration",
                    ["typescript", "configuration", "tsconfig"],
                    0.9,
                    "TypeScript project detected",
                ),
                (
                    "type_safety",
                    ["typescript", "types", "safety"],
                    0.8,
                    "TypeScript projects benefit from strict typing",
                ),
                (
                    "typescript_testing",
                    ["typescript", "testing", "types"],
                    0.7,
                    "TypeScript testing with type safety",
                ),
            ],
            Language.JAVA: [
                (
                    "java_best_practices",
                    ["java", "best-practices", "spring"],
                    0.9,
                    "Java project detected",
                ),
                (
                    "java_testing",
                    ["java", "testing", "junit"],
                    0.8,
                    "Java projects need comprehensive testing",
                ),
                (
                    "java_security",
                    ["java", "security", "spring-security"],
                    0.8,
                    "Java applications need security considerations",
                ),
            ],
            Language.GO: [
                (
                    "go_best_practices",
                    ["go", "best-practices", "gofmt"],
                    0.9,
                    "Go project detected",
                ),
                (
                    "go_testing",
                    ["go", "testing", "benchmark"],
                    0.8,
                    "Go has excellent built-in testing",
                ),
                (
                    "go_concurrency",
                    ["go", "concurrency", "goroutines"],
                    0.7,
                    "Go projects often use concurrency",
                ),
            ],
            Language.RUST: [
                (
                    "rust_best_practices",
                    ["rust", "best-practices", "cargo"],
                    0.9,
                    "Rust project detected",
                ),
                (
                    "rust_safety",
                    ["rust", "safety", "ownership"],
                    0.8,
                    "Rust memory safety patterns",
                ),
                (
                    "rust_testing",
                    ["rust", "testing", "cargo-test"],
                    0.8,
                    "Rust testing with cargo",
                ),
            ],
        }

        if language in language_mapping:
            for inst_id, tags, confidence, reason in language_mapping[language]:
                suggestions.append(
                    InstructionSuggestion(
                        instruction_id=inst_id,
                        tags=tags,
                        confidence=confidence,
                        reasons=[reason],
                        category="languages",
                    )
                )

        return suggestions

    def _get_framework_suggestions(
        self, framework: Framework
    ) -> List[InstructionSuggestion]:
        """Get suggestions based on detected framework"""
        suggestions = []

        framework_mapping = {
            "react": [
                (
                    "frontend_state_management",
                    ["frontend", "state", "react"],
                    "React state management patterns",
                ),
                (
                    "accessibility_compliance",
                    ["accessibility", "frontend", "ui"],
                    "React apps need accessibility",
                ),
                (
                    "mobile_responsiveness",
                    ["frontend", "mobile", "responsive"],
                    "React apps should be mobile-friendly",
                ),
                (
                    "progressive_web_app",
                    ["frontend", "pwa", "offline"],
                    "React can be enhanced with PWA features",
                ),
            ],
            "vue": [
                (
                    "frontend_state_management",
                    ["frontend", "state", "vue"],
                    "Vue state management with Vuex",
                ),
                (
                    "accessibility_compliance",
                    ["accessibility", "frontend", "ui"],
                    "Vue apps need accessibility",
                ),
                (
                    "mobile_responsiveness",
                    ["frontend", "mobile", "responsive"],
                    "Vue apps should be mobile-friendly",
                ),
            ],
            "angular": [
                (
                    "frontend_state_management",
                    ["frontend", "state", "angular"],
                    "Angular state management with NgRx",
                ),
                (
                    "accessibility_compliance",
                    ["accessibility", "frontend", "ui"],
                    "Angular apps need accessibility",
                ),
                (
                    "mobile_responsiveness",
                    ["frontend", "mobile", "responsive"],
                    "Angular apps should be mobile-friendly",
                ),
                (
                    "typescript_configuration",
                    ["typescript", "configuration"],
                    "Angular uses TypeScript",
                ),
            ],
            "django": [
                (
                    "api_design",
                    ["api", "design", "rest"],
                    "Django REST API best practices",
                ),
                (
                    "database_optimization",
                    ["database", "performance", "optimization"],
                    "Django ORM optimization",
                ),
                (
                    "django_security",
                    ["security", "django", "authentication"],
                    "Django security features",
                ),
                (
                    "django_testing",
                    ["testing", "django", "pytest"],
                    "Django testing patterns",
                ),
            ],
            "flask": [
                (
                    "api_design",
                    ["api", "design", "rest"],
                    "Flask API design patterns",
                ),
                (
                    "flask_security",
                    ["security", "flask", "authentication"],
                    "Flask security considerations",
                ),
                (
                    "database_optimization",
                    ["database", "performance"],
                    "Flask database patterns",
                ),
            ],
            "fastapi": [
                (
                    "api_design",
                    ["api", "design", "rest"],
                    "FastAPI automatic documentation",
                ),
                (
                    "async_programming",
                    ["async", "performance", "python"],
                    "FastAPI async patterns",
                ),
                (
                    "api_testing",
                    ["testing", "api", "pytest"],
                    "FastAPI testing strategies",
                ),
            ],
            "express": [
                (
                    "api_design",
                    ["api", "design", "rest"],
                    "Express.js API patterns",
                ),
                (
                    "webhook_handling",
                    ["webhooks", "api", "integration"],
                    "Express webhook handling",
                ),
                (
                    "real_time_features",
                    ["realtime", "websockets", "sse"],
                    "Express real-time features",
                ),
                (
                    "node_security",
                    ["security", "node", "express"],
                    "Express security middleware",
                ),
            ],
            "nextjs": [
                (
                    "frontend_state_management",
                    ["frontend", "state", "react"],
                    "Next.js state management",
                ),
                (
                    "progressive_web_app",
                    ["frontend", "pwa", "offline"],
                    "Next.js PWA capabilities",
                ),
                (
                    "seo_optimization",
                    ["seo", "performance", "nextjs"],
                    "Next.js SEO features",
                ),
                (
                    "api_design",
                    ["api", "design", "serverless"],
                    "Next.js API routes",
                ),
            ],
            "spring": [
                (
                    "api_design",
                    ["api", "design", "rest"],
                    "Spring Boot REST APIs",
                ),
                (
                    "database_optimization",
                    ["database", "performance", "jpa"],
                    "Spring Data JPA optimization",
                ),
                (
                    "spring_security",
                    ["security", "spring", "authentication"],
                    "Spring Security configuration",
                ),
                (
                    "microservices_architecture",
                    ["microservices", "spring", "cloud"],
                    "Spring Cloud microservices",
                ),
            ],
        }

        if framework.name in framework_mapping:
            for inst_id, tags, reason in framework_mapping[framework.name]:
                suggestions.append(
                    InstructionSuggestion(
                        instruction_id=inst_id,
                        tags=tags,
                        confidence=min(framework.confidence + 0.1, 1.0),
                        reasons=[
                            f"{reason} (detected {framework.name} with {framework.confidence:.1%} confidence)"
                        ],
                        category=("frontend" if "frontend" in tags else "backend"),
                    )
                )

        return suggestions

    def _get_project_type_suggestions(
        self, project_type: ProjectType
    ) -> List[InstructionSuggestion]:
        """Get suggestions based on project type"""
        suggestions = []

        type_mapping = {
            ProjectType.WEB_FRONTEND: [
                (
                    "accessibility_compliance",
                    ["accessibility", "frontend", "ui"],
                    0.9,
                    "Frontend projects must be accessible",
                ),
                (
                    "mobile_responsiveness",
                    ["frontend", "mobile", "responsive"],
                    0.9,
                    "Frontend must work on mobile",
                ),
                (
                    "progressive_web_app",
                    ["frontend", "pwa", "offline"],
                    0.7,
                    "Consider PWA features for web apps",
                ),
                (
                    "frontend_performance",
                    ["frontend", "performance", "optimization"],
                    0.8,
                    "Frontend performance is critical",
                ),
                (
                    "seo_optimization",
                    ["seo", "performance", "frontend"],
                    0.7,
                    "SEO important for web applications",
                ),
            ],
            ProjectType.WEB_BACKEND: [
                (
                    "api_design",
                    ["api", "design", "rest"],
                    0.9,
                    "Backend projects need well-designed APIs",
                ),
                (
                    "database_optimization",
                    ["database", "performance", "optimization"],
                    0.8,
                    "Backend likely uses databases",
                ),
                (
                    "api_security",
                    ["security", "api", "authentication"],
                    0.9,
                    "API security is critical",
                ),
                (
                    "webhook_handling",
                    ["webhooks", "api", "integration"],
                    0.6,
                    "Backend may need webhook support",
                ),
                (
                    "real_time_features",
                    ["realtime", "websockets", "sse"],
                    0.5,
                    "Consider real-time capabilities",
                ),
            ],
            ProjectType.FULLSTACK_WEB: [
                (
                    "api_design",
                    ["api", "design", "rest"],
                    0.8,
                    "Fullstack needs API design",
                ),
                (
                    "accessibility_compliance",
                    ["accessibility", "frontend", "ui"],
                    0.8,
                    "Fullstack needs accessibility",
                ),
                (
                    "database_optimization",
                    ["database", "performance"],
                    0.7,
                    "Fullstack likely uses databases",
                ),
                (
                    "progressive_web_app",
                    ["frontend", "pwa", "offline"],
                    0.7,
                    "Fullstack can benefit from PWA",
                ),
                (
                    "seo_optimization",
                    ["seo", "performance"],
                    0.8,
                    "Fullstack apps need SEO",
                ),
            ],
            ProjectType.MOBILE_APP: [
                (
                    "mobile_performance",
                    ["mobile", "performance", "optimization"],
                    0.9,
                    "Mobile performance is critical",
                ),
                (
                    "offline_functionality",
                    ["mobile", "offline", "sync"],
                    0.8,
                    "Mobile apps need offline support",
                ),
                (
                    "push_notifications",
                    ["mobile", "notifications", "engagement"],
                    0.7,
                    "Mobile apps benefit from notifications",
                ),
                (
                    "mobile_security",
                    ["mobile", "security", "data"],
                    0.8,
                    "Mobile security considerations",
                ),
            ],
            ProjectType.CLI_TOOL: [
                (
                    "cli_design",
                    ["cli", "usability", "help"],
                    0.9,
                    "CLI tools need good UX",
                ),
                (
                    "error_handling",
                    ["cli", "errors", "user-friendly"],
                    0.8,
                    "CLI error handling is important",
                ),
                (
                    "configuration_management",
                    ["cli", "config", "flexibility"],
                    0.7,
                    "CLI tools need configuration",
                ),
                (
                    "cross_platform",
                    ["cli", "compatibility", "portability"],
                    0.7,
                    "CLI should work cross-platform",
                ),
            ],
            ProjectType.LIBRARY: [
                (
                    "api_design",
                    ["library", "api", "design"],
                    0.9,
                    "Libraries need clean APIs",
                ),
                (
                    "documentation",
                    ["library", "documentation", "examples"],
                    0.9,
                    "Libraries need excellent docs",
                ),
                (
                    "versioning",
                    ["library", "versioning", "compatibility"],
                    0.8,
                    "Library versioning is critical",
                ),
                (
                    "testing",
                    ["library", "testing", "coverage"],
                    0.9,
                    "Libraries need comprehensive tests",
                ),
            ],
            ProjectType.MICROSERVICE: [
                (
                    "microservices_architecture",
                    ["microservices", "architecture", "design"],
                    0.9,
                    "Microservice design patterns",
                ),
                (
                    "api_design",
                    ["api", "design", "rest"],
                    0.9,
                    "Microservices need well-designed APIs",
                ),
                (
                    "observability",
                    ["monitoring", "logging", "tracing"],
                    0.8,
                    "Microservices need observability",
                ),
                (
                    "resilience_patterns",
                    ["resilience", "circuit-breaker", "retry"],
                    0.8,
                    "Microservices need resilience",
                ),
                (
                    "containerization",
                    ["docker", "kubernetes", "deployment"],
                    0.8,
                    "Microservices often use containers",
                ),
            ],
        }

        if project_type in type_mapping:
            for inst_id, tags, confidence, reason in type_mapping[project_type]:
                suggestions.append(
                    InstructionSuggestion(
                        instruction_id=inst_id,
                        tags=tags,
                        confidence=confidence,
                        reasons=[reason],
                        category=self._categorize_by_tags(tags),
                    )
                )

        return suggestions

    def _get_dependency_suggestions(
        self, dependencies: List[Dependency]
    ) -> List[InstructionSuggestion]:
        """Get suggestions based on project dependencies"""
        suggestions = []
        dep_names = [dep.name.lower() for dep in dependencies]

        # Security-sensitive dependencies
        security_deps = {
            "express": (
                "express_security",
                ["security", "express", "middleware"],
                "Express security middleware needed",
            ),
            "django": (
                "django_security",
                ["security", "django", "authentication"],
                "Django security best practices",
            ),
            "flask": (
                "flask_security",
                ["security", "flask", "authentication"],
                "Flask security considerations",
            ),
            "react": (
                "react_security",
                ["security", "react", "xss"],
                "React XSS prevention",
            ),
            "spring-boot": (
                "spring_security",
                ["security", "spring", "authentication"],
                "Spring Security configuration",
            ),
            "fastapi": (
                "fastapi_security",
                ["security", "fastapi", "oauth"],
                "FastAPI security features",
            ),
        }

        for dep_name in dep_names:
            for sec_dep, (inst_id, tags, reason) in security_deps.items():
                if sec_dep in dep_name:
                    suggestions.append(
                        InstructionSuggestion(
                            instruction_id=inst_id,
                            tags=tags,
                            confidence=0.8,
                            reasons=[f"{reason} (detected {sec_dep} dependency)"],
                            category="security",
                        )
                    )

        # Database dependencies
        db_deps = {
            "postgresql": (
                "database_optimization",
                ["database", "postgresql", "performance"],
                "PostgreSQL optimization",
            ),
            "mysql": (
                "database_optimization",
                ["database", "mysql", "performance"],
                "MySQL optimization",
            ),
            "mongodb": (
                "nosql_patterns",
                ["database", "mongodb", "nosql"],
                "MongoDB best practices",
            ),
            "redis": (
                "caching_strategies",
                ["performance", "redis", "caching"],
                "Redis caching patterns",
            ),
            "elasticsearch": (
                "search_optimization",
                ["search", "elasticsearch", "performance"],
                "Elasticsearch optimization",
            ),
        }

        for dep_name in dep_names:
            for db_dep, (inst_id, tags, reason) in db_deps.items():
                if db_dep in dep_name:
                    suggestions.append(
                        InstructionSuggestion(
                            instruction_id=inst_id,
                            tags=tags,
                            confidence=0.7,
                            reasons=[f"{reason} (detected {db_dep} dependency)"],
                            category="performance",
                        )
                    )

        # Testing dependencies
        test_deps = {
            "jest": (
                "javascript_testing",
                ["testing", "javascript", "jest"],
                "Jest testing framework detected",
            ),
            "pytest": (
                "python_testing",
                ["testing", "python", "pytest"],
                "Pytest testing framework detected",
            ),
            "junit": (
                "java_testing",
                ["testing", "java", "junit"],
                "JUnit testing framework detected",
            ),
            "mocha": (
                "javascript_testing",
                ["testing", "javascript", "mocha"],
                "Mocha testing framework detected",
            ),
            "cypress": (
                "e2e_testing",
                ["testing", "e2e", "cypress"],
                "Cypress E2E testing detected",
            ),
        }

        for dep_name in dep_names:
            for test_dep, (inst_id, tags, reason) in test_deps.items():
                if test_dep in dep_name:
                    suggestions.append(
                        InstructionSuggestion(
                            instruction_id=inst_id,
                            tags=tags,
                            confidence=0.8,
                            reasons=[f"{reason}"],
                            category="testing",
                        )
                    )

        return suggestions

    def _get_structure_suggestions(
        self, file_structure: FileStructure
    ) -> List[InstructionSuggestion]:
        """Get suggestions based on file structure analysis"""
        suggestions = []

        # Testing suggestions
        has_tests = len(file_structure.test_files) > 0
        has_source = len(file_structure.source_files) > 0

        if not has_tests and has_source:
            suggestions.append(
                InstructionSuggestion(
                    instruction_id="testing_setup",
                    tags=["testing", "quality", "setup"],
                    confidence=0.9,
                    reasons=["No test files detected in project with source code"],
                    category="testing",
                )
            )
        elif has_tests:
            test_coverage_ratio = len(file_structure.test_files) / len(
                file_structure.source_files
            )
            if test_coverage_ratio < 0.3:  # Less than 30% test coverage
                suggestions.append(
                    InstructionSuggestion(
                        instruction_id="test_coverage",
                        tags=["testing", "coverage", "quality"],
                        confidence=0.7,
                        reasons=[f"Low test coverage ratio: {test_coverage_ratio:.1%}"],
                        category="testing",
                    )
                )

        # Documentation suggestions
        has_docs = len(file_structure.documentation_files) > 0
        if not has_docs:
            suggestions.append(
                InstructionSuggestion(
                    instruction_id="documentation",
                    tags=["documentation", "maintenance", "readme"],
                    confidence=0.8,
                    reasons=["No documentation files detected"],
                    category="general",
                )
            )

        # Configuration management
        config_count = len(file_structure.config_files)
        if config_count > 10:
            suggestions.append(
                InstructionSuggestion(
                    instruction_id="configuration_management",
                    tags=["configuration", "management", "organization"],
                    confidence=0.7,
                    reasons=[f"Many configuration files detected ({config_count})"],
                    category="general",
                )
            )

        # Project size considerations
        if file_structure.total_files > 500:
            suggestions.extend(
                [
                    InstructionSuggestion(
                        instruction_id="large_codebase_management",
                        tags=["architecture", "organization", "scalability"],
                        confidence=0.8,
                        reasons=[
                            f"Large codebase detected ({file_structure.total_files} files)"
                        ],
                        category="architecture",
                    ),
                    InstructionSuggestion(
                        instruction_id="build_optimization",
                        tags=["performance", "build", "optimization"],
                        confidence=0.7,
                        reasons=["Large projects benefit from build optimization"],
                        category="performance",
                    ),
                ]
            )

        # File type analysis
        if ".js" in file_structure.file_types and ".ts" in file_structure.file_types:
            js_count = file_structure.file_types.get(".js", 0)
            ts_count = file_structure.file_types.get(".ts", 0)
            if js_count > ts_count * 2:  # More JS than TS
                suggestions.append(
                    InstructionSuggestion(
                        instruction_id="typescript_migration",
                        tags=["typescript", "migration", "type-safety"],
                        confidence=0.6,
                        reasons=[
                            "Mixed JS/TS project could benefit from full TypeScript migration"
                        ],
                        category="languages",
                    )
                )

        return suggestions

    def _categorize_by_tags(self, tags: List[str]) -> str:
        """Categorize instruction by its tags"""
        tag_categories = {
            "frontend": "frontend",
            "backend": "backend",
            "security": "security",
            "testing": "testing",
            "performance": "performance",
            "database": "database",
            "api": "backend",
            "mobile": "mobile",
            "architecture": "architecture",
            "devops": "devops",
            "documentation": "general",
        }

        for tag in tags:
            if tag in tag_categories:
                return tag_categories[tag]

        return "general"
