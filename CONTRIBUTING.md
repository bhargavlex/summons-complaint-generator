# Contributing to Lexvia Summons Generator

Welcome to the team! To ensure we move fast without breaking things, we follow a strict **Feature Branch Workflow**. Please read this guide before pushing any code.

## 🌳 Branching Strategy

We use two main long-lived branches:

* **`main`**: 🔴 **DO NOT TOUCH.** This is the stable, production-ready code.
* **`develop`**: 🟡 **Integration Branch.** All new features are merged here first.

**Feature Branches:**
All work must happen in short-lived feature branches created from `develop`.
Naming convention: `feature/<task-name>` (e.g., `feature/login-auth`, `feature/doc-upload`).

---

## 🚀 The Daily Workflow

Follow this loop for every single task or ticket you work on.

### 1. Start Fresh (Sync with Team)

Before starting new work, always make sure your local `develop` is up to date.

```bash
git checkout develop
git pull origin develop
```

### 2. Create Your Branch

Create a new branch for your specific task.

```bash
# Syntax: git checkout -b feature/<your-feature-name> develop
git checkout -b feature/db-schema develop
```

### 3. Code & Commit

Work on your feature. Commit often with clear messages.

```bash
git add .
git commit -m "Added initial User model"
```

### 4. 🛡️ The "Anti-Conflict" Move (CRITICAL)

**Do this daily** or before you push. This pulls your team's latest work into your branch so you can fix conflicts *locally* before they break the server.

```bash
# 1. Fetch latest changes from the server
git fetch origin

# 2. Merge develop into your current feature branch
git merge origin/develop
```

* **If Git says `Already up to date`**: You are good to go!
* **If Git reports a `CONFLICT`**:
  1. Open the files with conflicts.
  2. Look for the `<<<<<<<` markers and decide which code to keep.
  3. Save the files.
  4. Run `git add .` and `git commit` to finish the fix.

### 5. Push Your Feature

When you are ready for a review:

```bash
# The first time you push this branch
git push -u origin feature/db-schema
```

---

## 🔀 Pull Requests (Merging to Develop)

**Never merge your own code locally.** We use Pull Requests (PRs) to ensure quality.

1. Go to the repository on GitHub/GitLab.
2. Click **"Compare & Pull Request"**.
   * **Base:** `develop` ⬅️ **Compare:** `feature/your-branch`
3. Add a Title and Description of what you changed.
4. **Request a Review:** Tag at least one other team member.
5. **Merge:** Once approved, click "Squash and Merge" or "Merge Commit".
6. **Cleanup:** Delete your remote feature branch after merging.

---

## 📦 Releasing (Merging to Main)

Merging to `main` happens only when `develop` is stable and ready for a release.

1. Create a PR with **Base:** `main` ⬅️ **Compare:** `develop`.
2. Ensure all CI/CD checks pass.
3. Merge and Tag the release.
