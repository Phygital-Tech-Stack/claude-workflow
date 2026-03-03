"""Flutter/Dart failure pattern matcher for post-failure.sh dispatcher."""


def match(cmd: str, output: str) -> list[str] | None:
    """Match Flutter/Dart error patterns and return recovery suggestions."""
    suggestions = []

    # Flutter/Dart analyze failures
    if "flutter analyze" in cmd or "dart analyze" in cmd:
        if "unused_import" in output:
            suggestions.append("Unused import — remove the import or use the imported symbol")
        elif "undefined_class" in output or "undefined_identifier" in output:
            suggestions.append("Missing import or typo — check class/function name and add the correct import")
        elif "not a subtype" in output or "type_argument_not_matching_bounds" in output:
            suggestions.append("Type mismatch — check widget hierarchy and generic type parameters")
        elif "invalid_override" in output:
            suggestions.append("Method override mismatch — check parent class method signature")
        elif "missing_required_argument" in output:
            suggestions.append("Missing required parameter — check constructor/function signature")
        else:
            suggestions.append("Analysis error — read the specific error code and file:line reference")

    # Flutter/Dart test failures
    elif "flutter test" in cmd or "dart test" in cmd:
        if "connection refused" in output:
            suggestions.append("Backend not running — start the backend server first")
        elif "timeout" in output or "timed out" in output:
            suggestions.append(
                "Test timeout — check for unresolved Futures, missing async/await, "
                "or missing pump/pumpAndSettle"
            )
        elif "no test" in output or "no file" in output or "could not find" in output:
            suggestions.append("No tests found — check test file naming convention (*_test.dart)")
        elif "widget test" in output and "not found" in output:
            suggestions.append("Widget not found in test — check pump and finder")
        else:
            suggestions.append("Test failure — read assertion error for expected vs actual values")

    # Flutter build failures
    elif "flutter build" in cmd:
        if "out of memory" in output or "oom" in output:
            suggestions.append("OOM during build — close other apps or try flutter clean first")
        elif "minimum deployment" in output or "minsdk" in output:
            suggestions.append("Deployment target issue — check minSdkVersion or Podfile platform")
        elif "pubspec" in output or "dependency" in output:
            suggestions.append("Dependency issue — run flutter pub get and check pubspec.yaml")
        elif "gradle" in output:
            suggestions.append("Gradle error — try cd android && ./gradlew clean, then rebuild")
        elif "cocoapods" in output or "pod" in output:
            suggestions.append("CocoaPods error — try cd ios && pod install --repo-update")
        else:
            suggestions.append("Build failure — try flutter clean && flutter pub get && flutter build")

    # Pub get/upgrade failures
    elif "pub get" in cmd or "pub upgrade" in cmd or "pub add" in cmd:
        if "version solving failed" in output:
            suggestions.append("Version conflict — check pubspec.yaml dependency constraints")
        elif "git" in output and ("timeout" in output or "fatal" in output):
            suggestions.append("Git dependency timeout — check network connectivity")
        elif "could not find package" in output:
            suggestions.append(
                "Package not found — verify package name on pub.dev "
                "(AI can hallucinate package names)"
            )
        else:
            suggestions.append("Pub error — try flutter clean && flutter pub get")

    # Build runner failures
    elif "build_runner" in cmd:
        if "conflicting outputs" in output:
            suggestions.append(
                "Conflicting outputs — use: "
                "dart run build_runner build --delete-conflicting-outputs"
            )
        elif "could not resolve" in output or "unresolved" in output:
            suggestions.append("Unresolvable reference — check Drift table/model definitions")
        elif "stack overflow" in output:
            suggestions.append("Circular reference in code generation — check table relationships")
        else:
            suggestions.append(
                "Build runner error — try: "
                "dart run build_runner clean && "
                "dart run build_runner build --delete-conflicting-outputs"
            )

    # Dart format failures
    elif "dart format" in cmd:
        if "could not format" in output or "error" in output:
            suggestions.append("Format error — likely a syntax error; fix compilation errors first")

    # Pre-commit / gitleaks failures
    elif "pre_commit" in cmd or "pre-commit" in cmd or "gitleaks" in cmd:
        if "gitleaks" in output and ("secret" in output or "leak" in output):
            suggestions.append("Secret detected — remove the credential/key before committing")

    return suggestions if suggestions else None
