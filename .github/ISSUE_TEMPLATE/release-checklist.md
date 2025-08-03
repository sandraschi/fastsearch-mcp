---
name: Release Checklist
about: Checklist for preparing a new release
title: 'Release vX.Y.Z'
labels: 'release'
assignees: ''
---

## Pre-Release Checklist

### Code Quality
- [ ] All tests are passing (`pytest`)
- [ ] Code is properly formatted (`black .`)
- [ ] Type checking passes (`mypy .`)
- [ ] Linting passes (`flake8`)
- [ ] Documentation is up to date

### Version Management
- [ ] Update version in `__init__.py`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Ensure all changes are committed and pushed

### Local Testing
- [ ] Test installation from source
- [ ] Test DXT package generation
- [ ] Test service installation and startup
- [ ] Test basic search functionality

## Release Process

1. Create a signed tag:
   ```bash
   git tag -s vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

2. Monitor the [GitHub Actions workflow](https://github.com/yourusername/fastsearch-mcp/actions)

3. After successful build:
   - [ ] Verify all artifacts are attached to the GitHub release
   - [ ] Verify PyPI package was uploaded (if applicable)
   - [ ] Verify DXT package was generated correctly

## Post-Release

- [ ] Create a new version branch: `git checkout -b release/vX.Y`
- [ ] Bump version to next development version in `__init__.py`
- [ ] Update `CHANGELOG.md` with new `[Unreleased]` section
- [ ] Push changes: `git push origin release/vX.Y`
- [ ] Update documentation links if needed
- [ ] Announce the release in relevant channels
