# Branching, Merging & History

Detailed reference for [../SKILL.md](../SKILL.md). All commands verified against
SVN 1.14.3.

## Branching and tagging

Standard layout: `trunk/` | `branches/` | `tags/`. Branches and tags are
server-side copies (instant, no data transfer). All URL→URL copies verified.

```bash
# Create branch
svn copy https://svn.example.com/repo/trunk \
         https://svn.example.com/repo/branches/feature-name \
         -m "Branch: feature-name" --encoding UTF-8

# Switch working copy to branch / check current branch
svn switch https://svn.example.com/repo/branches/feature-name
svn info --show-item url

# Create tag (same mechanism; by convention don't commit to tags/)
svn copy https://svn.example.com/repo/trunk \
         https://svn.example.com/repo/tags/v2.1.0 \
         -m "Tag: v2.1.0" --encoding UTF-8

# Create a directory directly in the repo (immediate server commit)
svn mkdir -m "layout" https://svn.example.com/repo/trunk/newsub
```

## Merging

```bash
# Merge branch → trunk (record-based, SVN 1.5+). svn up first to flatten the WC.
svn switch https://svn.example.com/repo/trunk
svn up
svn merge https://svn.example.com/repo/branches/feature-name
svn status                              # review
svn diff --internal-diff > /tmp/merge_review.patch && cat /tmp/merge_review.patch
svn commit -m "Merge: feature-name into trunk" --encoding UTF-8

# Merge history
svn mergeinfo https://svn.example.com/repo/branches/feature-name
svn mergeinfo --show-revs eligible https://svn.example.com/repo/branches/feature-name
```

### Reverse-merge = the `git revert <commit>` equivalent

To undo an already-committed revision, reverse-merge it, then commit. **`svn up`
first is mandatory** — merging into a mixed-revision working copy fails (verified:
`E195020: Cannot merge into mixed-revision working copy [N:M]; try updating
first`).

```bash
svn up
svn merge -c -<rev> .                   # reverse-merge revision <rev>
svn status                              # review
svn commit -m "Revert r<rev>" --encoding UTF-8
```

> A reverse merge also records `svn:mergeinfo` on the target (verified). If you
> later see unexplained `svn:mergeinfo` property churn, this — or a subdirectory
> merge — is a likely source; see [../SKILL.md](../SKILL.md#svn-vs-git-semantics).

## Viewing history

```bash
svn log -l 20                          # last 20
svn log -r 1230:1240                   # revision range
svn log -v -r 1234                     # verbose: changed files
svn log <file>                         # file history
svn diff --internal-diff -r 1233:1234 > /tmp/rev_diff.patch
svn blame <file>                       # alias: praise / annotate / ann
svn cat -r 1234 src/file.cpp > /tmp/old_version.cpp

# Machine-readable (best for agents — UTF-8, no codepage ambiguity):
svn log -l 10 --xml > /tmp/svn_log.xml
svn log --xml -r 12345 <url>           # single revision, e.g. for a release note
```

## Externals management

```bash
svn propget svn:externals .
svn propget -R svn:externals .         # recursive

# Update behaviour
svn update --non-interactive           # updates externals by default
svn update --ignore-externals          # skip externals (faster)

# Add / edit a definition
svn propedit svn:externals .
# Modern format (target last):   [-r REV] URL  LOCAL_DIR
#   -r25 https://svn.example.com/ext/zlib/trunk  ThirdParty/zlib
# Pin to -r so externals don't float to HEAD unexpectedly.

svn commit -m "Externals: add zlib" --encoding UTF-8
```

> ⚠️ Scripting note (verified): `svn propget svn:externals .` **exits non-zero
> (1) with `W200017: Property not found`** when the directory has no externals —
> it does not return an empty success. Treat exit 1 + that warning as "no
> externals", not as an error.

Externals change the effective boundary of a working copy: `svn update` pulls
them in, so commit/release/scan logic must decide explicitly whether externals
are in scope.
