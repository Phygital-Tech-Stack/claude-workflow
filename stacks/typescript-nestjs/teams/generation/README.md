# Generation Team (TypeScript / NestJS)

Team prompts for parallelized module scaffolding. Used by `/generate-module --team` (skill planned, prompts ready).

## Prompt Inventory

| Prompt               | Role                | Model  | Purpose                                                 |
| -------------------- | ------------------- | ------ | ------------------------------------------------------- |
| `schema-builder.md`  | Database specialist | Sonnet | Drizzle table + history table + shared types interfaces |
| `backend-builder.md` | Nest.js specialist  | Sonnet | Repository + service + errors + module registration     |
| `api-builder.md`     | API specialist      | Sonnet | Controller + 4 DTOs (create, update, response, query)   |
| `test-writer.md`     | Testing specialist  | Sonnet | Service spec + controller spec                          |

## How It Works

### Phase 1: Read Inputs

The lead (Opus) reads the design doc and golden module, then produces a **structured Module Blueprint** that all teammates receive. This converts file dependencies into data dependencies, enabling full parallelism.

### Phase 2: Parallel Generation

```
Lead spawns 4 Tasks in parallel:
├─ schema-builder  -> drizzle/schema/<module>.ts + history + libs/shared-types/
├─ backend-builder -> apps/api/src/modules/<module>/{errors, repository, service, module}.ts
├─ api-builder     -> apps/api/src/modules/<module>/{controller, dto/*}.ts
└─ test-writer     -> apps/api/src/modules/<module>/__tests__/*.spec.ts
```

Each teammate receives:
1. The Module Blueprint (full text)
2. Their spawn prompt from `.claude/teams/generation/prompts/<role>.md`
3. Instruction to read the golden module reference files

### Phase 3: Assembly + Registration

After all 4 teammates return:
1. Write files from each teammate's output
2. Update barrel exports
3. Register the module in the app module
4. Run lint, type-check, and tests
5. Fix any naming mismatches between teammates
