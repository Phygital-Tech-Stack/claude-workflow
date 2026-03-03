"""C#/.NET failure pattern matcher for post-failure.sh dispatcher."""


def match(cmd: str, output: str) -> list[str] | None:
    """Match C#/.NET error patterns and return recovery suggestions."""
    suggestions = []

    # dotnet build failures
    if "dotnet build" in cmd or "dotnet restore" in cmd:
        if "could not be resolved" in output or "NU1101" in output:
            suggestions.append(
                "Package not found — check package name on nuget.org and run `dotnet restore`"
            )
        elif "CS0246" in output or "type or namespace" in output:
            suggestions.append("Missing using directive or package reference — check imports")
        elif "CS1061" in output:
            suggestions.append(
                "Member not found — check class definition and available methods/properties"
            )
        elif "CS0029" in output or "Cannot implicitly convert" in output:
            suggestions.append("Type mismatch — check type assignments and casting")
        elif "MSB" in output:
            suggestions.append("MSBuild error — check .csproj file configuration")
        else:
            suggestions.append("Build error — read the CS/MSB error code and location")

    # dotnet test failures
    elif "dotnet test" in cmd:
        if "No test matches" in output or "No test is available" in output:
            suggestions.append(
                "No tests found — check [Fact]/[Theory] attributes and test project reference"
            )
        elif "timeout" in output or "Timeout" in output:
            suggestions.append("Test timeout — check for deadlocks or long-running operations")
        elif "connection" in output or "ConnectionString" in output:
            suggestions.append("Database connection failed — check connection string in appsettings")
        else:
            suggestions.append("Test failure — read assertion message for expected vs actual")

    # dotnet format failures
    elif "dotnet format" in cmd:
        if "error" in output:
            suggestions.append("Format error — likely a syntax error; fix compilation errors first")

    # EF Core migration failures
    elif "ef" in cmd and "migration" in cmd:
        if "already exists" in output:
            suggestions.append("Migration name conflict — use a different migration name")
        elif "pending" in output:
            suggestions.append(
                "Pending migrations — run `dotnet ef database update` first"
            )
        elif "snapshot" in output:
            suggestions.append(
                "Model snapshot mismatch — check DbContext model against latest migration"
            )
        else:
            suggestions.append("EF migration error — try `dotnet ef migrations list` to diagnose")

    # NuGet failures
    elif "nuget" in cmd or "restore" in cmd:
        if "401" in output or "403" in output:
            suggestions.append("Authentication failed — check NuGet source credentials")
        elif "version" in output and "conflict" in output:
            suggestions.append("Version conflict — check PackageReference versions in .csproj")

    return suggestions if suggestions else None
