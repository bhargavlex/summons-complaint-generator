

# Contributing to Lexvia Summons Generator

Welcome to the team!
To move fast **without breaking production**, we follow a strict and predictable **Feature Branch Workflow**. This guide documents the *only supported way* to contribute code.

Please read this fully before pushing anything.

---

## 🌳 Branching Strategy

We maintain two long-lived branches:

### 🔴 `main`

* Production-ready code
* **Never commit directly**
* Only updated via Pull Request from `develop`

### 🟡 `develop`

* Integration branch
* All features are merged here first

---

### 🌱 Feature Branches

All work must happen in short-lived feature branches created from `develop`.

**Naming convention**

```
feature/<short-description>
```

Examples:

```
feature/llm-extraction
feature/doc-upload
feature/auth-middleware
```

---

## 🚀 Standard Daily Workflow

### 1️⃣ Sync with the Team

Always start with the latest `develop`.

```bash
git checkout develop
git pull origin develop
```

---

### 2️⃣ Create a Feature Branch

```bash
git checkout -b feature/your-feature-name develop
```

---

### 3️⃣ Code & Commit Incrementally

Commit small, logical changes with clear intent.

```bash
git add .
git commit -m "Add extraction router"
```

✔ Good commits are easy to review
❌ Large “everything at once” commits are not

---

## 🛡️ Staying in Sync with `develop` (CRITICAL)

You **must** regularly merge `develop` into your feature branch to avoid large conflicts later.

```bash
git fetch origin
git merge origin/develop
```

### Outcomes:

* **Already up to date** → ✅ continue working
* **Conflicts** → resolve them **immediately**

#### Resolving conflicts:

1. Open conflicted files
2. Decide what to keep
3. Remove `<<<<<<<` markers
4. Save
5. Finish the merge

```bash
git add .
git commit
```

📌 This commit should contain **only conflict resolution**, no feature logic.

---

## 🧳 Working with `git stash` (Real-World Scenario)

Sometimes you have **uncommitted work** and need to merge `develop`.

### ✅ Correct Stash Workflow

```bash
git stash
git fetch origin
git merge origin/develop
```

---

### 🔧 Resolve Merge Conflicts (If Any)

```bash
git add .
git commit    # conflict-resolution commit
```

---

### 🔁 Re-apply Your Work

```bash
git stash pop
```

⚠️ **Important:**
Conflicts may happen *again*.
This is **normal and expected**.

**Why?**

* The stash was created before `develop` was merged
* Git is replaying old changes onto new code

---

### ✅ Handling Stash Conflicts

1. Resolve conflicts manually
2. Decide whether to keep:

   * your feature changes
   * new `develop` changes
   * or both (most common)
3. Stage and commit

```bash
git add .
git commit -m "Integrate feature changes after develop update"
```

📌 **Rule of thumb**

* Conflict-only fixes → neutral commit message
* Feature logic → feature-focused commit message

---

## 📤 Pushing Your Feature

```bash
git push -u origin feature/your-feature-name
```

---

## 🔀 Pull Requests (Feature → Develop)

**Never merge into `develop` locally.**

1. Open a Pull Request:

   * **Base:** `develop`
   * **Compare:** `feature/your-feature-name`
2. Add a clear title and description
3. Request at least one review
4. Merge using:

   * **Squash and Merge** (preferred)
   * or **Merge Commit**

---

## 🚢 Releases (Develop → Main)

Only when `develop` is stable:

1. Create PR:

   * **Base:** `main`
   * **Compare:** `develop`
2. Ensure CI passes
3. Merge and tag the release

---

## 🚫 Common Mistakes (READ THIS)

### ❌ Running `git merge origin/develop` twice

* A merge pauses on conflicts
* Resolve → `git add` → `git commit`
* **Do not run merge again**

---

### ❌ Ignoring stash conflicts

* Conflicts after `stash pop` are normal
* Ignoring them = lost feature work
* Always resolve + commit

---

### ❌ Mixing conflict resolution and feature logic in one commit

* Makes reviews impossible
* Makes rollbacks dangerous

✔ Fix conflicts first
✔ Commit feature work separately

---

### ❌ Committing directly to `develop` or `main`

* This bypasses review
* Breaks CI history
* Makes hotfixes painful

---

### ❌ Vague commit messages

Avoid:

```
"fix"
"changes"
"update"
"conflicts"
```

Use:

```
"Add extraction endpoint"
"Wire LLM service into pipeline"
"Integrate feature with updated API structure"
```

