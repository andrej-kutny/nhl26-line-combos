# NHL 26 Frontend (Angular)

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 21.0.4.

## Prerequisites

- Node.js 22+ recommended (Angular CLI may warn on unsupported Node versions).

## Development server

Install deps:

```bash
npm install
```

Start a local development server:

```bash
npm start
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Backend API

The UI expects the FastAPI backend to run at `http://127.0.0.1:8000` by default (editable in the UI header).

Start backend from repo root:

```bash
venv/bin/python -m uvicorn src.api.main:app --reload --port 8000
```

Recommended demo flow:
- Default mode is **Demo** (reads `/demo/goal1-stageb` output)
- Switch to **Live** to call `/optimize/forward-line` and `/optimize/defense-pair`

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
npm run build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Vitest](https://vitest.dev/) test runner, use the following command:

```bash
ng test
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
